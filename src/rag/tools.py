"""
MedFront Brain Integration Tools.
Exposes Knowledge Base capabilities as OpenAI Function Calling schemas and dispatchers.
This file connects Module 4 (RAG) directly into Module 3 (The Brain).
"""

from typing import Any

from src.rag.engine import RAGEngine

# Singleton engine instance for tool executions
_engine = None

def get_engine() -> RAGEngine:
    global _engine
    if _engine is None:
        _engine = RAGEngine()
    return _engine


# 1. OpenAI Function Calling Tool Schemas
CLINIC_KNOWLEDGE_TOOL = {
    "type": "function",
    "function": {
        "name": "query_clinic_knowledge",
        "description": "Look up clinic operational hours, accepted insurance plans, fasting/lab prep guidelines, parking, and clinic policies.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The specific question or topic to search (e.g. 'accepted insurance for Aetna', 'fasting rules for lipid panel', 'Saturday clinic hours')"
                },
                "category": {
                    "type": "string",
                    "enum": ["clinic_policy", "insurance", "procedure_prep"],
                    "description": "Optional category filter"
                }
            },
            "required": ["question"]
        }
    }
}

PATIENT_RECORDS_TOOL = {
    "type": "function",
    "function": {
        "name": "query_patient_records",
        "description": "Query confidential clinical encounters, SOAP notes, lab results, and call transcripts for an identified patient. Strictly requires a verified patient_id.",
        "parameters": {
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "The verified patient ID (e.g. 'P-10023'). Never guess or leave blank."
                },
                "query": {
                    "type": "string",
                    "description": "The clinical or administrative topic to search (e.g. 'blood pressure medication history', 'last call transcript', 'allergies')"
                },
                "access_level": {
                    "type": "string",
                    "enum": ["administrative", "clinical"],
                    "description": "Filter by access level. Receptionist voice agent must use 'administrative'."
                }
            },
            "required": ["patient_id", "query"]
        }
    }
}

RAG_TOOLS: list[dict[str, Any]] = [
    CLINIC_KNOWLEDGE_TOOL,
    PATIENT_RECORDS_TOOL
]


# 2. Tool Execution Dispatcher
def execute_rag_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """
    Executes the specified tool called by GPT-4o and returns formatted context.
    """
    engine = get_engine()

    if tool_name == "query_clinic_knowledge":
        question = arguments.get("question", "")
        category = arguments.get("category")
        results = engine.search_clinic(query=question, category=category, top_k=3)
        return engine.format_context_for_prompt(results)

    elif tool_name == "query_patient_records":
        patient_id = arguments.get("patient_id")
        query = arguments.get("query", "")
        access_level = arguments.get("access_level")

        if not patient_id:
            return "Error: patient_id is required to query patient records. Please verify patient identity first."

        results = engine.search_patient(
            patient_id=patient_id,
            query=query,
            access_level=access_level,
            top_k=3
        )
        return engine.format_context_for_prompt(results)

    else:
        return f"Unknown tool: {tool_name}"
