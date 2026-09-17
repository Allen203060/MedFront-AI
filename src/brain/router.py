"""
LLM-Driven Intent Router for MedFront-AI Agentic Brain.
Classifies user intent, determines routing targets (RAG vs Tools), and extracts parameters.
"""
from google.genai import types

import json
import os
from dotenv import load_dotenv
from google import genai
from src.brain.memory import ConversationMemory
from src.brain.models import IntentDecision
from src.brain.prompts import ROUTER_SYSTEM_PROMPT
from src.brain.taxonomy import IntentCategory, ToolName

load_dotenv()


class IntentRouter:
    """
    Analyzes user turn + conversation context using Google Gemini to produce an IntentDecision.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash")

        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY in environment variables.")

        self.client = genai.Client(api_key=self.api_key)

    def classify_intent(self, memory: ConversationMemory, current_text: str) -> IntentDecision:
        """
        Analyzes the latest user message + memory transcript and returns a structured IntentDecision.
        """
        # Format recent transcript context for multi-turn awareness
        transcript = memory.get_formatted_transcript(max_turns=6)
        
        prompt = (
            f"{ROUTER_SYSTEM_PROMPT}\n\n"
            f"[Conversation History]:\n{transcript}\n"
            f"[Current Patient Input]: {current_text}\n\n"
            f"Output JSON:"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Low temperature for deterministic intent classification
                )
            )

            raw_text = response.text.strip() if response.text else "{}"

            # Clean markdown code blocks if present
            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "").strip()

            data = json.loads(raw_text)

            # Map intent string to Enum safely
           # Replace lines 61-67 with:
            raw_intent = str(data.get("intent", "CASUAL_CONVERSATION")).strip().replace(" ", "_").upper()

            try:
                intent_enum = IntentCategory(raw_intent)
            except ValueError:
                intent_enum = IntentCategory.CASUAL_CONVERSATION


            # Map tool name safely
            raw_tool = data.get("tool_name")
            tool_enum = None
            if raw_tool:
                try:
                    tool_enum = ToolName(raw_tool)
                except ValueError:
                    tool_enum = None

            return IntentDecision(
                intent=intent_enum,
                confidence=float(data.get("confidence", 1.0)),
                rag_query=data.get("rag_query"),
                target_index=data.get("target_index"),
                tool_name=tool_enum,
                tool_parameters=data.get("tool_parameters", {}),
                reasoning=data.get("reasoning", "")
            )

        except Exception as e:
            # Fallback defensively if LLM output fails to parse
            return IntentDecision(
                intent=IntentCategory.CASUAL_CONVERSATION,
                confidence=0.5,
                reasoning=f"Router fallback due to exception: {str(e)}"
            )
