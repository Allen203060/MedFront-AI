"""
MedFront Vector Stores.
Implements Local In-Memory Vector Store (with JSON persistence) and Azure AI Search.
"""

import json
import logging
import math
import os
from abc import ABC, abstractmethod
from typing import Any

from src.core.config import settings
from src.rag.models import DocumentChunk, DocumentMetadata, SearchResult

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from azure.search.documents import SearchClient
    from azure.search.documents.models import VectorizedQuery
except ImportError:
    AzureKeyCredential = None  # type: ignore[assignment]
    DefaultAzureCredential = None  # type: ignore[assignment]
    SearchClient = None  # type: ignore[assignment]
    VectorizedQuery = None  # type: ignore[assignment]

logger = logging.getLogger("medfront.rag.store")


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class BaseKnowledgeStore(ABC):
    """Abstract interface for knowledge indexes."""

    @abstractmethod
    def index_documents(self, chunks: list[DocumentChunk]) -> int:
        """Upsert a list of document chunks into the store."""

    @abstractmethod
    def search(
        self,
        query: str,
        query_vector: list[float],
        top_k: int = 3,
        patient_id: str | None = None,
        category: str | None = None,
        access_level: str | None = None,
    ) -> list[SearchResult]:
        """Query the store with hybrid / vector search and metadata filters."""

    @abstractmethod
    def count(self) -> int:
        """Return total indexed chunks."""


class LocalVectorStore(BaseKnowledgeStore):
    """
    In-memory vector store with persistence to local JSON files.
    Enforces HIPAA-compliant patient_id partition filtering and cosine similarity ranking.
    """

    def __init__(self, index_name: str, cache_dir: str = "data/cache"):
        self.index_name = index_name
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, f"{index_name}.json")
        self.chunks: dict[str, DocumentChunk] = {}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        metadata = DocumentMetadata(**item["metadata"])
                        chunk = DocumentChunk(
                            id=item["id"],
                            text=item["text"],
                            metadata=metadata,
                            embedding=item.get("embedding"),
                        )
                        self.chunks[chunk.id] = chunk
                logger.info(f"Loaded {len(self.chunks)} chunks from local cache: {self.cache_file}")
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Could not load cache {self.cache_file}: {e}")

    def _save_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                data = [chunk.to_dict() for chunk in self.chunks.values()]
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.chunks)} chunks to local cache: {self.cache_file}")
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to save cache to {self.cache_file}: {e}")

    def index_documents(self, chunks: list[DocumentChunk]) -> int:
        added = 0
        for chunk in chunks:
            self.chunks[chunk.id] = chunk
            added += 1
        self._save_cache()
        return added

    def search(
        self,
        query: str,
        query_vector: list[float],
        top_k: int = 3,
        patient_id: str | None = None,
        category: str | None = None,
        access_level: str | None = None,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        lower_query = query.lower()

        for chunk in self.chunks.values():
            meta = chunk.metadata

            # 1. Strict Patient Partition Filter (HIPAA Isolation)
            if patient_id:
                # If searching for a specific patient, reject any chunk that doesn't match
                if meta.patient_id != patient_id:
                    continue
            else:
                # If searching public clinic knowledge, reject patient health records
                if meta.patient_id is not None:
                    continue

            # 2. Category Filter
            if category and meta.category != category:
                continue

            # 3. Access Level Filter (e.g. receptionist cannot access clinical notes)
            if access_level == "administrative" and meta.access_level == "clinical":
                continue

            # 4. Calculate Similarity Score
            sim_score = 0.0
            if query_vector and chunk.embedding:
                sim_score = cosine_similarity(query_vector, chunk.embedding)

            # Keyword lexical boost (hybrid enhancement)
            text_lower = chunk.text.lower()
            stop_words = {
                "a", "about", "an", "are", "as", "at", "be", "by", "for", "from",
                "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
                "this", "to", "was", "what", "when", "where", "who", "will", "with",
                "do", "does", "can", "could", "should", "would", "you", "your"
            }
            import re
            query_words = [w for w in re.findall(r'\b[a-z0-9]+\b', lower_query) if w not in stop_words]
            if query_words:
                match_count = sum(1 for w in query_words if re.search(r'\b' + re.escape(w) + r'\b', text_lower))
                lexical_boost = (match_count / len(query_words)) * 0.4
            else:
                lexical_boost = 0.0

            # Phrase match bonus
            if len(query_words) >= 2 and " ".join(query_words) in text_lower:
                lexical_boost += 0.25

            final_score = sim_score + lexical_boost

            results.append(SearchResult(
                chunk_id=chunk.id,
                text=chunk.text,
                score=round(final_score, 4),
                metadata=meta,
            ))

        # Sort descending by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def count(self) -> int:
        return len(self.chunks)

    def clear(self):
        self.chunks.clear()
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)


class AzureSearchStore(BaseKnowledgeStore):
    """
    Enterprise-grade Azure AI Search store.
    Utilizes hybrid retrieval with vector search + keyword search and OData filter expressions.
    """

    def __init__(self, index_name: str):
        self.index_name = index_name
        self.client = None
        self._init_client()

    def _init_client(self):
        if SearchClient is None or DefaultAzureCredential is None or AzureKeyCredential is None:
            logger.warning("Azure Search dependencies are not installed.")
            return

        try:
            endpoint = settings.azure_search_endpoint
            if not endpoint:
                raise ValueError("AZURE_SEARCH_ENDPOINT is not set.")

            if settings.use_managed_identity:
                credential = DefaultAzureCredential()
            else:
                if not settings.azure_search_api_key:
                    raise ValueError("AZURE_SEARCH_API_KEY is not set.")
                credential = AzureKeyCredential(settings.azure_search_api_key)

            self.client = SearchClient(
                endpoint=endpoint,
                index_name=self.index_name,
                credential=credential,
            )
            logger.info(f"Initialized Azure AI Search client for index '{self.index_name}'.")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Could not connect to Azure AI Search ({e}).")

    def index_documents(self, chunks: list[DocumentChunk]) -> int:
        if not self.client:
            raise RuntimeError("Azure AI Search client is not initialized.")

        docs: list[dict[str, Any]] = []
        for c in chunks:
            doc: dict[str, Any] = {
                "id": c.id,
                "text": c.text,
                "category": c.metadata.category,
                "source": c.metadata.source,
                "patient_id": c.metadata.patient_id or "",
                "patient_name": c.metadata.patient_name or "",
                "record_type": c.metadata.record_type or "",
                "author": c.metadata.author or "",
                "access_level": c.metadata.access_level,
                "timestamp": c.metadata.timestamp or "",
            }
            if c.embedding:
                doc["embedding"] = c.embedding
            docs.append(doc)

        result = self.client.upload_documents(documents=docs)
        succeeded = sum(1 for r in result if r.succeeded)
        return succeeded

    def search(
        self,
        query: str,
        query_vector: list[float],
        top_k: int = 3,
        patient_id: str | None = None,
        category: str | None = None,
        access_level: str | None = None,
    ) -> list[SearchResult]:
        if not self.client:
            raise RuntimeError("Azure AI Search client is not initialized.")

        # Build OData filter expressions
        filters = []
        if patient_id:
            filters.append(f"patient_id eq '{patient_id}'")
        else:
            filters.append("patient_id eq ''")

        if category:
            filters.append(f"category eq '{category}'")

        if access_level == "administrative":
            filters.append("access_level eq 'administrative'")

        filter_expr = " and ".join(filters) if filters else None

        vector_queries = []
        if query_vector and VectorizedQuery is not None:
            vector_queries.append(
                VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="embedding")
            )

        raw_results = self.client.search(
            search_text=query,
            vector_queries=vector_queries,
            filter=filter_expr,
            top=top_k,
        )

        results = []
        for r in raw_results:
            metadata = DocumentMetadata(
                source=r.get("source", ""),
                category=r.get("category", ""),
                patient_id=r.get("patient_id") or None,
                patient_name=r.get("patient_name") or None,
                record_type=r.get("record_type") or None,
                author=r.get("author") or "",
                access_level=r.get("access_level", "administrative"),
                timestamp=r.get("timestamp") or None,
            )
            results.append(SearchResult(
                chunk_id=r["id"],
                text=r["text"],
                score=r.get("@search.score", 0.0),
                metadata=metadata,
            ))
        return results

    def count(self) -> int:
        if not self.client:
            return 0
        return self.client.get_document_count()
