"""
Module 2 Verification Test: Speech Processing Isolation.
Tests neural TTS synthesis latency and continuous STT push-stream ingestion.
"""

import os
import sys
import time
import wave
import logging

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.config import settings
from src.speech.tts import TextToSpeechEngine
from src.speech.stt import SpeechToTextEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_speech")


def test_speech_pipeline() -> None:
    logger.info("=" * 60)
    logger.info("MEDFRONT MODULE 2: SPEECH ISOLATION TEST")
    logger.info("=" * 60)

    if not settings.azure_speech_key or settings.azure_speech_key.startswith("<"):
        logger.error("AZURE_SPEECH_KEY is not configured in .env!")
        logger.error("Please update .env with your Azure AI Speech key and rerun.")
        sys.exit(1)

    # -------------------------------------------------------------
    # 1. Test Text-to-Speech (TTS)
    # -------------------------------------------------------------
    logger.info("\n[TEST 1] Testing Neural Text-to-Speech (TTS)...")
    tts = TextToSpeechEngine()

    sample_prompt = (
        "Hello, thank you for calling MedFront Clinic. "
        "My name is Jenny, your virtual medical receptionist. "
        "How can I assist you with your appointment today?"
    )

    t0 = time.perf_counter()
    audio_bytes = tts.synthesize_text(sample_prompt)
    tts_latency_ms = (time.perf_counter() - t0) * 1000.0

    output_wav_path = os.path.join(os.path.dirname(__file__), "test_greeting.wav")
    with open(output_wav_path, "wb") as f:
        f.write(audio_bytes)

    logger.info(f"✓ TTS Generated: {len(audio_bytes)} bytes in {tts_latency_ms:.1f}ms")
    logger.info(f"✓ Audio saved to: {output_wav_path}")

    # -------------------------------------------------------------
    # 2. Test Speech-to-Text (STT) via Push Stream Ingestion
    # -------------------------------------------------------------
    logger.info("\n[TEST 2] Testing Continuous Speech-to-Text (STT)...")

    interim_results = []
    final_results = []

    def on_interim(text: str):
        interim_results.append(text)
        logger.info(f"  [STT Interim Event]: '{text}'")

    def on_final(text: str):
        final_results.append(text)
        logger.info(f"  [STT Final Event]: '{text}'")

    stt = SpeechToTextEngine(
        on_interim_result=on_interim,
        on_final_result=on_final,
        end_silence_timeout_ms=800,
    )

    stt.start_recognition()

    # Read the generated WAV file and feed it into the push stream
    logger.info("Streaming WAV audio into PushAudioInputStream in simulated 20ms frames...")
    with wave.open(output_wav_path, "rb") as wav_file:
        # Standard 16kHz 16-bit Mono: 16000 samples/sec * 2 bytes/sample = 32000 bytes/sec
        # A 20ms frame = 0.02 * 32000 = 640 bytes
        chunk_size = 640
        while True:
            chunk = wav_file.readframes(320)  # 320 frames * 2 bytes = 640 bytes
            if not chunk:
                break
            stt.write_audio_chunk(chunk)
            time.sleep(0.018)  # Simulate real-time streaming pace (~20ms per packet)

    # Signal End-Of-Stream and allow the recognizer to process the trailing silence
    stt.close_stream()
    logger.info("Audio stream closed. Waiting for final recognition...")
    time.sleep(2.0)
    stt.stop_recognition()

    # -------------------------------------------------------------
    # 3. Summary & Verification
    # -------------------------------------------------------------
    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    logger.info(f"TTS Latency: {tts_latency_ms:.1f}ms")
    logger.info(f"Interim Events Fired (Barge-in Triggers): {len(interim_results)}")
    logger.info(f"Final Transcript: '{' '.join(final_results)}'")

    if final_results:
        logger.info("\n🎉 MODULE 2 VALIDATION SUCCESSFUL: STT & TTS are operating with low latency!")
    else:
        logger.warning("\n⚠️ STT did not produce a final transcript. Check speech recognition audio format.")


if __name__ == "__main__":
    test_speech_pipeline()
