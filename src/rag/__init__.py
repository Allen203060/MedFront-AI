"""
MedFront Knowledge Base & RAG Module.
Provides dual-mode hybrid vector retrieval, document chunking, and Brain tool interfaces.
"""

from src.rag.chunker import DocumentChunker
from src.rag.embeddings import (
    AzureOpenAIEmbeddings,
    BaseEmbeddingProvider,
    LocalDeterministicEmbeddings,
    get_embedding_provider,
)
from src.rag.engine import RAGEngine
from src.rag.models import (
    DocumentChunk,
    DocumentMetadata,
    RAGAnswer,
    RAGQuery,
    SearchResult,
)
from src.rag.store import (
    AzureSearchStore,
    BaseKnowledgeStore,
    LocalVectorStore,
)
from src.rag.tools import (
    CLINIC_KNOWLEDGE_TOOL,
    PATIENT_RECORDS_TOOL,
    RAG_TOOLS,
    execute_rag_tool,
)

__all__ = [
    "CLINIC_KNOWLEDGE_TOOL",
    "PATIENT_RECORDS_TOOL",
    "RAG_TOOLS",
    "AzureOpenAIEmbeddings",
    "AzureSearchStore",
    "BaseEmbeddingProvider",
    "BaseKnowledgeStore",
    "DocumentChunk",
    "DocumentChunker",
    "DocumentMetadata",
    "LocalDeterministicEmbeddings",
    "LocalVectorStore",
    "RAGAnswer",
    "RAGEngine",
    "RAGQuery",
    "SearchResult",
    "execute_rag_tool",
    "get_embedding_provider",
]
