"""
Live implementations of RAG and Tool interfaces for production Brain orchestration.
Connects the Agentic Brain to Module 4 (RAG Engine) and Module 5 (Cosmos DB Actions).
"""

from typing import Optional
from src.brain.interfaces import RAGProviderInterface, ToolRegistryInterface
from src.brain.models import RAGRequest, RAGResponse, ToolCallRequest, ToolCallResult
from src.rag.engine import RAGEngine
from src.actions.tools import execute_tool


class LiveRAGProvider(RAGProviderInterface):
    """Bridges Brain RAG requests to the unified RAGEngine (Azure Search or Local)."""

    def __init__(self, engine: Optional[RAGEngine] = None):
        self.engine = engine or RAGEngine()

    def query(self, request: RAGRequest) -> RAGResponse:
        try:
            if request.index_target == "patient_records":
                if not request.patient_id:
                    return RAGResponse(
                        success=False,
                        error_message="Access Denied: Unverified patient_id required for clinical records."
                    )
                results = self.engine.search_patient(
                    patient_id=request.patient_id,
                    query=request.query_text,
                    top_k=request.top_k,
                )
            else:
                results = self.engine.search_clinic(
                    query=request.query_text,
                    top_k=request.top_k,
                )

            if not results:
                return RAGResponse(
                    success=True,
                    retrieved_chunks=[],
                    sources=[],
                )

            chunks = [r.text for r in results]
            sources = [f"{r.source}#{r.id}" for r in results]
            return RAGResponse(
                success=True,
                retrieved_chunks=chunks,
                sources=sources,
            )
        except Exception as e:
            return RAGResponse(
                success=False,
                error_message=f"RAG search error: {str(e)}"
            )


class LiveToolRegistry(ToolRegistryInterface):
    """Bridges Brain tool requests to the Action Layer (Cosmos DB / Mock)."""

    def execute_tool(self, request: ToolCallRequest) -> ToolCallResult:
        tool_name = request.tool_name.value if hasattr(request.tool_name, "value") else str(request.tool_name)
        res_dict = execute_tool(tool_name, request.parameters)

        success = res_dict.get("success", False)
        message = res_dict.get("message", "")
        data = res_dict.get("data") or {}
        error = res_dict.get("error_code")

        return ToolCallResult(
            success=success,
            output_data=data,
            user_message=message,
            error_message=None if success else f"{error}: {message}",
        )
