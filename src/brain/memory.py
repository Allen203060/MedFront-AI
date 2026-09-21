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

        # 1. Explicit Language Switch Requests (English, Hindi, Punjabi)
        explicit_english = ["speak in english", "talk in english", "switch to english", "in english please", "in english", "अंग्रेजी में", "अंग्रेज़ी में"]
        if any(phrase in lower for phrase in explicit_english):
            self.language = "English"
            return self.language

        explicit_hindi = ["speak in hindi", "talk in hindi", "hindi me", "hindi mein", "hindi please", "in hindi", "हिंदी में बात करो", "हिंदी में बोलो", "हिंदी में"]
        if any(phrase in lower for phrase in explicit_hindi):
            self.language = "Hindi"
            return self.language

        explicit_punjabi = ["speak in punjabi", "talk in punjabi", "punjabi vich", "punjabi please", "in punjabi", "ਪੰਜਾਬੀ ਵਿੱਚ", "ਪੰਜਾਬੀ ਚ"]
        if any(phrase in lower for phrase in explicit_punjabi):
            self.language = "Punjabi"
            return self.language

        # 2. Transliterated English Phonetics in Indic Script (Common Azure STT artifacts)
        # E.g. "फ़ोन नंबर इज़ 123 ओवर 6789", "माय नेम इज़ दिव्या", "अपॉइंटमेंट फॉर कार्डियो"
        transliterated_english_tokens = {
            "फ़ोन", "फोन", "नंबर", "इज़", "इज", "माय", "नेम", "कार्डियो", "अपॉइंटमेंट",
            "थैंक", "यू", "प्लीज़", "प्लीज", "डॉक्टर", "ओवर", "हेलो", "हाय", "यस",
            "नो", "ओके", "टुमॉरो", "टुमारो", "मॉर्निंग", "इवनिंग", "आफ्टरनून", "फॉर"
        }
        indic_words = [w.strip(".,!?;:'\"|।") for w in text.split() if w.strip(".,!?;:'\"|।")]
        transliterated_matches = [w for w in indic_words if w in transliterated_english_tokens]
        if len(transliterated_matches) >= 2 or any(w in ["इज़", "इज"] for w in indic_words):
            # Caller spoke English which Azure STT phonetically transcribed into Devanagari
            self.language = "English"
            return self.language

        # 3. Direct Indic Script Grammar & Proper Name Filtering
        has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in text)
        has_gurmukhi = any("\u0A00" <= ch <= "\u0A7F" for ch in text)

        # Devanagari grammatical markers indicating genuine Hindi sentences
        hindi_script_markers = {
            "है", "हैं", "था", "थी", "थे", "हो", "हूँ", "हू", "करो", "कीजिए", "करना",
            "चाहिए", "बताओ", "बताइए", "दिखाना", "मिलना", "लेना", "सकता", "सकती",
            "सकते", "आना", "जाना", "बोलिए", "बोलो", "दीजिए", "दो", "करवाएं", "करवाना",
            "मेरा", "मेरी", "मेरे", "मुझे", "मुझको", "हमारा", "हमारी", "हम",
            "आप", "आपका", "आपकी", "आपके", "तुम", "तुम्हारा", "तुम्हारी",
            "क्या", "कब", "कहाँ", "कैसे", "कौन", "कितना", "कितनी", "किस",
            "नमस्ते", "नमस्कार", "धन्यवाद", "शुक्रिया", "कृपया", "हाँ", "नहीं",
            "अच्छा", "ठीक", "कल", "आज", "परसों", "समय"
        }

        # Gurmukhi grammatical markers indicating genuine Punjabi sentences
        punjabi_script_markers = {
            "ਹੈ", "ਹਨ", "ਸੀ", "ਸਨ", "ਕਰਨਾ", "ਕਰੋ", "ਦੱਸੋ", "ਦੱਸ", "ਚਾਹੀਦਾ", "ਚਾਹੀਦੀ",
            "ਮੈਨੂੰ", "ਤੁਸੀਂ", "ਤੁਹਾਡਾ", "ਤੁਹਾਡੀ", "ਸਤਿ", "ਸ਼੍ਰੀ", "ਅਕਾਲ", "ਕਿਵੇਂ", "ਕਿੱਥੇ",
            "ਕੱਲ੍ਹ", "ਅੱਜ", "ਹਾਂ", "ਨਹੀਂ", "ਜੀ"
        }

        if self.language == "English":
            # If the ongoing session is in English:
            # Single words or short phrases (<= 2 words like "दिव्या" or "दिव्या शर्मा")
            # are proper names/entities, NOT a request to switch the conversation to Hindi.
            if has_devanagari:
                matched_hindi = [w for w in indic_words if w in hindi_script_markers]
                if len(indic_words) <= 2 and not matched_hindi:
                    # Isolated name or entity: Retain English session language
                    return self.language
                if matched_hindi or len(indic_words) >= 4:
                    self.language = "Hindi"
                    return self.language
                return self.language

            if has_gurmukhi:
                matched_punjabi = [w for w in indic_words if w in punjabi_script_markers]
                if len(indic_words) <= 2 and not matched_punjabi:
                    # Isolated name or entity: Retain English session language
                    return self.language
                if matched_punjabi or len(indic_words) >= 4:
                    self.language = "Punjabi"
                    return self.language
                return self.language
        else:
            # Ongoing session is Hindi or Punjabi:
            if has_devanagari and not has_gurmukhi:
                matched_hindi = [w for w in indic_words if w in hindi_script_markers]
                if len(indic_words) <= 2 and not matched_hindi:
                    return self.language
                self.language = "Hindi"
                return self.language

            if has_gurmukhi and not has_devanagari:
                matched_punjabi = [w for w in indic_words if w in punjabi_script_markers]
                if len(indic_words) <= 2 and not matched_punjabi:
                    return self.language
                self.language = "Punjabi"
                return self.language

        # 4. Keyword / Lexical Pattern Matching for Romanized Indic Languages
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

        # 5. English Conversational Detection & Fluid Code-Switching
        english_markers = {
            "i", "im", "i'm", "my", "me", "you", "your", "we", "our", "they", "he", "she",
            "can", "could", "would", "will", "do", "does", "did", "have", "has", "had",
            "is", "am", "are", "was", "were", "what", "when", "where", "which", "who", "why", "how",
            "want", "need", "book", "appointment", "schedule", "doctor", "dr", "please",
            "thanks", "thank", "hello", "hi", "hey", "good", "morning", "afternoon", "evening",
            "tomorrow", "today", "slot", "slots", "available", "first", "time", "visiting",
            "new", "patient", "name", "call", "help", "visit", "check", "see", "phone", "number"
        }
        matched_english_words = word_set.intersection(english_markers)

        # If the turn contains recognizable English words/structure and no Indic markers:
        if len(matched_english_words) >= 1 and not (has_hindi or has_punjabi):
            self.language = "English"
            return self.language

        # 6. Short Neutral Persistence (e.g. "10:00 AM", "Tomorrow", "Dr. Rao", "Yes", "No")
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
