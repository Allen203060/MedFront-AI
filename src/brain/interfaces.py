"""
Abstract interface contracts for RAG and Tool execution layers.
"""

from abc import ABC, abstractmethod
from src.brain.models import RAGRequest, RAGResponse, ToolCallRequest, ToolCallResult


class RAGProviderInterface(ABC):
    """
    Abstract interface for querying the RAG search layer.
    """
    @abstractmethod
    def query(self, request: RAGRequest) -> RAGResponse:
        """Executes a search query against Azure AI Search or local knowledge base."""
        pass


class ToolRegistryInterface(ABC):
    """
    Abstract interface for executing backend tools and database operations.
    """
    @abstractmethod
    def execute_tool(self, request: ToolCallRequest) -> ToolCallResult:
        """Executes a requested tool with parameters and returns the execution result."""
        pass
