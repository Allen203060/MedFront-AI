"""
Conversation Engine for MedFront-AI.
Manages multi-turn conversation state using Azure OpenAI Service (GPT-4o).
"""

import logging
from typing import List, Dict
from src.core.config import settings
from src.brain.azure_client import get_azure_openai_client
from src.brain.prompts import RECEPTIONIST_SYSTEM_PROMPT

logger = logging.getLogger("medfront.brain.engine")


class ConversationEngine:
    """
    Manages multi-turn conversation state using Azure OpenAI.
    """

    def __init__(self, system_prompt: str = RECEPTIONIST_SYSTEM_PROMPT) -> None:
        self.system_prompt = system_prompt
        self.deployment_name = settings.azure_openai_deployment_name
        self.client = get_azure_openai_client()

        if not self.client:
            logger.warning("ConversationEngine running in mock mode: Azure OpenAI credentials not set.")

        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt}
        ]

    def process_message(self, user_text: str) -> str:
        """
        Sends user text to Azure OpenAI and appends turn to message history.
        """
        clean_text = user_text.strip()
        if not clean_text:
            return "I didn't catch that. Could you please repeat?"

        self.messages.append({"role": "user", "content": clean_text})

        if not self.client:
            reply = f"[Offline Mode] Thank you for calling MedFront Clinic. You said: '{clean_text}'."
            self.messages.append({"role": "assistant", "content": reply})
            return reply

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=self.messages,
            )
            assistant_response = response.choices[0].message.content.strip()
            self.messages.append({"role": "assistant", "content": assistant_response})
            return assistant_response

        except Exception as e:
            logger.error(f"Azure OpenAI Error in process_message: {e}")
            return f"Error communicating with AI engine: {str(e)}"

    def reset_conversation(self) -> None:
        """Clears conversation history and restores the base system prompt."""
        self.messages = [{"role": "system", "content": self.system_prompt}]
