"""
MedFront Neural Text-to-Speech (TTS) Engine.
Integrates Azure AI Speech SDK for neural voice synthesis, memory-streamed
audio chunking, and SSML-enhanced healthcare speech modulation.
"""

import logging
import time
from typing import Generator, Optional
import azure.cognitiveservices.speech as speechsdk
from src.core.config import settings

logger = logging.getLogger("medfront.speech.tts")


class TextToSpeechEngine:
    """
    Manages neural speech synthesis to in-memory byte streams.
    Optimized for low-latency streaming back to the telephony client.
    """

    def __init__(
        self,
        voice_name: Optional[str] = None,
        output_format: speechsdk.SpeechSynthesisOutputFormat = speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
    ) -> None:
        """
        Initializes the SpeechSynthesizer with neural voice settings.

        :param voice_name: The Azure Neural voice identifier (e.g., 'en-US-JennyNeural').
        :param output_format: Audio container/bitrate format (default: 16kHz 16-bit Mono PCM WAV).
        """
        if not settings.azure_speech_key:
            logger.warning("AZURE_SPEECH_KEY is not set. TTS engine is in offline mock mode.")
            self.speech_config = None
            self.synthesizer = None
            return

        self.voice_name = voice_name or settings.azure_speech_voice_name

        # 1. Configure Azure Speech Service connection
        self.speech_config = speechsdk.SpeechConfig(
            subscription=settings.azure_speech_key,
            region=settings.azure_speech_region,
        )
        self.speech_config.speech_synthesis_voice_name = self.voice_name

        # 2. Set telephony-compatible audio output format (16kHz 16-bit Mono PCM)
        self.speech_config.set_speech_synthesis_output_format(output_format)

        # 3. Instantiate Synthesizer with audio_config=None (memory synthesis, no local speakers)
        self.synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None,
        )

    def generate_ssml(
        self,
        text: str,
        rate: str = "0%",
        pitch: str = "0%",
        style: Optional[str] = None,
    ) -> str:
        """
        Wraps plain text in Speech Synthesis Markup Language (SSML)
        to govern prosody, pacing, and tone for clinical interactions.
        """
        if style:
            # Expressive neural styling (e.g. empathetic, cheerful)
            content = f'<mstts:express-as style="{style}">{text}</mstts:express-as>'
        else:
            content = text

        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
    xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
    <voice name="{self.voice_name}">
        <prosody rate="{rate}" pitch="{pitch}">
            {content}
        </prosody>
    </voice>
</speak>"""
        return ssml

    def synthesize_text(self, text: str) -> bytes:
        """
        Synthesizes plain text into complete audio bytes.
        Automatically selects native neural voices for Hindi (hi-IN-SwaraNeural)
        or Punjabi (pa-IN-VaaniNeural) if corresponding characters are present.

        :param text: The text string to speak.
        :return: Synthesized WAV audio bytes.
        """
        if not self.synthesizer:
            raise RuntimeError("SpeechSynthesizer is not initialized. Check AZURE_SPEECH_KEY.")

        start_time = time.perf_counter()

        # Dynamic Voice Selection based on script
        target_voice = self.voice_name
        target_lang = "en-IN"
        if any("\u0900" <= ch <= "\u097F" for ch in text):
            target_voice = "hi-IN-SwaraNeural"
            target_lang = "hi-IN"
        elif any("\u0A00" <= ch <= "\u0A7F" for ch in text):
            target_voice = "pa-IN-VaaniNeural"
            target_lang = "pa-IN"

        logger.info(f"Synthesizing text: '{text[:50]}...' using voice {target_voice} ({target_lang})")

        if target_voice != self.voice_name:
            escaped_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{target_lang}"><voice name="{target_voice}">{escaped_text}</voice></speak>'
            result = self.synthesizer.speak_ssml_async(ssml).get()
        else:
            result = self.synthesizer.speak_text_async(text).get()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_bytes = result.audio_data
            logger.info(
                f"TTS complete: {len(audio_bytes)} bytes generated in {elapsed_ms:.1f}ms"
            )
            return audio_bytes
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error(f"TTS synthesis canceled: {cancellation.reason}")
            if cancellation.reason == speechsdk.CancellationReason.Error:
                logger.error(f"TTS ErrorDetails: {cancellation.error_details}")
            raise RuntimeError(f"TTS synthesis failed: {cancellation.error_details}")

        return b""

    def synthesize_ssml(self, ssml: str) -> bytes:
        """
        Synthesizes formatted SSML markup into complete audio bytes.

        :param ssml: The SSML string to speak.
        :return: Synthesized WAV audio bytes.
        """
        if not self.synthesizer:
            raise RuntimeError("SpeechSynthesizer is not initialized. Check AZURE_SPEECH_KEY.")

        start_time = time.perf_counter()
        result = self.synthesizer.speak_ssml_async(ssml).get()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_bytes = result.audio_data
            logger.info(f"SSML TTS complete: {len(audio_bytes)} bytes in {elapsed_ms:.1f}ms")
            return audio_bytes
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation = result.cancellation_details
            logger.error(f"SSML TTS canceled: {cancellation.error_details}")
            raise RuntimeError(f"SSML TTS failed: {cancellation.error_details}")

        return b""

    def stream_text_chunks(self, text: str, chunk_size: int = 4096) -> Generator[bytes, None, None]:
        """
        Yields synthesized audio in sequential chunks for streaming over WebSockets.

        :param text: Text to synthesize.
        :param chunk_size: Number of bytes per yielded chunk (default: 4KB).
        """
        if not self.synthesizer:
            raise RuntimeError("SpeechSynthesizer is not initialized. Check AZURE_SPEECH_KEY.")

        result = self.synthesizer.speak_text_async(text).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            stream = speechsdk.AudioDataStream(result)
            buffer = bytes(chunk_size)
            filled_size = stream.read_data(buffer)
            while filled_size > 0:
                yield buffer[:filled_size]
                filled_size = stream.read_data(buffer)
        else:
            logger.error("TTS stream synthesis failed.")
