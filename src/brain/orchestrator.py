"""
Agentic Brain Orchestrator for MedFront-AI.
Coordinates Intent Classification, RAG Retrieval, Tool Action Execution,
and Output Generation natively on Azure OpenAI (GPT-4o).
"""

import json
import logging
import re
from typing import Optional, Dict, Any

from src.core.config import settings
from src.brain.azure_client import get_azure_openai_client
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

logger = logging.getLogger("medfront.brain.orchestrator")


class AgenticBrainOrchestrator:
    """
    Central Orchestrator for the MedFront AI Receptionist Brain.
    """

    def __init__(
        self,
        rag_provider: Optional[RAGProviderInterface] = None,
        tool_registry: Optional[ToolRegistryInterface] = None,
    ) -> None:
        self.deployment_name = settings.azure_openai_deployment_name
        self.client = get_azure_openai_client()

        # Core Components
        self.memory = ConversationMemory()
        self.router = IntentRouter()

        # Interfaces (Defaults to Mock implementations if not provided)
        self.rag_provider = rag_provider or MockRAGProvider()
        self.tool_registry = tool_registry or MockToolRegistry()

    def process_turn(self, user_text: str) -> BrainOutput:
        """
        Executes one full conversation turn: Memory -> Router -> Route Execution -> Response.
        Metadata harvesting is decoupled to run without blocking spoken output.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return BrainOutput(
                speech_text="I didn't catch that. Could you please repeat?",
                intent_detected=IntentCategory.UNKNOWN_OR_UNSUPPORTED
            )

        # 1. Add User Input to Memory & Detect Language
        self.memory.add_user_message(clean_text)
        self.memory.detect_and_update_language(clean_text)

        # 2. Instant Fast-Path for Conversational Greetings (<50ms instant response)
        greeting_words = {"hello", "hi", "hey", "namaste", "नमस्ते", "sat sri akal", "sasrikaal", "good morning", "good afternoon", "good evening"}
        lower_clean = clean_text.lower().strip(".,!?;:'\"")
        if lower_clean in greeting_words and len(self.memory.messages) <= 3:
            if self.memory.language == "Hindi":
                fast_reply = "नमस्ते! मेडफ्रंट हेल्थ क्लिनिक में आपका स्वागत है। मैं ऑरा हूँ। आज मैं आपकी क्या सहायता कर सकती हूँ?"
            elif self.memory.language == "Punjabi":
                fast_reply = "ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ! ਮੈਡਫਰੰਟ ਹੈਲਥ ਕਲੀਨਿਕ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਮੈਂ ਔਰਾ ਹਾਂ। ਅੱਜ ਮੈਂ ਤੁਹਾਡੀ ਕੀ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ?"
            else:
                fast_reply = "Hello! Welcome to MedFront Health Clinic. My name is Aura. How may I assist you with your appointment today?"

            self.memory.add_assistant_message(fast_reply)
            return BrainOutput(
                speech_text=fast_reply,
                intent_detected=IntentCategory.CASUAL_CONVERSATION,
                rag_used=False,
                tool_used=None,
                patient_ingestion_payload=None,
            )

        # 3. Classify Intent & Extract Parameters via Router
        decision = self.router.classify_intent(self.memory, clean_text)
        self.memory.update_session(intent=decision.intent)

        speech_response = ""
        rag_used = False
        tool_used_name = None

        # 4. Route Execution Based on Intent Decision
        # Check if caller is providing their phone number to complete a pending appointment booking
        from src.actions.tools import extract_phone_number
        extracted_phone = extract_phone_number(clean_text)
        if extracted_phone:
            self.memory.update_session(phone_number=extracted_phone)

        if extracted_phone and self.memory.pending_doctor and self.memory.pending_time and not decision.tool_name:
            decision = IntentDecision(
                intent=IntentCategory.APPOINTMENT_BOOKING,
                tool_name=ToolName.BOOK_APPOINTMENT,
                tool_parameters={
                    "doctor": self.memory.pending_doctor,
                    "date": self.memory.pending_date or "tomorrow",
                    "time": self.memory.pending_time,
                    "full_name": self.memory.verified_name,
                    "phone_number": extracted_phone,
                }
            )

        if decision.intent == IntentCategory.EMERGENCY_TRIAGE:
            if self.memory.language == "Hindi":
                speech_response = (
                    "यदि आपको सीने में दर्द या सांस लेने में गंभीर कठिनाई हो रही है, "
                    "तो कृपया तुरंत फोन काटें और आपातकालीन सेवा 112 या 108 पर कॉल करें या नजदीकी अस्पताल जाएं।"
                )
            elif self.memory.language == "Punjabi":
                speech_response = (
                    "ਜੇਕਰ ਤੁਹਾਨੂੰ ਛਾਤੀ ਵਿੱਚ ਦਰਦ ਜਾਂ ਸਾਹ ਲੈਣ ਵਿੱਚ ਗੰਭੀਰ ਮੁਸ਼ਕਲ ਆ ਰਹੀ ਹੈ, "
                    "ਤਾਂ ਕਿਰਪਾ ਕਰਕੇ ਤੁਰੰਤ ਫ਼ੋਨ ਕੱਟੋ ਅਤੇ ਐਮਰਜੈਂਸੀ ਸੇਵਾਵਾਂ ਨੂੰ ਕਾਲ ਕਰੋ ਜਾਂ ਨੇੜਲੇ ਹਸਪਤਾਲ ਜਾਓ।"
                )
            else:
                speech_response = (
                    "If you are experiencing severe symptoms such as chest pain or difficulty breathing, "
                    "please hang up immediately and dial 911 or go to the nearest emergency room."
                )

        elif decision.intent in [IntentCategory.CLINIC_INFORMATION, IntentCategory.PATIENT_RECORD_LOOKUP]:
            speech_response, rag_used = self._handle_rag_branch(clean_text, decision)

        elif self._should_execute_tool(decision):
            speech_response, tool_used_name = self._handle_tool_branch(clean_text, decision)

        else:
            # Conversational Branch (gathers patient info, doctor preference, or answers queries)
            speech_response = self._handle_conversational_branch(clean_text)

        # 5. Save Assistant Output to Memory
        self.memory.add_assistant_message(speech_response)

        # 6. Return immediate BrainOutput without waiting for background extraction
        return BrainOutput(
            speech_text=speech_response,
            intent_detected=decision.intent,
            rag_used=rag_used,
            tool_used=tool_used_name,
            patient_ingestion_payload=None  # Can be harvested asynchronously post-call
        )

    def _should_execute_tool(self, decision: IntentDecision) -> bool:
        """Determines if the decision has sufficient parameters to execute a backend tool call."""
        if not decision.tool_name:
            return False

        params = decision.tool_parameters or {}

        if decision.tool_name == ToolName.VERIFY_PATIENT_IDENTITY:
            has_name = bool(params.get("full_name") or (params.get("first_name") and params.get("last_name")))
            has_dob = bool(params.get("dob") or params.get("date_of_birth"))
            return has_name and has_dob

        if decision.tool_name == ToolName.BOOK_APPOINTMENT:
            has_doc = bool(params.get("doctor") or params.get("doctor_name") or params.get("doctor_name_or_specialty"))
            has_time = bool(params.get("time") or params.get("appointment_time") or params.get("slot_time"))
            return has_doc and has_time

        if decision.tool_name == ToolName.CANCEL_APPOINTMENT:
            return bool(params.get("appointment_id"))

        if decision.tool_name == ToolName.CHECK_AVAILABILITY:
            return bool(
                params.get("doctor")
                or params.get("doctor_name")
                or params.get("specialty")
                or params.get("date")
            )

        return True

    def _generate_llm_response(self, system_instruction: str, user_content: str, temperature: float = 0.5) -> str:
        """Helper to invoke Azure OpenAI chat completion tuned for low-latency voice synthesis."""
        if not self.client:
            return "Thank you for contacting MedFront Clinic. How can I help you today?"

        try:
            res = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
                max_tokens=100,  # Strict cap for fast spoken responses (1-2 sentences)
            )
            content = res.choices[0].message.content or ""
            return content.strip()
        except Exception as e:
            logger.error(f"Azure OpenAI call failed: {e}")
            return "I'm here to assist you at MedFront Clinic. Could you please clarify your request?"


    def _get_language_instruction(self) -> str:
        """Returns mandatory language enforcement instruction for the LLM prompt."""
        if self.memory.language == "Hindi":
            return (
                "\n[MANDATORY LANGUAGE & GENDER DIRECTIVE]: The active conversation language is HINDI. "
                "You MUST reply in fluent, natural Hindi using Devanagari script (e.g. 'डॉक्टर विक्रम सेन कल उपलब्ध हैं...'). "
                "CRITICAL GRAMMAR RULE: Aura is FEMALE. You MUST ALWAYS speak using FEMALE first-person grammatical inflections "
                "(स्त्रीलिंग क्रिया रूप). Use 'देखती हूँ', 'करती हूँ', 'बताती हूँ', 'मदद कर सकती हूँ', 'बुक कर देती हूँ'. "
                "NEVER use masculine forms like 'देखता हूँ', 'करता हूँ', 'बताता हूँ', 'सकता हूँ'. "
                "Do NOT reply in English."
            )
        if self.memory.language == "Punjabi":
            return (
                "\n[MANDATORY LANGUAGE & GENDER DIRECTIVE]: The active conversation language is PUNJABI. "
                "You MUST reply in fluent, natural Punjabi using Gurmukhi script. "
                "CRITICAL GRAMMAR RULE: Aura is FEMALE. You MUST speak using FEMALE first-person grammatical inflections "
                "(ਇਸਤਰੀ ਲਿੰਗ: 'ਮੈਂ ਵੇਖਦੀ ਹਾਂ', 'ਮੈਂ ਕਰਦੀ ਹਾਂ', 'ਮੈਂ ਮਦਦ ਕਰ ਸਕਦੀ ਹਾਂ'). "
                "Do NOT reply in English."
            )
        return "\n[MANDATORY LANGUAGE]: Reply in clear, professional English."

    def _handle_conversational_branch(self, user_text: str) -> str:
        """Handles casual conversation and general pleasantries."""
        user_prompt = (
            f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n\n"
            f"Respond naturally to the patient:{self._get_language_instruction()}"
        )
        return self._generate_llm_response(RECEPTIONIST_SYSTEM_PROMPT, user_prompt)

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
            if self.memory.language == "Hindi":
                fallback = "माफ़ कीजिए, मुझे इस समय यह जानकारी नहीं मिल पा रही है। क्या आप चाहते हैं कि मैं आपकी बात किसी क्लिनिक स्टाफ से करा दूँ?"
            elif self.memory.language == "Punjabi":
                fallback = "ਮਾਫ਼ ਕਰਨਾ, ਮੈਨੂੰ ਇਸ ਸਮੇਂ ਇਹ ਜਾਣਕਾਰੀ ਨਹੀਂ ਮਿਲ ਰਹੀ। ਕੀ ਤੁਸੀਂ ਚਾਹੁੰਦੇ ਹੋ ਕਿ ਮੈਂ ਤੁਹਾਡੀ ਗੱਲ ਕਲੀਨਿਕ ਸਟਾਫ ਨਾਲ ਕਰਵਾਵਾਂ?"
            else:
                fallback = (
                    "I apologize, but I am currently unable to retrieve that information from our records. "
                    "Would you like me to transfer you to a staff member?"
                )
            return (fallback, True)

        context_str = "\n".join(rag_res.retrieved_chunks)
        user_prompt = (
            f"[Retrieved Information]:\n{context_str}\n\n"
            f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n\n"
            f"Answer the patient concisely using the retrieved information above without medical diagnosis:{self._get_language_instruction()}"
        )

        reply = self._generate_llm_response(RECEPTIONIST_SYSTEM_PROMPT, user_prompt)
        return (reply, True)

    def _handle_tool_branch(self, user_text: str, decision: IntentDecision) -> tuple[str, Optional[str]]:
        """Executes backend tool request and formulates user confirmation message."""
        tool_name = decision.tool_name or ToolName.CHECK_AVAILABILITY
        params = dict(decision.tool_parameters or {})

        from src.actions.tools import extract_phone_number
        detected_phone = extract_phone_number(user_text)
        if detected_phone:
            self.memory.update_session(phone_number=detected_phone)
            params["phone_number"] = detected_phone
        elif self.memory.phone_number and "phone_number" not in params:
            params["phone_number"] = self.memory.phone_number

        # Automatically inject verified session patient_id or verified_name if available
        if self.memory.patient_id and "patient_id" not in params:
            params["patient_id"] = self.memory.patient_id
        if self.memory.verified_name and "full_name" not in params:
            params["full_name"] = self.memory.verified_name

        # If name is not in params, check if user text says "for <Name>" or "name is <Name>"
        if "full_name" not in params and not params.get("patient_id"):
            name_match = re.search(r'\b(?:name is|for|i am|iam)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', user_text, re.IGNORECASE)
            if name_match:
                extracted_name = name_match.group(1).strip()
                if extracted_name.lower() not in ["dr", "tomorrow", "today", "an appointment", "the appointment"]:
                    params["full_name"] = extracted_name

        # For appointment booking:
        if tool_name == ToolName.BOOK_APPOINTMENT:
            # Merge any pending details from previous turn
            if self.memory.pending_doctor and "doctor" not in params and "doctor_name" not in params:
                params["doctor"] = self.memory.pending_doctor
            if self.memory.pending_date and "date" not in params and "appointment_date" not in params:
                params["date"] = self.memory.pending_date
            if self.memory.pending_time and "time" not in params and "appointment_time" not in params:
                params["time"] = self.memory.pending_time

            doc_to_save = params.get("doctor") or params.get("doctor_name")
            date_to_save = params.get("date") or params.get("appointment_date")
            time_to_save = params.get("time") or params.get("appointment_time")
            name_to_save = params.get("full_name") or self.memory.verified_name

            if doc_to_save or date_to_save or time_to_save or name_to_save:
                self.memory.update_session(
                    pending_doctor=doc_to_save,
                    pending_date=date_to_save,
                    pending_time=time_to_save,
                    verified_name=name_to_save
                )

            # Check if this is an unverified / new patient without a phone number
            is_unverified = not self.memory.patient_id and not params.get("patient_id")
            if is_unverified and not params.get("phone_number"):
                name_disp = (name_to_save or "").strip().title()
                if self.memory.language == "Hindi":
                    ask_msg = f"धन्यवाद{' ' + name_disp if name_disp else ''}! एक नए मरीज़ के रूप में आपका पंजीकरण पूरा करने और अपॉइंटमेंट कन्फर्मेशन टिकट भेजने के लिए, क्या मुझे आपका संपर्क फोन नंबर मिल सकता है?"
                elif self.memory.language == "Punjabi":
                    ask_msg = f"ਧੰਨਵਾਦ{' ' + name_disp if name_disp else ''}! ਨਵੇਂ ਮਰੀਜ਼ ਵਜੋਂ ਤੁਹਾਡੀ ਰਜਿਸਟ੍ਰੇਸ਼ਨ ਪੂਰੀ ਕਰਨ ਅਤੇ ਟਿਕਟ ਭੇਜਣ ਲਈ, ਕੀ ਮੈਨੂੰ ਤੁਹਾਡਾ ਫ਼ੋਨ ਨੰਬਰ ਮਿਲ ਸਕਦਾ ਹੈ?"
                else:
                    ask_msg = f"Thank you{' ' + name_disp if name_disp else ''}! To complete your registration as a new patient and send your appointment confirmation ticket, may I please have your contact phone number?"
                return (ask_msg, "ask_phone_number")

        tool_req = ToolCallRequest(
            tool_name=tool_name,
            parameters=params
        )

        tool_res = self.tool_registry.execute_tool(tool_req)

        # Update Session Memory if patient identity verified or new patient booked
        if tool_res.success and tool_res.output_data:
            pid = tool_res.output_data.get("patient_id")
            if pid:
                self.memory.update_session(patient_id=pid)

            if tool_name == ToolName.CHECK_AVAILABILITY:
                scheds = tool_res.output_data.get("schedules", [])
                sug_doc = tool_res.output_data.get("suggested_doctor") or (scheds[0].get("doctor_name") if scheds else None)
                sug_date = tool_res.output_data.get("suggested_date") or (scheds[0].get("date") if scheds else None)
                if sug_doc or sug_date:
                    self.memory.update_session(pending_doctor=sug_doc, pending_date=sug_date)

        if not tool_res.success:
            user_prompt = (
                f"[Tool Execution Notification]: The action '{tool_name.value}' could not be completed because: {tool_res.user_message or tool_res.error_message}\n\n"
                f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n\n"
                f"As Aura the receptionist, explain this politely and guide the caller on the next step in 1-2 spoken sentences:{self._get_language_instruction()}"
            )
            reply = self._generate_llm_response(RECEPTIONIST_SYSTEM_PROMPT, user_prompt)
            return (reply, tool_name.value)

        # Low-latency optimization: if in English and tool returned a direct spoken message, return it directly!
        if self.memory.language == "English" and tool_res.user_message:
            return (tool_res.user_message, tool_name.value)

        user_prompt = (
            f"[Backend Tool Execution Result]: {tool_res.user_message}\n\n"
            f"[Conversation History]:\n{self.memory.get_formatted_transcript()}\n\n"
            f"Convey this result politely to the patient in 1-2 spoken sentences:{self._get_language_instruction()}"
        )

        reply = self._generate_llm_response(RECEPTIONIST_SYSTEM_PROMPT, user_prompt)
        return (reply, tool_name.value)

    def _harvest_patient_metadata(self) -> Dict[str, Any]:
        """Harvests structured patient info from transcript using native JSON mode."""
        if not self.client:
            return PatientInfoPayload().to_dict()

        try:
            transcript = self.memory.get_formatted_transcript(max_turns=10)
            res = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": PATIENT_INFO_EXTRACTION_PROMPT},
                    {"role": "user", "content": f"[Transcript]:\n{transcript}"}
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            raw_text = (res.choices[0].message.content or "").strip()
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

        except Exception as e:
            logger.debug(f"Patient metadata harvesting skipped: {e}")
            return PatientInfoPayload().to_dict()

    def reset(self) -> None:
        """Resets orchestrator state and memory."""
        self.memory.clear()
