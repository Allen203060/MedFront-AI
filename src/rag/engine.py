"""
MedFront Unified RAG Engine.
Orchestrates dual-mode retrieval across Public Clinic Knowledge and Scoped Patient Records.
"""

import argparse
import logging

from src.core.config import settings
from src.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider
from src.rag.models import RAGAnswer, SearchResult
from src.rag.store import AzureSearchStore, BaseKnowledgeStore, LocalVectorStore

logger = logging.getLogger("medfront.rag.engine")


class RAGEngine:
    """
    Central RAG engine used across all MedFront AI modules.
    Abstracts whether the underlying retrieval is executed via Local Vectors or Azure AI Search.
    """

    def __init__(
        self,
        clinic_store: BaseKnowledgeStore | None = None,
        patient_store: BaseKnowledgeStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
    ):
        self.mode = settings.effective_rag_mode
        self.embedding_provider = embedding_provider or get_embedding_provider()

        if clinic_store and patient_store:
            self.clinic_store = clinic_store
            self.patient_store = patient_store
        else:
            if self.mode == "azure":
                try:
                    logger.info("Initializing RAGEngine with Azure AI Search...")
                    self.clinic_store = AzureSearchStore(settings.azure_search_clinic_index)
                    self.patient_store = AzureSearchStore(settings.azure_search_patient_index)
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to initialize Azure stores ({e}). Using LocalVectorStore.")
                    self.clinic_store = LocalVectorStore("clinic-knowledge-index")
                    self.patient_store = LocalVectorStore("patient-records-index")
            else:
                logger.info("Initializing RAGEngine with LocalVectorStore (development/offline mode)...")
                self.clinic_store = LocalVectorStore("clinic-knowledge-index")
                self.patient_store = LocalVectorStore("patient-records-index")

    def search_clinic(
        self,
        query: str,
        top_k: int = 3,
        category: str | None = None,
    ) -> list[SearchResult]:
        """
        Query public clinic knowledge (hours, insurance, prep guidelines, policies).
        Guaranteed to exclude any patient-specific health records.
        """
        query_vector = self.embedding_provider.embed_text(query)
        return self.clinic_store.search(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            patient_id=None,
            category=category,
            access_level="administrative",
        )

    def search_patient(
        self,
        patient_id: str,
        query: str,
        top_k: int = 3,
        access_level: str | None = None,
    ) -> list[SearchResult]:
        """
        Query patient-specific encounters, SOAP notes, and call transcripts.
        Enforces strict patient_id partition isolation.
        """
        if not patient_id or not patient_id.strip():
            raise ValueError("patient_id is required for patient record searches.")

        query_vector = self.embedding_provider.embed_text(query)
        return self.patient_store.search(
            query=query,
            query_vector=query_vector,
            top_k=top_k,
            patient_id=patient_id.strip(),
            access_level=access_level,
        )

    def format_context_for_prompt(self, results: list[SearchResult]) -> str:
        """Format retrieved snippets into a clear string to inject into LLM system prompt."""
        if not results:
            return "No relevant clinic documentation or patient records found."

        context_lines = []
        for i, res in enumerate(results, start=1):
            context_lines.append(
                f"[Document {i} | Source: {res.citation} | Score: {res.score}]\n{res.text}\n"
            )
        return "\n".join(context_lines)

    def query(
        self,
        query: str,
        patient_id: str | None = None,
        top_k: int = 3,
        access_level: str | None = None,
    ) -> RAGAnswer:
        """
        Unified search returning citations and synthesized answer payload.
        """
        if patient_id:
            results = self.search_patient(patient_id, query, top_k=top_k, access_level=access_level)
        else:
            results = self.search_clinic(query, top_k=top_k)

        citations = [r.citation for r in results]
        context = self.format_context_for_prompt(results)

        return RAGAnswer(
            query=query,
            answer=context,
            citations=citations,
            results=results,
        )


def main():
    """Interactive command-line tool for verifying the RAG pipeline."""
    parser = argparse.ArgumentParser(description="MedFront RAG Interactive Query CLI")
    parser.add_argument("query", nargs="?", default="What are the clinic opening hours on Saturday?", help="Search query")
    parser.add_argument("--patient-id", "-p", default=None, help="Patient ID (e.g. P-10023) for scoped searches")
    parser.add_argument("--top-k", "-k", type=int, default=3, help="Number of results")
    parser.add_argument("--access-level", "-a", default=None, help="Access level: administrative or clinical")

    args = parser.parse_args()

    engine = RAGEngine()
    print(f"\n{'='*60}")
    print(f"MedFront RAG Engine (Mode: {engine.mode.upper()})")
    print(f"Query: '{args.query}'")
    if args.patient_id:
        print(f"Scoped Patient ID: {args.patient_id}")
    print(f"{'='*60}\n")

    if args.patient_id:
        results = engine.search_patient(
            patient_id=args.patient_id,
            query=args.query,
            top_k=args.top_k,
            access_level=args.access_level,
        )
    else:
        results = engine.search_clinic(
            query=args.query,
            top_k=args.top_k,
        )

    if not results:
        print("No matching records found.")
    else:
        for idx, res in enumerate(results, start=1):
            print(f"--- [Match #{idx}] Score: {res.score:.4f} ---")
            print(f"Citation: {res.citation}")
            print(f"Text:\n{res.text}\n")


if __name__ == "__main__":
    main()
