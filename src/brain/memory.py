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
        self.phone_number: Optional[str] = None
        self.pending_doctor: Optional[str] = None
        self.pending_date: Optional[str] = None
        self.pending_time: Optional[str] = None
        self.active_intent: IntentCategory = IntentCategory.CASUAL_CONVERSATION
        self.language: str = "English"

    def detect_and_update_language(self, text: str) -> str:
        """
        Detects Hindi, Punjabi, or English from caller input and dynamically maintains language state.
        Allows fluid turn-by-turn code-switching: if user switches from Hindi to English, it immediately
        switches to English. Short neutral replies (e.g. times, numbers, doctor names) retain previous language.
        """
        lower = text.lower().strip()
        words = [w.strip(".,!?;:'\"") for w in lower.split()]
        word_set = set(words)

        # 1. Direct Script Detection (Highest Confidence)
        if any("\u0900" <= ch <= "\u097F" for ch in text):
            self.language = "Hindi"
            return self.language
        if any("\u0A00" <= ch <= "\u0A7F" for ch in text):
            self.language = "Punjabi"
            return self.language

        # 2. Explicit Language Switch Requests
        if any(phrase in lower for phrase in ["speak in english", "talk in english", "switch to english", "in english please", "in english"]):
            self.language = "English"
            return self.language
        if any(phrase in lower for phrase in ["speak in hindi", "talk in hindi", "hindi me", "hindi mein", "hindi please", "in hindi"]):
            self.language = "Hindi"
            return self.language
        if any(phrase in lower for phrase in ["speak in punjabi", "talk in punjabi", "punjabi vich", "punjabi please", "in punjabi"]):
            self.language = "Punjabi"
            return self.language

        # 3. Keyword / Lexical Pattern Matching for Indic Languages
        hindi_markers = {
            "namaste", "shukriya", "dhanyawad", "aap", "mera", "meri", "mere",
            "mujhe", "kripya", "chahiye", "batao", "batayein", "kijiye", "karna",
            "kaise", "kab", "kya", "theek", "kal", "aana", "milna", "bataiye",
            "hai", "hain", "karo", "nahi", "nahin", "accha", "achha", "doctorji"
        }
        punjabi_markers = {
            "sat sri akal", "sasrikaal", "mainu", "tussi", "tuhada", "tuhadi",
            "kiddan", "chahida", "chahidi", "daso", "dasso", "veere", "paaji",
            "kivein", "kive", "ethe", "kithe", "nal", "karvana", "karna", "haye"
        }

        has_punjabi = any(m in lower for m in punjabi_markers)
        has_hindi = any(m in lower for m in hindi_markers)

        if has_punjabi:
            self.language = "Punjabi"
            return self.language

        if has_hindi:
            self.language = "Hindi"
            return self.language

        # 4. English Conversational Detection & Fluid Code-Switching
        english_markers = {
            "i", "im", "i'm", "my", "me", "you", "your", "we", "our", "they", "he", "she",
            "can", "could", "would", "will", "do", "does", "did", "have", "has", "had",
            "is", "am", "are", "was", "were", "what", "when", "where", "which", "who", "why", "how",
            "want", "need", "book", "appointment", "schedule", "doctor", "dr", "please",
            "thanks", "thank", "hello", "hi", "hey", "good", "morning", "afternoon", "evening",
            "tomorrow", "today", "slot", "slots", "available", "first", "time", "visiting",
            "new", "patient", "name", "call", "help", "visit", "check", "see"
        }
        matched_english_words = word_set.intersection(english_markers)

        # If the turn contains recognizable English words/structure and no Indic markers:
        if len(matched_english_words) >= 1 and not (has_hindi or has_punjabi):
            self.language = "English"
            return self.language

        # 5. Short Neutral Persistence (e.g. "10:00 AM", "Tomorrow", "Dr. Rao", "Yes", "No")
        # Retain the active conversation language if neither language has distinct markers
        return self.language

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
        phone_number: Optional[str] = None,
        pending_doctor: Optional[str] = None,
        pending_date: Optional[str] = None,
        pending_time: Optional[str] = None,
        intent: Optional[IntentCategory] = None
    ) -> None:
        """Updates active patient session metadata."""
        if patient_id:
            self.patient_id = patient_id
        if verified_name:
            self.verified_name = verified_name
        if dob:
            self.dob = dob
        if phone_number:
            self.phone_number = phone_number
        if pending_doctor:
            self.pending_doctor = pending_doctor
        if pending_date:
            self.pending_date = pending_date
        if pending_time:
            self.pending_time = pending_time
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
        self.phone_number = None
        self.pending_doctor = None
        self.pending_date = None
        self.pending_time = None
        self.active_intent = IntentCategory.CASUAL_CONVERSATION
        self.language = "English"
