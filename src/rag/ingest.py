"""
MedFront Knowledge Ingestion Pipeline.
Loads documents from data/knowledge/, generates chunks and embeddings,
and stores them in either the Local Vector Store or Azure AI Search.
"""

import argparse
import json
import logging
import os
from typing import Any

from src.core.config import settings
from src.rag.chunker import DocumentChunker
from src.rag.embeddings import (
    AzureOpenAIEmbeddings,
    LocalDeterministicEmbeddings,
)
from src.rag.models import DocumentChunk
from src.rag.store import AzureSearchStore, LocalVectorStore

try:
    from azure.core.credentials import AzureKeyCredential
    from azure.identity import DefaultAzureCredential
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        HnswAlgorithmConfiguration,
        SearchableField,
        SearchField,
        SearchFieldDataType,
        SearchIndex,
        SimpleField,
        VectorSearch,
        VectorSearchProfile,
    )
except ImportError:
    AzureKeyCredential = None  # type: ignore[assignment]
    DefaultAzureCredential = None  # type: ignore[assignment]
    SearchIndexClient = None  # type: ignore[assignment]
    SearchIndex = None  # type: ignore[assignment]
    SimpleField = None  # type: ignore[assignment]
    SearchableField = None  # type: ignore[assignment]
    SearchField = None  # type: ignore[assignment]
    SearchFieldDataType = None  # type: ignore[assignment]
    VectorSearch = None  # type: ignore[assignment]
    VectorSearchProfile = None  # type: ignore[assignment]
    HnswAlgorithmConfiguration = None  # type: ignore[assignment]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("medfront.rag.ingest")


def load_and_chunk_knowledge(data_dir: str = "data/knowledge") -> tuple[list[DocumentChunk], list[DocumentChunk]]:
    """Reads all knowledge documents and splits into clinic chunks and patient chunks."""
    chunker = DocumentChunker()
    clinic_chunks: list[DocumentChunk] = []
    patient_chunks: list[DocumentChunk] = []

    # 1. Ingest clinic info
    clinic_info_path = os.path.join(data_dir, "clinic_info.md")
    if os.path.exists(clinic_info_path):
        with open(clinic_info_path, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = chunker.chunk_markdown(content, source="clinic_info.md", category="clinic_policy")
        clinic_chunks.extend(chunks)
        logger.info(f"Loaded {len(chunks)} chunks from clinic_info.md")

    # 2. Ingest insurance & billing
    insurance_path = os.path.join(data_dir, "insurance_billing.md")
    if os.path.exists(insurance_path):
        with open(insurance_path, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = chunker.chunk_markdown(content, source="insurance_billing.md", category="insurance")
        clinic_chunks.extend(chunks)
        logger.info(f"Loaded {len(chunks)} chunks from insurance_billing.md")

    # 3. Ingest procedure prep
    prep_path = os.path.join(data_dir, "procedure_prep.md")
    if os.path.exists(prep_path):
        with open(prep_path, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = chunker.chunk_markdown(content, source="procedure_prep.md", category="procedure_prep")
        clinic_chunks.extend(chunks)
        logger.info(f"Loaded {len(chunks)} chunks from procedure_prep.md")

    # 4. Ingest patient records
    patient_records_path = os.path.join(data_dir, "sample_patient_records.json")
    if os.path.exists(patient_records_path):
        with open(patient_records_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        chunks = chunker.chunk_patient_records(records, source="sample_patient_records.json")
        patient_chunks.extend(chunks)
        logger.info(f"Loaded {len(chunks)} chunks from sample_patient_records.json")

    return clinic_chunks, patient_chunks


def create_azure_indexes_if_needed():
    """Create Azure AI Search indexes with vector search configurations if not existing."""
    if (
        SearchIndexClient is None
        or DefaultAzureCredential is None
        or AzureKeyCredential is None
        or SearchIndex is None
        or SimpleField is None
        or SearchableField is None
        or SearchField is None
        or SearchFieldDataType is None
        or VectorSearch is None
        or VectorSearchProfile is None
        or HnswAlgorithmConfiguration is None
    ):
        raise RuntimeError(
            "The 'azure-search-documents' and 'azure-identity' packages are required for Azure indexing. "
            "Please run `pip install -r requirements.txt`."
        )

    endpoint = settings.azure_search_endpoint
    if not endpoint:
        raise ValueError("AZURE_SEARCH_ENDPOINT is not configured.")

    if settings.use_managed_identity:
        credential = DefaultAzureCredential()
    else:
        api_key = settings.azure_search_api_key
        if not api_key:
            raise ValueError("AZURE_SEARCH_API_KEY is not configured.")
        credential = AzureKeyCredential(api_key)

    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

    vector_search = VectorSearch(
        profiles=[VectorSearchProfile(name="my-vector-profile", algorithm_configuration_name="my-hnsw")],
        algorithms=[HnswAlgorithmConfiguration(name="my-hnsw")]
    )

    fields: list[Any] = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SearchableField(name="category", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="source", type=SearchFieldDataType.String),
        SimpleField(name="patient_id", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="patient_name", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="record_type", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="author", type=SearchFieldDataType.String),
        SimpleField(name="access_level", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="timestamp", type=SearchFieldDataType.String, filterable=True, sortable=True),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,  # text-embedding-3-large or ada-002
            vector_search_profile_name="my-vector-profile"
        )
    ]

    for index_name in [settings.azure_search_clinic_index, settings.azure_search_patient_index]:
        try:
            index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)
            index_client.create_or_update_index(index)
            logger.info(f"Verified/Created Azure AI Search index: {index_name}")
        except Exception as e:
            logger.error(f"Error creating index {index_name}: {e}")
            raise


def run_ingestion(target: str = "local", data_dir: str = "data/knowledge"):
    """Orchestrate chunking, embedding generation, and indexing into target stores."""
    logger.info(f"Starting Ingestion Pipeline. Target: {target.upper()}")

    clinic_chunks, patient_chunks = load_and_chunk_knowledge(data_dir)
    total_chunks = len(clinic_chunks) + len(patient_chunks)

    if total_chunks == 0:
        logger.warning("No documents found in knowledge directory!")
        return

    # Choose embedding provider
    if target == "azure":
        embedder = AzureOpenAIEmbeddings()
        create_azure_indexes_if_needed()
        clinic_store = AzureSearchStore(settings.azure_search_clinic_index)
        patient_store = AzureSearchStore(settings.azure_search_patient_index)
    else:
        embedder = LocalDeterministicEmbeddings()
        clinic_store = LocalVectorStore("clinic-knowledge-index")
        patient_store = LocalVectorStore("patient-records-index")
        clinic_store.clear()
        patient_store.clear()

    # Generate embeddings for clinic chunks
    logger.info(f"Generating embeddings for {len(clinic_chunks)} clinic chunks...")
    clinic_texts = [c.text for c in clinic_chunks]
    clinic_vectors = embedder.embed_batch(clinic_texts)
    for c, vec in zip(clinic_chunks, clinic_vectors):
        c.embedding = vec

    indexed_clinic = clinic_store.index_documents(clinic_chunks)
    logger.info(f"Successfully indexed {indexed_clinic} chunks into Clinic Index.")

    # Generate embeddings for patient chunks
    logger.info(f"Generating embeddings for {len(patient_chunks)} patient chunks...")
    patient_texts = [c.text for c in patient_chunks]
    patient_vectors = embedder.embed_batch(patient_texts)
    for c, vec in zip(patient_chunks, patient_vectors):
        c.embedding = vec

    indexed_patient = patient_store.index_documents(patient_chunks)
    logger.info(f"Successfully indexed {indexed_patient} chunks into Patient Index.")

    print(f"\n{'='*55}")
    print(f"INGESTION COMPLETE ({target.upper()} MODE)")
    print(f"  • Clinic Knowledge Chunks: {indexed_clinic}")
    print(f"  • Patient Record Chunks:   {indexed_patient}")
    print(f"  • Total Chunks Indexed:    {indexed_clinic + indexed_patient}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into Knowledge Base")
    parser.add_argument(
        "--target",
        choices=["local", "azure"],
        default="local",
        help="Target storage destination ('local' or 'azure')",
    )
    parser.add_argument(
        "--data-dir",
        default="data/knowledge",
        help="Path to source documentation directory",
    )
    args = parser.parse_args()
    run_ingestion(target=args.target, data_dir=args.data_dir)
