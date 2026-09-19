"""
Unit and Integration Tests for Multilingual State Stability and Audio Playback Isolation.
Tests:
1. Proper name and entity immunity in English conversations (prevents Devanagari names from hijacking language).
2. Transliterated English phonetics detection (Azure STT Devanagari outputs for English speech).
3. Legitimate code-switching to Hindi and Punjabi on full grammatical sentences and explicit switch requests.
4. Symmetric turn-by-turn conversation simulation matching the reported user transcript.
"""

import pytest
from src.brain.memory import ConversationMemory


def test_english_session_proper_name_immunity():
    """Single Devanagari names or short proper nouns must NOT flip English session to Hindi."""
    mem = ConversationMemory()
    mem.language = "English"

    # User speaks their name, which Azure STT transcribes as Devanagari
    assert mem.detect_and_update_language("दिव्या।") == "English"
    assert mem.detect_and_update_language("दिव्या") == "English"
    assert mem.detect_and_update_language("अमित") == "English"
    assert mem.detect_and_update_language("दिव्या शर्मा") == "English"
    assert mem.detect_and_update_language("रोहन कपूर") == "English"


def test_transliterated_english_in_devanagari():
    """English sentences phonetically transcribed into Devanagari by Azure STT must remain English."""
    mem = ConversationMemory()
    mem.language = "English"

    # Exact user phrase from transcript
    assert mem.detect_and_update_language("फ़ोन नंबर इज़ 123 ओवर 6789।") == "English"
    assert mem.detect_and_update_language("माय नेम इज़ दिव्या") == "English"
    assert mem.detect_and_update_language("कार्डियो अपॉइंटमेंट फॉर टुमॉरो") == "English"


def test_legitimate_hindi_switching():
    """Full Hindi sentences with grammatical markers or explicit switch requests must switch to Hindi."""
    mem = ConversationMemory()
    mem.language = "English"

    # Grammatical sentences
    assert mem.detect_and_update_language("नमस्ते मुझे डॉक्टर से मिलना है") == "Hindi"
    assert mem.language == "Hindi"

    # Reset to English
    mem.language = "English"
    assert mem.detect_and_update_language("क्या कल कोई स्लॉट उपलब्ध है?") == "Hindi"

    # Reset to English
    mem.language = "English"
    assert mem.detect_and_update_language("मेरा नाम दिव्या है") == "Hindi"

    # Explicit switch commands
    mem.language = "English"
    assert mem.detect_and_update_language("हिंदी में बात करो") == "Hindi"

    mem.language = "English"
    assert mem.detect_and_update_language("speak in hindi") == "Hindi"


def test_legitimate_punjabi_switching():
    """Gurmukhi proper names retain English, while grammatical sentences or explicit requests switch to Punjabi."""
    mem = ConversationMemory()
    mem.language = "English"

    # Name immunity
    assert mem.detect_and_update_language("ਹਰਪ੍ਰੀਤ") == "English"
    assert mem.detect_and_update_language("ਹਰਪ੍ਰੀਤ ਸਿੰਘ") == "English"

    # Grammatical sentence
    assert mem.detect_and_update_language("ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ ਜੀ ਮੈਨੂੰ ਡਾਕਟਰ ਚਾਹੀਦਾ") == "Punjabi"
    assert mem.language == "Punjabi"

    # Switch back to English
    assert mem.detect_and_update_language("Please talk in English now") == "English"
    assert mem.language == "English"


def test_reported_user_conversation_flow():
    """
    Simulates the exact 5-turn sequence reported by the user to guarantee
    the conversation remains completely in English throughout the entire booking flow.
    """
    mem = ConversationMemory()
    assert mem.language == "English"

    # Turn 1
    t1 = "I have to Book an appointment Tomorrow for the Cardio Department."
    mem.add_user_message(t1)
    assert mem.detect_and_update_language(t1) == "English"
    mem.add_assistant_message("Found 6 available slots on 2026-09-20: Dr. Ananya Rao...")

    # Turn 2
    t2 = "Good."
    mem.add_user_message(t2)
    assert mem.detect_and_update_language(t2) == "English"
    mem.add_assistant_message("Great! Which time would you prefer for your appointment with Dr. Ananya Rao tomorrow?")

    # Turn 3
    t3 = "2:00 PM will be good."
    mem.add_user_message(t3)
    assert mem.detect_and_update_language(t3) == "English"
    mem.add_assistant_message("Thank you! To complete your registration as a new patient and send your appointment confirmation ticket, may I please have your full name and contact phone number?")

    # Turn 4: User states name (Transcribed by Azure STT into Devanagari)
    t4 = "दिव्या।"
    mem.add_user_message(t4)
    # MUST REMAIN ENGLISH!
    assert mem.detect_and_update_language(t4) == "English"
    assert mem.language == "English"
    mem.add_assistant_message("Thank you Divya! Please also provide your contact phone number...")

    # Turn 5: User states phone number (Transcribed by Azure STT phonetically into Devanagari)
    t5 = "फ़ोन नंबर इज़ 123 ओवर 6789।"
    mem.add_user_message(t5)
    # MUST REMAIN ENGLISH!
    assert mem.detect_and_update_language(t5) == "English"
    assert mem.language == "English"
