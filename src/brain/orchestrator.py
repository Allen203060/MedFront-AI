"""
Agentic Brain Orchestrator for MedFront-AI.
Coordinates Intent Classification, RAG Retrieval, Tool Action Execution, and Output Generation.
"""
from google.genai import types

import json
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai

from src.brain.interfaces import RAGProviderInterface, ToolRegistryInterface
from src.brain.memory import ConversationMemory
from src.brain.mocks import MockRAGProvider, MockToolRegistry
from src.brain.models import (
    BrainOutput,
    IntentDecision,
    PatientInfoPayload,
    RAGRequest,
    ToolCallRequest,
)
from src.brain.prompts import (
    PATIENT_INFO_EXTRACTION_PROMPT,
    RECEPTIONIST_SYSTEM_PROMPT,
)
from src.brain.router import IntentRouter
from src.brain.taxonomy import IntentCategory, ToolName

load_dotenv()


class AgenticBrainOrchestrator:
    """
    Central Orchestrator for the MedFront AI Receptionist Brain.
    """

    def __init__(
        self,
        rag_provider: Optional[RAGProviderInterface] = None,
        tool_registry: Optional[ToolRegistryInterface] = None,
    ) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")

        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY in environment variables.")

        self.client = genai.Client(api_key=self.api_key)

        # Core Components
        self.memory = ConversationMemory()
        self.router = IntentRouter()

        # Interfaces (Defaults to Mock implementations if not provided)
        self.rag_provider = rag_provider or MockRAGProvider()
        self.tool_registry = tool_registry or MockToolRegistry()

    def process_turn(self, user_text: str) -> BrainOutput:
        """
        Executes one full conversation turn: Memory -> Router -> Route Execution -> Response -> Harvest Metadata.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return BrainOutput(
                speech_text="I didn't catch that. Could you please repeat?",
                intent_detected=IntentCategory.UNKNOWN_OR_UNSUPPORTED
            )

        # 1. Add User Input to Memory
        self.memory.add_user_message(clean_text)

        # 2. Classify Intent & Extract Parameters via Router
        decision = self.router.classify_intent(self.memory, clean_text)
        self.memory.update_session(intent=decision.intent)

        speech_response = ""
        rag_used = False
        tool_used_name = None

        # 3. Route Execution Based on Intent Decision
        if decision.intent == IntentCategory.EMERGENCY_TRIAGE:
            speech_response = (
                "If you are experiencing severe symptoms such as chest pain or difficulty breathing, "
                "please hang up immediately and dial 911 or go to the nearest emergency room."
            )

        elif decision.intent in [IntentCategory.CLINIC_INFORMATION, IntentCategory.PATIENT_RECORD_LOOKUP]:
            speech_response, rag_used = self._handle_rag_branch(clean_text, decision)

        elif decision.intent in [
            IntentCategory.APPOINTMENT_BOOKING,
            IntentCategory.APPOINTMENT_CANCELLATION,
            IntentCategory.CHECK_AVAILABILITY,
        ] or decision.tool_name is not None:
            speech_response, tool_used_name = self._handle_tool_branch(clean_text, decision)

        else:
            # Fallback: Conversational Branch
            speech_response = self._handle_conversational_branch(clean_text)

        # 4. Save Assistant Output to Memory
        self.memory.add_assistant_message(speech_response)

        # 5. Harvest Patient Ingestion Metadata
        ingestion_payload = self._harvest_patient_metadata()

        return BrainOutput(
            speech_text=speech_response,
            intent_detected=decision.intent,
            rag_used=rag_used,
            tool_used=tool_used_name,
            patient_ingestion_payload=ingestion_payload
        )

    def _handle_conversational_branch(self, user_text: str) -> str:
        """Handles casual conversation and general pleasantries."""
        prompt = (
            f"{RECEPTIONIST_SYSTEM_PROMPT}\n\n"
            f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n"
            f"Aura:"
        )
        try:
            res = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return res.text.strip() if res.text else "How can I help you today at MedFront Clinic?"
        except Exception as e:
            return f"Thank you for calling MedFront. How can I assist you? (Note: {e})"

    def _handle_rag_branch(self, user_text: str, decision: IntentDecision) -> tuple[str, bool]:
        """Queries RAG provider and formulates natural language answer from retrieved context."""
        target_index = decision.target_index or "clinic_faq"
        query_str = decision.rag_query or user_text

        rag_req = RAGRequest(
            query_text=query_str,
            index_target=target_index,
            patient_id=self.memory.patient_id
        )

        rag_res = self.rag_provider.query(rag_req)

        if not rag_res.success or not rag_res.retrieved_chunks:
            return (
                "I apologize, but I am currently unable to retrieve that information from our records. "
                "Would you like me to transfer you to a staff member?",
                True
            )

        context_str = "\n".join(rag_res.retrieved_chunks)
        prompt = (
            f"{RECEPTIONIST_SYSTEM_PROMPT}\n\n"
            f"[Retrieved Information]:\n{context_str}\n\n"
            f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n"
            f"Answer the patient concisely using the retrieved information above:\nAura:"
        )

        try:
            res = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return (res.text.strip() if res.text else context_str, True)
        except Exception:
            return (rag_res.retrieved_chunks[0], True)

    def _handle_tool_branch(self, user_text: str, decision: IntentDecision) -> tuple[str, Optional[str]]:
        """Executes backend tool request and formulates user confirmation message."""
        tool_name = decision.tool_name or ToolName.CHECK_AVAILABILITY
        tool_req = ToolCallRequest(
            tool_name=tool_name,
            parameters=decision.tool_parameters
        )

        tool_res = self.tool_registry.execute_tool(tool_req)

        if not tool_res.success:
            return (
                f"I'm sorry, I couldn't complete that request: {tool_res.error_message}. "
                f"Would you like to try a different time?",
                tool_name.value
            )

        # Update Session Memory if patient identity verified
        if tool_name == ToolName.VERIFY_PATIENT_IDENTITY and tool_res.output_data.get("patient_id"):
            self.memory.update_session(patient_id=tool_res.output_data["patient_id"])

        prompt = (
            f"{RECEPTIONIST_SYSTEM_PROMPT}\n\n"
            f"[Backend Tool Execution Result]: {tool_res.user_message}\n\n"
            f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n"
            f"Convey this result politely to the patient in 1-2 spoken sentences:\nAura:"
        )

        try:
            res = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )
            return (res.text.strip() if res.text else tool_res.user_message, tool_name.value)
        except Exception:
            return (tool_res.user_message, tool_name.value)

    def _harvest_patient_metadata(self) -> Dict[str, Any]:
        """Harvests structured patient info from transcript for RAG ingestion."""
        try:
            transcript = self.memory.get_formatted_transcript(max_turns=10)
            prompt = f"{PATIENT_INFO_EXTRACTION_PROMPT}\n\n[Transcript]:\n{transcript}"

            res = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )

            raw_text = res.text.strip() if res.text else "{}"
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()

            parsed = json.loads(raw_text)
            
            # Update session memory with harvested details
            if parsed.get("full_name"):
                self.memory.update_session(verified_name=parsed["full_name"])
            if parsed.get("dob"):
                self.memory.update_session(dob=parsed["dob"])

            payload = PatientInfoPayload(
                full_name=parsed.get("full_name"),
                dob=parsed.get("dob"),
                reason_for_visit=parsed.get("reason_for_visit"),
                summary_notes=parsed.get("summary_notes")
            )
            return payload.to_dict()

        except Exception:
            return PatientInfoPayload().to_dict()

    def reset(self) -> None:
        """Resets orchestrator state and memory."""
        self.memory.clear()
