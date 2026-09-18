"""
MedFront Continuous Speech-to-Text (STT) Engine.
Integrates Azure AI Speech SDK with PhraseListGrammar domain biasing,
configurable language locale, and calibrated conversational VAD.
"""

import logging
from typing import Callable, Optional
import azure.cognitiveservices.speech as speechsdk
from src.core.config import settings

logger = logging.getLogger("medfront.speech.stt")


class SpeechToTextEngine:
    """
    Manages continuous speech recognition from an in-memory audio push stream.
    Optimized with medical domain phrase lists and accent-aware language configuration.
    """

    def __init__(
        self,
        on_interim_result: Optional[Callable[[str], None]] = None,
        on_final_result: Optional[Callable[[str], None]] = None,
        end_silence_timeout_ms: int = 1200,
        initial_silence_timeout_ms: int = 5000,
    ) -> None:
        if not settings.azure_speech_key:
            logger.warning("AZURE_SPEECH_KEY is not set. STT engine is in offline mock mode.")
            self.speech_config = None
            self.recognizer = None
            self.push_stream = None
            return

        self.on_interim_result = on_interim_result
        self.on_final_result = on_final_result

        # 1. Configure Azure Speech Service connection with accent/locale support
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )
        self.speech_config.speech_recognition_language = settings.azure_speech_language
        logger.info(f"STT initialized with language: {settings.azure_speech_language}")

        # 2. Conversational Voice Activity Detection (VAD) Tuning & Noise Suppression
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
            str(end_silence_timeout_ms),
        )
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
            str(initial_silence_timeout_ms),
        )
        # Suppress breath/air turbulence false interim triggers by requiring 2 stable decoder hypotheses
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_StablePartialResultThreshold,
            "2",
        )
        # Enable TrueText for disfluency cleaning and inverse text normalization
        self.speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceResponse_PostProcessingOption,
            "TrueText",
        )

        # 3. Audio Stream Format: 16kHz, 16-bit, Mono PCM
        self.audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000,
            bits_per_sample=16,
            channels=1,
        )
        self.push_stream = speechsdk.audio.PushAudioInputStream(stream_format=self.audio_format)
        self.audio_config = speechsdk.audio.AudioConfig(stream=self.push_stream)

        # 4. Instantiate Recognizer
        self.recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=self.audio_config,
        )

        # 5. Domain Phrase List Grammar (Biases acoustic model toward clinic terms)
        self._inject_medical_phrase_list()

        # 6. Connect Event Listeners
        self._register_callbacks()
        self._is_running = False

    def _inject_medical_phrase_list(self) -> None:
        """Injects clinic and medical specialties into the recognizer's grammar model."""
        phrase_list = speechsdk.PhraseListGrammar.from_recognizer(self.recognizer)
        medical_terms = [
            # Specialties & spoken department variations
            "Cardiology", "Cardio", "Cardiologist", "Cardio Department", "Cardiology Department",
            "Cardiac", "Heart Specialist", "Heart Department", "Cardio Clinic",
            "General Physician", "General Medicine", "General Practice", "Internal Medicine",
            "Dermatology", "Dermatologist", "Skin Department", "Skin Specialist", "Skin Clinic",
            "Pediatrics", "Pediatrician", "Orthopedics", "Neurology", "Radiology",
            
            # Clinician names (Indian context)
            "Dr. Ananya Rao", "Dr. Ananya", "Ananya Rao", "Ananya",
            "Dr. Rajesh Iyer", "Dr. Rajesh", "Rajesh Iyer", "Rajesh",
            "Dr. Sunita Kapoor", "Dr. Sunita", "Sunita Kapoor", "Sunita",
            
            # Clinic branding & regional terms
            "MedFront Health Clinic", "MedFront", "AuraCare Health Clinic", "AuraCare",
            "Koramangala", "Bengaluru", "Bangalore", "Receptionist", "Aura",
            
            # Conversational scheduling & administrative terms
            "Appointment", "Book an appointment", "Schedule availability", "Consultation",
            "Follow-up", "Reschedule", "Cancellation", "Prescription", "Blood test", "Lab report",
            "Tomorrow", "Today", "Next Monday", "Next Tuesday", "Next Wednesday", "Next Thursday", "Next Friday",
            "Morning slot", "Afternoon slot", "Evening slot", "Emergency", "Insurance", "Star Health", "HDFC ERGO",
            
            # Patient names
            "Aarav Sharma", "Priya Patel", "Vikram Malhotra"
        ]
        for term in medical_terms:
            phrase_list.addPhrase(term)
        logger.info(f"Loaded {len(medical_terms)} medical and clinic phrase hints into STT model.")

    def _register_callbacks(self) -> None:
        self.recognizer.recognizing.connect(self._handle_recognizing)
        self.recognizer.recognized.connect(self._handle_recognized)
        self.recognizer.session_started.connect(self._handle_session_started)
        self.recognizer.session_stopped.connect(self._handle_session_stopped)
        self.recognizer.canceled.connect(self._handle_canceled)

    def _handle_recognizing(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            partial_text = evt.result.text.strip()
            if partial_text and self.on_interim_result:
                self.on_interim_result(partial_text)

    def _handle_recognized(self, evt: speechsdk.SpeechRecognitionEventArgs) -> None:
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            final_text = evt.result.text.strip()
            if final_text and self.on_final_result:
                self.on_final_result(final_text)
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            logger.debug("[STT NoMatch]: Silence or noise.")

    def _handle_session_started(self, evt: speechsdk.SessionEventArgs) -> None:
        logger.info(f"STT Session started: {evt.session_id}")

    def _handle_session_stopped(self, evt: speechsdk.SessionEventArgs) -> None:
        logger.info(f"STT Session stopped: {evt.session_id}")
        self._is_running = False

    def _handle_canceled(self, evt: speechsdk.SpeechRecognitionCanceledEventArgs) -> None:
        logger.warning(f"STT Canceled: Reason={evt.reason}")
        if evt.reason == speechsdk.CancellationReason.Error:
            logger.error(f"STT ErrorDetails: {evt.error_details}")

    def write_audio_chunk(self, pcm_bytes: bytes) -> None:
        if self.push_stream and pcm_bytes:
            self.push_stream.write(pcm_bytes)

    def close_stream(self) -> None:
        if self.push_stream:
            self.push_stream.close()

    def start_recognition(self) -> None:
        if not self.recognizer or self._is_running:
            return
        logger.info("Starting continuous speech recognition...")
        self.recognizer.start_continuous_recognition_async()
        self._is_running = True

    def stop_recognition(self) -> None:
        if not self.recognizer or not self._is_running:
            return
        logger.info("Stopping continuous speech recognition...")
        self.recognizer.stop_continuous_recognition_async()
        self._is_running = False
