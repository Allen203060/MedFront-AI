"""
LLM-Driven Intent Router for MedFront-AI Agentic Brain.
Classifies user intent and routing targets using Azure OpenAI with strict JSON output.
"""

import json
import logging
from src.core.config import settings
from src.brain.azure_client import get_azure_openai_client
from src.brain.memory import ConversationMemory
from src.brain.models import IntentDecision
from src.brain.prompts import ROUTER_SYSTEM_PROMPT
from src.brain.taxonomy import IntentCategory, ToolName

logger = logging.getLogger("medfront.brain.router")


class IntentRouter:
    """
    Analyzes user turn + conversation context using Azure OpenAI to produce an IntentDecision.
    """

    def __init__(self) -> None:
        self.deployment_name = settings.azure_openai_deployment_name
        self.client = get_azure_openai_client()

    def classify_intent(self, memory: ConversationMemory, current_text: str) -> IntentDecision:
        """
        Analyzes the latest user message + memory transcript and returns a structured IntentDecision.
        """
        transcript = memory.get_formatted_transcript(max_turns=6)
        from datetime import date
        today_str = date.today().strftime("%Y-%m-%d (%A)")
        
        user_prompt = (
            f"[Current Reference Date]: {today_str}\n"
            f"[Conversation History]:\n{transcript}\n\n"
            f"[Current Patient Input]: {current_text}"
        )

        if not self.client:
            logger.warning("Azure OpenAI unconfigured. Defaulting to CASUAL_CONVERSATION.")
            return IntentDecision(
                intent=IntentCategory.CASUAL_CONVERSATION,
                confidence=1.0,
                reasoning="Offline default"
            )

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            raw_text = response.choices[0].message.content.strip()
            data = json.loads(raw_text)

            raw_intent = str(data.get("intent", "CASUAL_CONVERSATION")).strip().replace(" ", "_").upper()
            try:
                intent_enum = IntentCategory(raw_intent)
            except ValueError:
                intent_enum = IntentCategory.CASUAL_CONVERSATION

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
            logger.error(f"Intent classification failed: {e}")
            return IntentDecision(
                intent=IntentCategory.CASUAL_CONVERSATION,
                confidence=0.5,
                reasoning=f"Router fallback due to exception: {str(e)}"
            )
