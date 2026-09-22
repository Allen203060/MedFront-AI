"""
FastAPI Router for Telephony Call Automation and Web Calling Interface.
Merges Module 1 (Telephony), Module 2 (Speech: STT & TTS), and Module 3 (Azure OpenAI Brain)
for an end-to-end full-duplex clinical voice receptionist with real-time barge-in.
"""
import asyncio
import base64
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.websockets import WebSocketState

from src.core.config import settings
from src.telephony.service import telephony_service, resolve_caller_identity_and_greeting
from src.speech.tts import TextToSpeechEngine
from src.speech.stt import SpeechToTextEngine
from src.brain.orchestrator import AgenticBrainOrchestrator
from src.brain.live_providers import LiveRAGProvider, LiveToolRegistry

logger = logging.getLogger("medfront.telephony.router")
router = APIRouter(prefix="/api/telephony", tags=["Telephony"])

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
STATIC_DIR = Path(__file__).resolve().parent / "static"

# In-memory storage for dynamically synthesized TTS audio buffers
audio_cache: Dict[str, bytes] = {}

# Active call state tracking for media control & barge-in
active_call_state: Dict[str, Any] = {
    "call_connection_id": None,
    "is_playing_audio": False,
    "last_played_text": "",
    "last_audio_start_time": 0.0,
    "last_playback_end_time": 0.0,
    "has_websocket_client": False,
}

# Initialize Neural TTS Engine
try:
    tts_engine: Optional[TextToSpeechEngine] = TextToSpeechEngine()
except Exception as e:
    logger.warning(f"Could not initialize TTS Engine: {e}")
    tts_engine = None


@router.get("/static/bundle.js", summary="Serve local Calling SDK bundle")
async def get_calling_bundle() -> Response:
    """Serves the locally bundled Azure Calling SDK."""
    bundle_path = STATIC_DIR / "bundle.js"
    if not bundle_path.exists():
        logger.error(f"Bundle not found at: {bundle_path}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, 
            content={"error": "Calling SDK bundle.js not found. Run esbuild first."}
        )
    return FileResponse(path=str(bundle_path), media_type="application/javascript")


@router.get("/token", summary="Generate ACS VoIP User Token for Web Caller")
async def get_web_caller_token() -> JSONResponse:
    """Returns an ACS user identity and VoIP token for browser calling."""
    try:
        data = telephony_service.create_web_caller_token()
        return JSONResponse(status_code=status.HTTP_200_OK, content=data)
    except Exception as e:
        logger.error(f"Failed to generate VoIP token: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )


@router.post("/call-browser", summary="Trigger Call Automation to call the browser")
async def call_browser_endpoint(request: Request) -> JSONResponse:
    """Tells Call Automation to initiate a WebRTC call to the active browser user."""
    try:
        body = await request.json()
        caller_user_id = body.get("caller_user_id")
        if not caller_user_id:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, 
                content={"error": "caller_user_id is required"}
            )

        if not settings.acs_callback_base_url:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "ACS_CALLBACK_BASE_URL is not configured in .env"},
            )

        base_url = settings.acs_callback_base_url.rstrip("/")
        callback_url = f"{base_url}/api/telephony/callbacks"

        call_connection_id = telephony_service.call_web_user(
            caller_user_id=caller_user_id,
            callback_url=callback_url,
        )

        active_call_state["call_connection_id"] = call_connection_id

        return JSONResponse(
            status_code=status.HTTP_200_OK, 
            content={"status": "calling", "call_connection_id": call_connection_id}
        )
    except Exception as e:
        logger.error(f"Failed to trigger browser call: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": str(e)},
        )


@router.get("/audio/dynamic/{audio_id}.wav", summary="Serve dynamic synthesized audio to ACS")
async def get_dynamic_audio(audio_id: str) -> Response:
    """Serves in-memory synthesized WAV audio to Azure Call Automation."""
    audio_bytes = audio_cache.get(audio_id)
    if not audio_bytes:
        return Response(status_code=status.HTTP_404_NOT_FOUND, content=b"Audio not found")
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/callbacks", summary="ACS Call Automation Lifecycle Events")
async def handle_call_callbacks(request: Request) -> Response:
    """Receives call state events (CallConnected, PlayCompleted, CallDisconnected)."""
    events: List[Dict[str, Any]] = await request.json()
    logger.info(f"ACS Call Callback received: {events}")

    if not settings.acs_callback_base_url:
        logger.error("ACS_CALLBACK_BASE_URL is not configured.")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    base_url = settings.acs_callback_base_url.rstrip("/")

    for event in events:
        event_type = event.get("type")
        data = event.get("data", {})
        call_connection_id = data.get("callConnectionId")

        logger.info(f"Event: {event_type} for CallConnectionId: {call_connection_id}")

        if event_type == "Microsoft.Communication.CallConnected":
            active_call_state["call_connection_id"] = call_connection_id
            logger.info(f"Call {call_connection_id} connected!")

            # Skip duplicate greeting if greeting was already started on WebSocket connect within last 5s
            if (time.time() - active_call_state.get("last_audio_start_time", 0.0)) < 5.0:
                logger.info("Greeting already streamed over WebSocket; skipping duplicate ACS Call Automation greeting.")
            else:
                caller_id = (
                    data.get("from", {}).get("phoneNumber", {}).get("value")
                    or data.get("callerId", {}).get("value")
                    or data.get("from", {}).get("rawId")
                )
                greeting_text, patient, next_appt = resolve_caller_identity_and_greeting(caller_id)
                active_call_state["last_played_text"] = greeting_text
                active_call_state["is_playing_audio"] = True
                active_call_state["last_audio_start_time"] = time.time()

                if tts_engine and settings.azure_speech_key:
                    audio_bytes = tts_engine.synthesize_text(greeting_text)
                    audio_id = f"greeting_{int(time.time())}"
                    audio_cache[audio_id] = audio_bytes
                    audio_url = f"{base_url}/api/telephony/audio/dynamic/{audio_id}.wav"
                else:
                    audio_url = "https://raw.githubusercontent.com/Azure-Samples/communication-services-python-quickstarts/main/CallAutomation_Play/hello.wav"

                await asyncio.sleep(1.0)
                telephony_service.play_audio(call_connection_id=call_connection_id, audio_url=audio_url)

        elif event_type == "Microsoft.Communication.PlayCompleted":
            active_call_state["is_playing_audio"] = False
            active_call_state["last_playback_end_time"] = time.time()
            logger.info(f"Playback completed on {call_connection_id}. Call remains open for caller speech.")

        elif event_type == "Microsoft.Communication.PlayFailed":
            active_call_state["is_playing_audio"] = False
            active_call_state["last_playback_end_time"] = time.time()
            result_info = data.get("resultInformation", {})
            logger.error(f"Audio playback FAILED on call {call_connection_id}. Reason: {result_info}")

        elif event_type == "Microsoft.Communication.CallDisconnected":
            active_call_state["call_connection_id"] = None
            active_call_state["is_playing_audio"] = False
            active_call_state["last_playback_end_time"] = time.time()
            logger.info(f"Call {call_connection_id} disconnected.")

    return Response(status_code=status.HTTP_200_OK)


@router.websocket("/ws/audio-stream")
@router.websocket("/ws/audio")
async def audio_stream_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint that receives raw 16kHz PCM audio from the browser,
    transcribes it using SpeechToTextEngine, processes it through AgenticBrainOrchestrator,
    and returns low-latency direct audio stream + triggers ACS Call Automation playback.
    Supports Caller ID auto-lookup via query params (?caller_id=... or ?phone=...).
    """
    await websocket.accept()
    logger.info("Browser audio WebSocket connected. Initializing Agentic Brain session...")
    active_call_state["has_websocket_client"] = True

    loop = asyncio.get_running_loop()
    brain_orchestrator = AgenticBrainOrchestrator(
        rag_provider=LiveRAGProvider(),
        tool_registry=LiveToolRegistry(),
    )

    ws_send_lock = asyncio.Lock()

    async def safe_send_json(payload: dict) -> None:
        """Thread-safe and async-safe serialized WebSocket sender."""
        try:
            async with ws_send_lock:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_json(payload)
        except Exception as ex:
            logger.debug(f"WebSocket safe send error: {ex}")

    # 1. Caller ID Auto-Lookup (Instant Zero-Friction Verification)
    caller_id = websocket.query_params.get("caller_id") or websocket.query_params.get("phone")
    greeting_text, patient, next_appt = resolve_caller_identity_and_greeting(caller_id)

    if patient:
        brain_orchestrator.memory.update_session(
            patient_id=patient.patient_id,
            verified_name=f"{patient.first_name} {patient.last_name}",
        )
        logger.info(f"[CALLER ID PRE-VERIFIED]: Linked session to Patient {patient.patient_id} ({patient.first_name} {patient.last_name})")

    # Record greeting in conversational memory
    brain_orchestrator.memory.add_assistant_message(greeting_text)

    active_call_state["playback_id"] = active_call_state.get("playback_id", 0) + 1
    current_pid = active_call_state["playback_id"]
    active_call_state["last_played_text"] = greeting_text
    active_call_state["is_playing_audio"] = True
    active_call_state["last_audio_start_time"] = time.time()

    async def _auto_clear_playback(delay_seconds: float, p_id: int) -> None:
        """Automatically resets the is_playing_audio state after the audio duration expires."""
        await asyncio.sleep(delay_seconds + 0.3)
        if active_call_state.get("playback_id") == p_id:
            active_call_state["is_playing_audio"] = False
            active_call_state["last_playback_end_time"] = time.time()
            logger.debug(f"[Audio Playback] Auto-cleared is_playing_audio for sequence #{p_id}")

    await safe_send_json({
        "type": "assistant",
        "text": greeting_text,
        "intent": "CASUAL_CONVERSATION",
        "rag_used": False,
        "tool_used": None,
        "recognized_patient": {
            "patient_id": patient.patient_id,
            "name": f"{patient.first_name} {patient.last_name}",
            "phone": patient.phone_number,
            "upcoming_doctor": next_appt.doctor_name if next_appt else None,
            "appointment_date": next_appt.appointment_date if next_appt else None,
            "appointment_time": next_appt.appointment_time if next_appt else None,
        } if patient else None,
    })

    if tts_engine and settings.azure_speech_key:
        try:
            greeting_audio = tts_engine.synthesize_text(greeting_text)
            b64_greeting = base64.b64encode(greeting_audio).decode("utf-8")
            await safe_send_json({"type": "audio", "data": b64_greeting})
            # Schedule auto-reset of playing flag after greeting audio length (16kHz 16-bit mono = 32000 bytes/sec)
            greeting_duration = max(1.0, len(greeting_audio) / 32000.0)
            asyncio.create_task(_auto_clear_playback(greeting_duration, current_pid))
        except Exception as e:
            logger.warning(f"Could not synthesize initial WebSocket greeting audio: {e}")
            active_call_state["is_playing_audio"] = False

    def on_interim(text: str) -> None:
        """Fires when interim speech is recognized (Instant Barge-in trigger)."""
        clean_text = text.strip()
        if not clean_text:
            return

        # 1. Instant Barge-In: interrupt playback immediately on first user speech detection
        active_call_state["is_playing_audio"] = False
        active_call_state["last_playback_end_time"] = time.time()
        logger.info(f"[BARGE-IN TRIGGERED] Caller interim speech: '{clean_text}'. Interrupting playback...")

        call_id = active_call_state.get("call_connection_id")
        if call_id and telephony_service.client:
            try:
                conn = telephony_service.client.get_call_connection(call_id)
                conn.cancel_all_media_operations()
            except Exception as e:
                logger.warning(f"Barge-in cancel error: {e}")

        # Signal browser to immediately halt active Web Audio playback
        asyncio.run_coroutine_threadsafe(
            safe_send_json({"type": "interrupt"}),
            loop,
        )

        # Push interim text back to browser UI
        asyncio.run_coroutine_threadsafe(
            safe_send_json({"type": "interim", "text": clean_text}),
            loop,
        )

    def _is_acoustic_speaker_echo(transcribed_text: str, last_played_text: str) -> bool:
        """Detects when laptop/phone speakers leak assistant audio back into the microphone."""
        if not last_played_text or not transcribed_text:
            return False
            
        # Echo can ONLY occur while the speaker is physically playing audio
        if not active_call_state.get("is_playing_audio"):
            last_end = active_call_state.get("last_playback_end_time", 0)
            if time.time() - last_end > 0.3:
                return False

        ai_words = set(w.lower() for w in re.findall(r'\b\w{3,}\b', last_played_text))
        user_words = [w.lower() for w in re.findall(r'\b\w{3,}\b', transcribed_text)]
        if not user_words or not ai_words:
            return False

        safe_words = {"hello", "hi", "hey", "yes", "no", "cardio", "cardiology", "doctor", "appointment", "book", "schedule", "tomorrow", "today", "help", "aura", "wait"}
        if any(w in safe_words for w in user_words):
            return False

        overlap_count = sum(1 for w in user_words if w in ai_words)
        overlap_ratio = overlap_count / len(user_words)
        if overlap_ratio >= 0.75 and len(user_words) >= 4:
            return True
        return False

    def on_final(text: str) -> None:
        """Fires when user pauses and sentence is finalized."""
        clean_text = text.strip()
        if not clean_text:
            return

        logger.info(f"[STT Finalized]: '{clean_text}'")

        # Guarantee audio playback is interrupted upon finalized speech
        active_call_state["is_playing_audio"] = False
        active_call_state["last_playback_end_time"] = time.time()
        asyncio.run_coroutine_threadsafe(
            safe_send_json({"type": "interrupt"}),
            loop,
        )

        # 1. Filter acoustic loopback feedback (only during active speaker output)
        last_spoken = active_call_state.get("last_played_text", "").strip()
        if _is_acoustic_speaker_echo(clean_text, last_spoken):
            logger.info(f"[ECHO SUPPRESSION]: Filtered acoustic speaker loopback: '{clean_text}'")
            return

        # 2. Push verified User transcript to browser UI
        asyncio.run_coroutine_threadsafe(
            safe_send_json({"type": "final", "event": "user", "text": clean_text}),
            loop,
        )

        # 3. Process turn through Agentic Brain (Azure OpenAI)
        start_brain = time.perf_counter()
        brain_output = brain_orchestrator.process_turn(clean_text)
        speech_reply = brain_output.speech_text
        intent_name = brain_output.intent_detected.value
        tool_status = brain_output.tool_used
        brain_duration = (time.perf_counter() - start_brain) * 1000.0

        logger.info(f"[Brain Output in {brain_duration:.0f}ms]: '{speech_reply}' | Intent={intent_name}")

        # 4. Push Assistant Text & Badges to Browser UI
        asyncio.run_coroutine_threadsafe(
            safe_send_json({
                "type": "assistant",
                "text": speech_reply,
                "intent": intent_name,
                "rag_used": brain_output.rag_used,
                "tool_used": tool_status,
            }),
            loop,
        )

        # 5. Synthesize Neural TTS (Azure AI Speech)
        if tts_engine and settings.azure_speech_key:
            try:
                active_call_state["playback_id"] = active_call_state.get("playback_id", 0) + 1
                turn_pid = active_call_state["playback_id"]
                active_call_state["last_played_text"] = speech_reply
                active_call_state["is_playing_audio"] = True
                active_call_state["last_audio_start_time"] = time.time()

                tts_start = time.perf_counter()
                audio_bytes = tts_engine.synthesize_text(speech_reply)
                tts_duration = (time.perf_counter() - tts_start) * 1000.0
                logger.info(f"[TTS Synthesized in {tts_duration:.0f}ms]: {len(audio_bytes)} bytes")

                # Send DIRECT audio to browser over WebSocket (Zero-latency instant playback)
                b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                asyncio.run_coroutine_threadsafe(
                    safe_send_json({"type": "audio", "data": b64_audio}),
                    loop,
                )

                # Schedule auto-reset of playing flag after audio playback finishes
                reply_duration = max(1.0, len(audio_bytes) / 32000.0)
                asyncio.run_coroutine_threadsafe(_auto_clear_playback(reply_duration, turn_pid), loop)

                # Only trigger ACS play_audio for external telephony calls (when no direct WebSocket exists)
                call_id = active_call_state.get("call_connection_id")
                if call_id and settings.acs_callback_base_url and not active_call_state.get("has_websocket_client"):
                    audio_id = f"reply_{int(time.time())}"
                    audio_cache[audio_id] = audio_bytes
                    base_url = settings.acs_callback_base_url.rstrip("/")
                    audio_url = f"{base_url}/api/telephony/audio/dynamic/{audio_id}.wav"
                    telephony_service.play_audio(call_connection_id=call_id, audio_url=audio_url)

            except Exception as e:
                logger.error(f"Failed to play brain response: {e}")
                active_call_state["is_playing_audio"] = False

    # Initialize continuous STT engine with calibrated 450ms silence timeout for low-latency conversational cadence
    stt_engine = SpeechToTextEngine(
        on_interim_result=on_interim,
        on_final_result=on_final,
        end_silence_timeout_ms=450,
    )
    stt_engine.start_recognition()

    chunk_counter = 0
    total_audio_bytes = 0
    try:
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                logger.info("Browser audio WebSocket received disconnect signal.")
                break
            if "bytes" in message and message["bytes"]:
                chunk_counter += 1
                total_audio_bytes += len(message["bytes"])
                if chunk_counter == 1 or chunk_counter % 100 == 0:
                    logger.info(f"[WS Audio Stream] Received audio chunk #{chunk_counter} ({total_audio_bytes} total bytes) -> writing to STT PushStream")
                stt_engine.write_audio_chunk(message["bytes"])
            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type") or data.get("event")
                    if msg_type in ["client_barge_in", "interrupt"]:
                        logger.info("[Client Barge-in Signal]: Instant speaker cutoff received from browser.")
                        active_call_state["is_playing_audio"] = False
                        active_call_state["last_playback_end_time"] = time.time()
                        call_id = active_call_state.get("call_connection_id")
                        if call_id and telephony_service.client:
                            try:
                                conn = telephony_service.client.get_call_connection(call_id)
                                conn.cancel_all_media_operations()
                            except Exception:
                                pass
                    elif msg_type == "playback_start":
                        active_call_state["is_playing_audio"] = True
                    elif msg_type == "playback_end":
                        active_call_state["is_playing_audio"] = False
                        active_call_state["last_playback_end_time"] = time.time()
                    elif msg_type == "caller_handshake":
                        c_id = data.get("caller_id") or data.get("phone")
                        if c_id:
                            g_text, pat, n_appt = resolve_caller_identity_and_greeting(c_id)
                            if pat:
                                brain_orchestrator.memory.update_session(
                                    patient_id=pat.patient_id,
                                    verified_name=f"{pat.first_name} {pat.last_name}"
                                )
                    elif msg_type in ["simulated_speech", "text_input", "prompt"] and data.get("text"):
                        prompt_text = data.get("text")
                        logger.info(f"[WS Text Input]: Processing spoken prompt: '{prompt_text}'")
                        on_final(prompt_text)
                except Exception as ex:
                    logger.warning(f"Error handling WS text message: {ex}")
    except WebSocketDisconnect:
        logger.info("Browser audio WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error in audio stream: {e}")
    finally:
        active_call_state["has_websocket_client"] = False
        stt_engine.close_stream()
        stt_engine.stop_recognition()


@router.get("/web-caller", response_class=HTMLResponse, summary="Browser VoIP Web Calling Test Page")
async def get_web_caller_page() -> str:
    """Interactive WebRTC browser calling test client with real-time agentic transcript and theme synchronization."""
    return """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aura Voice AI Studio | MedFrontcare</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script defer src="/api/telephony/static/bundle.js"></script>
    <style>
        :root {
            --bg-base: #f8fafc;
            --bg-surface: #ffffff;
            --bg-card: #ffffff;
            --bg-card-subtle: #f1f5f9;
            --border-subtle: #e2e8f0;
            --border-strong: #cbd5e1;
            --border-glow: rgba(13, 148, 136, 0.35);
            --text-main: #0f172a;
            --text-muted: #64748b;
            --teal-500: #0d9488;
            --teal-600: #0f766e;
            --teal-50: #f0fdfa;
            --teal-100: #ccfbf1;
            --shadow-elevated: 0 12px 32px -4px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04);
            --bubble-user-bg: #f0fdfa;
            --bubble-user-border: #0d9488;
            --bubble-user-text: #0f766e;
            --bubble-agent-bg: #ffffff;
            --bubble-agent-border: #e2e8f0;
            --bubble-agent-text: #1e293b;
        }

        [data-theme="dark"] {
            --bg-base: #090d16;
            --bg-surface: #0f172a;
            --bg-card: #131d31;
            --bg-card-subtle: #1a263d;
            --border-subtle: #1e293b;
            --border-strong: #334155;
            --border-glow: rgba(20, 184, 166, 0.45);
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --teal-500: #14b8a6;
            --teal-600: #0d9488;
            --teal-50: rgba(13, 148, 136, 0.15);
            --teal-100: rgba(13, 148, 136, 0.25);
            --shadow-elevated: 0 16px 40px rgba(0, 0, 0, 0.6);
            --bubble-user-bg: #132738;
            --bubble-user-border: #0284c7;
            --bubble-user-text: #38bdf8;
            --bubble-agent-bg: #16243b;
            --bubble-agent-border: #243552;
            --bubble-agent-text: #e2e8f0;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-base);
            color: var(--text-main);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1.5rem 1rem;
            transition: background 0.3s ease, color 0.3s ease;
        }

        .studio-card {
            background: var(--bg-card);
            border: 1px solid var(--border-subtle);
            border-radius: 20px;
            box-shadow: var(--shadow-elevated);
            width: 580px;
            max-width: 100%;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            transition: all 0.3s ease;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-subtle);
            padding-bottom: 1rem;
        }

        .brand-title {
            font-family: 'Outfit', sans-serif;
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .btn-theme-toggle {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-strong);
            color: var(--text-main);
            border-radius: 9999px;
            padding: 0.35rem 0.85rem;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: all 0.2s;
        }
        .btn-theme-toggle:hover {
            border-color: var(--teal-500);
        }

        .mic-box {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }
        .mic-box label {
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
        }
        select {
            width: 100%;
            padding: 0.65rem 0.85rem;
            background: var(--bg-surface);
            border: 1px solid var(--border-strong);
            color: var(--text-main);
            border-radius: 10px;
            font-size: 0.85rem;
            outline: none;
            font-family: inherit;
        }
        select:focus { border-color: var(--teal-500); }

        .call-status-bar {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            text-align: center;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            word-break: break-word;
        }

        .waveform-container {
            background: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: 12px;
            padding: 0.6rem;
            text-align: center;
        }
        canvas { width: 100%; height: 50px; }

        .console-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
        }

        .badge-live {
            background: #ef4444;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 700;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

        .transcript-box {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 14px;
            height: 240px;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            scroll-behavior: smooth;
        }

        .bubble-msg {
            padding: 0.75rem 1rem;
            border-radius: 12px;
            font-size: 0.88rem;
            line-height: 1.45;
            max-width: 90%;
            word-break: break-word;
            animation: fadeIn 0.25s ease forwards;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

        .bubble-user {
            background: var(--bubble-user-bg);
            border: 1px solid var(--bubble-user-border);
            color: var(--bubble-user-text);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }

        .bubble-assistant {
            background: var(--bubble-agent-bg);
            border: 1px solid var(--bubble-agent-border);
            color: var(--bubble-agent-text);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }

        .bubble-interim {
            background: rgba(148, 163, 184, 0.15);
            border: 1px dashed var(--border-strong);
            color: var(--text-muted);
            align-self: flex-end;
            font-style: italic;
        }

        .tag-pill {
            display: inline-block;
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 6px;
            background: var(--teal-50);
            color: var(--teal-600);
            font-weight: 700;
            border: 1px solid rgba(13, 148, 136, 0.2);
            margin-left: 4px;
        }
        .tag-tool {
            background: #ede9fe;
            color: #7c3aed;
            border-color: rgba(124, 58, 237, 0.2);
        }

        button.btn-primary {
            background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.9rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35);
            transition: all 0.2s;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            width: 100%;
            font-family: inherit;
        }
        button.btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(13, 148, 136, 0.45);
        }

        button.btn-danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.9rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            display: none;
            width: 100%;
            font-family: inherit;
        }

        .quick-prompts-bar {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }
        .quick-prompts-bar span {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            color: var(--text-muted);
        }
        .chip-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.4rem;
        }
        .prompt-chip {
            background: var(--bg-card-subtle);
            border: 1px solid var(--border-subtle);
            border-radius: 8px;
            padding: 0.45rem 0.6rem;
            font-size: 0.75rem;
            color: var(--text-main);
            text-align: left;
            cursor: pointer;
            transition: all 0.15s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-family: inherit;
        }
        .prompt-chip:hover {
            border-color: var(--teal-500);
            background: var(--teal-50);
            color: var(--teal-600);
        }

        .link-dashboard {
            display: block;
            text-align: center;
            font-size: 0.85rem;
            color: var(--teal-600);
            text-decoration: none;
            padding: 0.65rem;
            border: 1px solid var(--border-subtle);
            border-radius: 10px;
            background: var(--bg-card-subtle);
            font-weight: 600;
            transition: all 0.2s;
        }
        .link-dashboard:hover {
            border-color: var(--teal-500);
            background: var(--teal-50);
        }
    </style>
</head>
<body>
    <div class="studio-card">
        <div class="card-header">
            <div>
                <div class="brand-title">
                    <span>🎙️ Aura Voice Receptionist</span>
                    <span class="tag-pill" style="font-size: 0.68rem;">TRILINGUAL AI</span>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">
                    Full-duplex Azure Speech STT &rarr; GPT-4o Intent &rarr; Neural TTS
                </div>
            </div>
            <button id="themeToggleBtn" class="btn-theme-toggle" onclick="toggleTheme()">
                🌙 Dark Mode
            </button>
        </div>

        <div class="mic-box">
            <label for="micSelect">🎤 Select Microphone Hardware:</label>
            <select id="micSelect"></select>
        </div>

        <div id="status" class="call-status-bar">
            Click "Start Voice Call (Instant)" to begin speaking with Aura
        </div>

        <!-- Waveform Visualizer -->
        <div class="waveform-container">
            <canvas id="waveformCanvas" width="500" height="50"></canvas>
            <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 2px;">Microphone Voice Frequency Spectrum</div>
        </div>

        <div class="console-header">
            <span>Agentic Conversation Stream</span>
            <span id="liveIndicator" style="display:none;" class="badge-live">MIC ACTIVE</span>
        </div>

        <div id="transcriptBox" class="transcript-box">
            <div style="color: var(--text-muted); font-style: italic; text-align: center; margin-top: 4.5rem;">
                Spoken conversation turns and live transcripts will appear here in real time...
            </div>
        </div>

        <div class="quick-prompts-bar">
            <span>Quick Test Prompts (Spoken Simulators):</span>
            <div class="chip-grid">
                <button class="prompt-chip" onclick="simulateSpokenPrompt('What are Dr. Ananya Rao open slots for cardiology tomorrow?')">
                    💬 "Dr. Ananya cardiology slots tomorrow?"
                </button>
                <button class="prompt-chip" onclick="simulateSpokenPrompt('I am visiting for the first time, my name is Rahul Mehta, book me with Dr. Rajesh tomorrow at 10 AM')">
                    💬 "Book as first-time new patient"
                </button>
                <button class="prompt-chip" onclick="simulateSpokenPrompt('नमस्ते, क्या मुझे कल डॉक्टर सुनीता कपूर के लिए अपॉइंटमेंट मिल सकता है?')">
                    💬 "नमस्ते, डॉक्टर से मिलना है (Hindi)"
                </button>
                <button class="prompt-chip" onclick="simulateSpokenPrompt('Can I book an appointment with Dr. Vikram Sen?')">
                    💬 "Switch back to English booking"
                </button>
            </div>
        </div>

        <button id="directCallBtn" class="btn-primary" onclick="startDirectVoiceCall()">
            <span>🎙️ Start Voice Call (Instant)</span>
        </button>
        <button id="hangupBtn" class="btn-danger" onclick="hangUp()">
            <span>🔴 End Voice Call</span>
        </button>

        <a href="/dashboard" class="link-dashboard">
            🏥 Return to Hospital Administrative Dashboard
        </a>
    </div>

    <script>
        // Theme synchronization with main dashboard
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('auracare_theme', theme);
            const btn = document.getElementById('themeToggleBtn');
            if (btn) {
                btn.innerHTML = theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
            }
        }
        function toggleTheme() {
            const cur = document.documentElement.getAttribute('data-theme') || 'light';
            applyTheme(cur === 'dark' ? 'light' : 'dark');
        }
        const savedTheme = localStorage.getItem('auracare_theme') || 'light';
        applyTheme(savedTheme);

        let audioWs = null;
        let audioContext = null;
        let micStream = null;
        let processorNode = null;
        let analyserNode = null;
        let isCallActive = false;

        const log = (msg) => {
            const el = document.getElementById('status');
            if (el) el.innerText = msg;
        };

        async function populateMicrophones() {
            try {
                if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(track => track.stop());

                const devices = await navigator.mediaDevices.enumerateDevices();
                const audioInputs = devices.filter(d => d.kind === 'audioinput');
                const select = document.getElementById('micSelect');
                select.innerHTML = '';
                audioInputs.forEach((dev, idx) => {
                    const opt = document.createElement('option');
                    opt.value = dev.deviceId;
                    opt.text = dev.label || `Microphone ${idx + 1}`;
                    if (!dev.label.toLowerCase().includes('monitor') && !dev.label.toLowerCase().includes('mix')) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            } catch (e) {
                console.warn("Could not list audio devices:", e);
            }
        }
        populateMicrophones();

        function downsampleTo16k(buffer, inputSampleRate) {
            if (inputSampleRate === 16000) return buffer;
            const ratio = inputSampleRate / 16000;
            const newLength = Math.round(buffer.length / ratio);
            const result = new Float32Array(newLength);
            let offsetResult = 0;
            let offsetBuffer = 0;
            while (offsetResult < result.length) {
                const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
                let accum = 0, count = 0;
                for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
                    accum += buffer[i];
                    count++;
                }
                result[offsetResult] = count > 0 ? accum / count : buffer[offsetBuffer];
                offsetResult++;
                offsetBuffer = nextOffsetBuffer;
            }
            return result;
        }

        async function startDirectVoiceCall() {
            try {
                log("Connecting directly to Voice Receptionist pipeline...");
                const directBtn = document.getElementById('directCallBtn');
                directBtn.disabled = true;

                if (!audioContext) {
                    const AudioCtx = window.AudioContext || window.webkitAudioContext;
                    try {
                        audioContext = new AudioCtx({ sampleRate: 16000 });
                    } catch (e) {
                        audioContext = new AudioCtx();
                    }
                }
                if (audioContext.state === 'suspended') {
                    await audioContext.resume();
                }

                await startMicStreaming();
                directBtn.style.display = 'none';
                document.getElementById('hangupBtn').style.display = 'block';
                log("🟢 Call Active! Speak naturally in English, Hindi, or Punjabi.");
                isCallActive = true;
            } catch (err) {
                console.error("Direct call error:", err);
                log("Call Error: " + err.message);
                const directBtn = document.getElementById('directCallBtn');
                if (directBtn) {
                    directBtn.disabled = false;
                    directBtn.style.display = 'block';
                }
                document.getElementById('hangupBtn').style.display = 'none';
            }
        }

        async function startMicStreaming() {
            try {
                let stream = null;
                const selectEl = document.getElementById('micSelect');
                const selectedDeviceId = selectEl ? selectEl.value : null;

                const audioConstraints = {
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                };
                if (selectedDeviceId && selectedDeviceId !== 'default' && selectedDeviceId !== '') {
                    audioConstraints.deviceId = { ideal: selectedDeviceId };
                }
                stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
                micStream = stream;

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/api/telephony/ws/audio-stream`;
                audioWs = new WebSocket(wsUrl);

                audioWs.onopen = () => {
                    const liveIndicator = document.getElementById('liveIndicator');
                    if (liveIndicator) liveIndicator.style.display = 'inline-block';
                    setupWaveformVisualizer(stream);
                };

                audioWs.onerror = (err) => {
                    console.error("[WS] Voice stream error:", err);
                    log("⚠️ Voice stream connection error.");
                };

                audioWs.onclose = () => {
                    hangUp();
                };

                audioWs.onmessage = (event) => {
                    const msg = JSON.parse(event.data);
                    handleSpeechEvent(msg);
                };

                const actualRate = audioContext.sampleRate;
                const source = audioContext.createMediaStreamSource(micStream);
                processorNode = audioContext.createScriptProcessor(4096, 1, 1);

                const liveIndicator = document.getElementById('liveIndicator');
                processorNode.onaudioprocess = (e) => {
                    if (!audioWs || audioWs.readyState !== WebSocket.OPEN) return;
                    const rawFloatData = e.inputBuffer.getChannelData(0);

                    // Voice energy detector
                    let sumSquares = 0;
                    for (let i = 0; i < rawFloatData.length; i++) {
                        sumSquares += rawFloatData[i] * rawFloatData[i];
                    }
                    const rms = Math.sqrt(sumSquares / rawFloatData.length);
                    if (liveIndicator) {
                        if (rms > 0.015) {
                            liveIndicator.innerText = "TALKING 🗣️";
                            liveIndicator.style.background = "#10b981";
                        } else {
                            liveIndicator.innerText = "MIC ACTIVE";
                            liveIndicator.style.background = "#ef4444";
                        }
                    }

                    const downsampled = downsampleTo16k(rawFloatData, actualRate);
                    const pcmData = new Int16Array(downsampled.length);
                    for (let i = 0; i < downsampled.length; i++) {
                        const s = Math.max(-1, Math.min(1, downsampled[i]));
                        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }
                    audioWs.send(pcmData.buffer);
                };

                source.connect(processorNode);
                // Safe mute node to prevent mic loopback into user speakers
                const muteGain = audioContext.createGain();
                muteGain.gain.value = 0;
                processorNode.connect(muteGain);
                muteGain.connect(audioContext.destination);

            } catch (err) {
                console.error("Failed to start mic stream:", err);
                log("Microphone access error: " + err.message);
                throw err;
            }
        }

        function setupWaveformVisualizer(stream) {
            try {
                if (!audioContext) return;
                analyserNode = audioContext.createAnalyser();
                analyserNode.fftSize = 64;
                const source = audioContext.createMediaStreamSource(stream);
                source.connect(analyserNode);

                const canvas = document.getElementById('waveformCanvas');
                const ctx = canvas.getContext('2d');
                const dataArray = new Uint8Array(analyserNode.frequencyBinCount);

                function draw() {
                    if (!isCallActive) {
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        return;
                    }
                    requestAnimationFrame(draw);
                    analyserNode.getByteFrequencyData(dataArray);
                    ctx.clearRect(0, 0, canvas.width, canvas.height);

                    const barWidth = (canvas.width / dataArray.length) * 2.2;
                    let x = 0;
                    for (let i = 0; i < dataArray.length; i++) {
                        const barHeight = (dataArray[i] / 255) * canvas.height;
                        ctx.fillStyle = '#0d9488';
                        ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);
                        x += barWidth;
                    }
                }
                draw();
            } catch(e) {}
        }

        let currentSourceNode = null;
        function stopAiPlayback() {
            if (currentSourceNode) {
                try {
                    currentSourceNode.stop();
                    currentSourceNode.disconnect();
                } catch (e) {}
                currentSourceNode = null;
            }
        }

        async function playAudioBuffer(base64Data) {
            try {
                stopAiPlayback();
                if (!audioContext) {
                    const AudioCtx = window.AudioContext || window.webkitAudioContext;
                    audioContext = new AudioCtx();
                }
                if (audioContext.state === 'suspended') {
                    await audioContext.resume();
                }

                if (audioWs && audioWs.readyState === WebSocket.OPEN) {
                    try { audioWs.send(JSON.stringify({ type: "playback_start" })); } catch(e) {}
                }

                const binaryString = window.atob(base64Data);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                const audioBuffer = await audioContext.decodeAudioData(bytes.buffer.slice(0));
                const sourceNode = audioContext.createBufferSource();
                sourceNode.buffer = audioBuffer;
                sourceNode.connect(audioContext.destination);
                currentSourceNode = sourceNode;

                sourceNode.onended = () => {
                    if (currentSourceNode === sourceNode) {
                        currentSourceNode = null;
                        setTimeout(() => {
                            if (audioWs && audioWs.readyState === WebSocket.OPEN) {
                                try { audioWs.send(JSON.stringify({ type: "playback_end" })); } catch(e) {}
                            }
                        }, 100);
                    }
                };
                sourceNode.start(0);
            } catch (err) {
                console.warn("Audio playback warning:", err);
            }
        }

        function handleSpeechEvent(msg) {
            const box = document.getElementById('transcriptBox');
            let interimEl = document.getElementById('interimText');

            if (msg.type === 'interrupt') {
                stopAiPlayback();
                return;
            }

            if (msg.type === 'audio') {
                playAudioBuffer(msg.data);
                return;
            }

            // Real-time user speech interim display
            if (msg.type === 'interim') {
                stopAiPlayback();
                if (!interimEl) {
                    interimEl = document.createElement('div');
                    interimEl.id = 'interimText';
                    interimEl.className = 'bubble-msg bubble-interim';
                    box.appendChild(interimEl);
                }
                interimEl.innerText = "🗣️ You: " + msg.text + "...";
                box.scrollTop = box.scrollHeight;
                return;
            }

            // Finalized user speech turn
            if (msg.type === 'final' || msg.type === 'user' || msg.event === 'user') {
                stopAiPlayback();
                if (interimEl) interimEl.remove();

                const finalEl = document.createElement('div');
                finalEl.className = 'bubble-msg bubble-user';
                finalEl.innerHTML = `<strong>You:</strong> ${msg.text}`;
                box.appendChild(finalEl);
                box.scrollTop = box.scrollHeight;
                return;
            }

            // Assistant response turn
            if (msg.type === 'assistant') {
                const assistantEl = document.createElement('div');
                assistantEl.className = 'bubble-msg bubble-assistant';

                let tags = `<span class="tag-pill">${msg.intent || 'CONVERSATION'}</span>`;
                if (msg.tool_used) {
                    tags += ` <span class="tag-pill tag-tool">⚙️ ${msg.tool_used}</span>`;
                }

                assistantEl.innerHTML = `<div><strong>Aura:</strong> ${tags}</div><div style="margin-top:5px;">${msg.text}</div>`;
                box.appendChild(assistantEl);
                box.scrollTop = box.scrollHeight;
            }
        }

        function simulateSpokenPrompt(text) {
            if (!isCallActive) {
                alert("Please click 'Start Voice Call (Instant)' first to activate the live audio session.");
                return;
            }
            if (audioWs && audioWs.readyState === WebSocket.OPEN) {
                audioWs.send(JSON.stringify({ event: "simulated_speech", text: text }));
            }
        }

        function hangUp() {
            isCallActive = false;
            stopAiPlayback();

            const liveIndicator = document.getElementById('liveIndicator');
            if (liveIndicator) liveIndicator.style.display = 'none';

            if (processorNode) {
                try { processorNode.disconnect(); } catch(e) {}
                processorNode = null;
            }
            if (audioContext) {
                try { audioContext.close(); } catch(e) {}
                audioContext = null;
            }
            if (micStream) {
                try { micStream.getTracks().forEach(t => t.stop()); } catch(e) {}
                micStream = null;
            }
            if (audioWs) {
                try { audioWs.close(); } catch(e) {}
                audioWs = null;
            }

            const hangupBtn = document.getElementById('hangupBtn');
            if (hangupBtn) hangupBtn.style.display = 'none';

            const directBtn = document.getElementById('directCallBtn');
            if (directBtn) {
                directBtn.style.display = 'flex';
                directBtn.disabled = false;
            }

            log("Call ended. Click 'Start Voice Call (Instant)' to speak again.");
        }
    </script>
</body>
</html>
    """
