"""
Conversation Memory & Session State Manager for MedFront-AI Brain.
Tracks chat turn history and session variables across multi-turn interactions.
"""

from typing import List, Dict, Any, Optional
from src.brain.taxonomy import IntentCategory


class ConversationMemory:
    """
    Manages in-memory chat message history and session state.
    """

    def __init__(self) -> None:
        # Message History List: [{"role": "user"|"assistant"|"system", "content": "text"}]
        self.messages: List[Dict[str, str]] = []

        # Session Context Variables
        self.patient_id: Optional[str] = None
        self.verified_name: Optional[str] = None
        self.dob: Optional[str] = None
        self.active_intent: IntentCategory = IntentCategory.CASUAL_CONVERSATION

    def add_user_message(self, text: str) -> None:
        """Appends a user input turn to memory."""
        self.messages.append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        """Appends an assistant output turn to memory."""
        self.messages.append({"role": "assistant", "content": text})

    def update_session(
        self,
        patient_id: Optional[str] = None,
        verified_name: Optional[str] = None,
        dob: Optional[str] = None,
        intent: Optional[IntentCategory] = None
    ) -> None:
        """Updates active patient session metadata."""
        if patient_id:
            self.patient_id = patient_id
        if verified_name:
            self.verified_name = verified_name
        if dob:
            self.dob = dob
        if intent:
            self.active_intent = intent

    def get_formatted_transcript(self, max_turns: int = 6) -> str:
        """
        Returns a formatted text string transcript of the last N turns for LLM context.
        """
        recent_messages = self.messages[-max_turns:]
        transcript = ""
        for msg in recent_messages:
            role_label = "Patient" if msg["role"] == "user" else "Aura"
            transcript += f"{role_label}: {msg['content']}\n"
        return transcript

    def clear(self) -> None:
        """Resets memory and session state back to turn 0."""
        self.messages.clear()
        self.patient_id = None
        self.verified_name = None
        self.dob = None
        self.active_intent = IntentCategory.CASUAL_CONVERSATION
