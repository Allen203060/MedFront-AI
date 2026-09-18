"""
FastAPI Router for Telephony Call Automation and Web Calling Interface.
Merges Module 1 (Telephony), Module 2 (Speech: STT & TTS), and Module 3 (Azure OpenAI Brain)
for an end-to-end full-duplex clinical voice receptionist with real-time barge-in.
"""
import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from src.core.config import settings
from src.telephony.service import telephony_service
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
async def get_calling_bundle() -> FileResponse:
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
                greeting_text = (
                    "Hello! Thank you for calling MedFront Health Clinic. "
                    "My name is Aura. How may I assist you today?"
                )
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
async def audio_stream_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint that receives raw 16kHz PCM audio from the browser,
    transcribes it using SpeechToTextEngine, processes it through AgenticBrainOrchestrator,
    and returns low-latency direct audio stream + triggers ACS Call Automation playback.
    """
    await websocket.accept()
    logger.info("Browser audio WebSocket connected. Initializing Agentic Brain session...")
    active_call_state["has_websocket_client"] = True

    loop = asyncio.get_running_loop()
    brain_orchestrator = AgenticBrainOrchestrator(
        rag_provider=LiveRAGProvider(),
        tool_registry=LiveToolRegistry(),
    )

    # Send opening greeting immediately over WebSocket so caller hears Aura with zero cloud delay
    greeting_text = (
        "Hello! Thank you for calling MedFront Health Clinic. "
        "My name is Aura. How may I assist you today?"
    )
    active_call_state["last_played_text"] = greeting_text
    active_call_state["is_playing_audio"] = True
    active_call_state["last_audio_start_time"] = time.time()

    async def _auto_clear_playback(delay_seconds: float) -> None:
        """Automatically resets the is_playing_audio state after the audio duration expires."""
        await asyncio.sleep(delay_seconds + 0.3)
        active_call_state["is_playing_audio"] = False
        active_call_state["last_playback_end_time"] = time.time()
        logger.debug("[Audio Playback] Auto-cleared is_playing_audio to False")

    await websocket.send_json({
        "type": "assistant",
        "text": greeting_text,
        "intent": "CASUAL_CONVERSATION",
        "rag_used": False,
        "tool_used": None,
    })

    if tts_engine and settings.azure_speech_key:
        try:
            greeting_audio = tts_engine.synthesize_text(greeting_text)
            b64_greeting = base64.b64encode(greeting_audio).decode("utf-8")
            await websocket.send_json({"type": "audio", "data": b64_greeting})
            # Schedule auto-reset of playing flag after greeting audio length (16kHz 16-bit mono = 32000 bytes/sec)
            greeting_duration = max(1.0, len(greeting_audio) / 32000.0)
            asyncio.create_task(_auto_clear_playback(greeting_duration))
        except Exception as e:
            logger.warning(f"Could not synthesize initial WebSocket greeting audio: {e}")
            active_call_state["is_playing_audio"] = False

    def on_interim(text: str) -> None:
        """Fires when interim speech is recognized (Barge-in trigger)."""
        clean_text = text.strip()
        words = [w for w in re.findall(r'\b\w+\b', clean_text) if len(w) >= 2]
        if not words:
            return

        # 1. Barge-In: If AI is actively playing and user speaks, cancel playback immediately!
        if active_call_state.get("is_playing_audio"):
            call_id = active_call_state.get("call_connection_id")
            logger.info(f"[BARGE-IN TRIGGERED] Caller spoke word '{clean_text}'. Interrupting playback...")
            active_call_state["is_playing_audio"] = False
            active_call_state["last_playback_end_time"] = time.time()

            # Signal browser to immediately halt active Web Audio playback
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "interrupt"}),
                loop,
            )

            if call_id and telephony_service.client:
                try:
                    conn = telephony_service.client.get_call_connection(call_id)
                    conn.cancel_all_media_operations()
                except Exception as e:
                    logger.warning(f"Barge-in cancel error: {e}")

        # 2. Push interim text back to browser UI
        asyncio.run_coroutine_threadsafe(
            websocket.send_json({"type": "interim", "text": clean_text}),
            loop,
        )

    def _is_acoustic_speaker_echo(transcribed_text: str, last_played_text: str) -> bool:
        """Detects when laptop/phone speakers leak assistant audio back into the microphone."""
        if not last_played_text or not transcribed_text:
            return False
            
        # 1. Physical constraint: Echo can ONLY occur while the speaker is physically playing audio!
        # If AI is not actively playing audio right now (or has stopped >0.3s ago), it is 100% genuine user speech.
        if not active_call_state.get("is_playing_audio"):
            last_end = active_call_state.get("last_playback_end_time", 0)
            if time.time() - last_end > 0.3:
                return False

        ai_words = set(w.lower() for w in re.findall(r'\b\w{3,}\b', last_played_text))
        user_words = [w.lower() for w in re.findall(r'\b\w{3,}\b', transcribed_text)]
        if not user_words or not ai_words:
            return False

        # Common user greetings, affirmations, and scheduling terms must NEVER be filtered as echo
        safe_words = {"hello", "hi", "hey", "yes", "no", "cardio", "cardiology", "doctor", "appointment", "book", "schedule", "tomorrow", "today", "help", "aura"}
        if any(w in safe_words for w in user_words):
            return False

        # Only drop if the transcribed text is a near-exact verbatim echo (>75% overlap) and has at least 4 words
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

        # 1. Filter acoustic loopback feedback (only during active speaker output)
        last_spoken = active_call_state.get("last_played_text", "").strip()
        if _is_acoustic_speaker_echo(clean_text, last_spoken):
            logger.info(f"[ECHO SUPPRESSION]: Filtered acoustic speaker loopback: '{clean_text}'")
            return

        # 2. If AI was still playing, genuine caller barge-in! Interrupt audio and process turn.
        if active_call_state.get("is_playing_audio"):
            logger.info(f"[BARGE-IN FINALIZED] User completed turn during playback: '{clean_text}'")
            active_call_state["is_playing_audio"] = False
            active_call_state["last_playback_end_time"] = time.time()
            asyncio.run_coroutine_threadsafe(
                websocket.send_json({"type": "interrupt"}),
                loop,
            )

        # 3. Push verified User transcript to browser UI
        asyncio.run_coroutine_threadsafe(
            websocket.send_json({"type": "final", "text": clean_text}),
            loop,
        )

        # 4. Process turn through Agentic Brain (Azure OpenAI)
        start_brain = time.perf_counter()
        brain_output = brain_orchestrator.process_turn(clean_text)
        speech_reply = brain_output.speech_text
        intent_name = brain_output.intent_detected.value
        tool_status = brain_output.tool_used
        brain_duration = (time.perf_counter() - start_brain) * 1000.0

        logger.info(f"[Brain Output in {brain_duration:.0f}ms]: '{speech_reply}' | Intent={intent_name}")

        # 5. Push Assistant Text & Badges to Browser UI
        asyncio.run_coroutine_threadsafe(
            websocket.send_json({
                "type": "assistant",
                "text": speech_reply,
                "intent": intent_name,
                "rag_used": brain_output.rag_used,
                "tool_used": tool_status,
            }),
            loop,
        )

        # 6. Synthesize Neural TTS (Azure AI Speech)
        if tts_engine and settings.azure_speech_key:
            try:
                active_call_state["last_played_text"] = speech_reply
                active_call_state["is_playing_audio"] = True
                active_call_state["last_audio_start_time"] = time.time()

                tts_start = time.perf_counter()
                audio_bytes = tts_engine.synthesize_text(speech_reply)
                tts_duration = (time.perf_counter() - tts_start) * 1000.0
                logger.info(f"[TTS Synthesized in {tts_duration:.0f}ms]: {len(audio_bytes)} bytes")

                # Schedule auto-reset of playing flag after audio playback finishes
                reply_duration = max(1.0, len(audio_bytes) / 32000.0)
                asyncio.create_task(_auto_clear_playback(reply_duration))

                # A. Send DIRECT audio to browser over WebSocket (Zero-latency instant playback)
                b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "audio", "data": b64_audio}),
                    loop,
                )

                # B. Only trigger ACS play_audio for external telephony calls (when no direct WebSocket exists)
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

    # Initialize continuous STT engine with calibrated 700ms silence timeout (was 1200ms)
    stt_engine = SpeechToTextEngine(
        on_interim_result=on_interim,
        on_final_result=on_final,
        end_silence_timeout_ms=700,
    )
    stt_engine.start_recognition()

    chunk_counter = 0
    total_audio_bytes = 0
    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                chunk_counter += 1
                total_audio_bytes += len(message["bytes"])
                if chunk_counter == 1 or chunk_counter % 100 == 0:
                    logger.info(f"[WS Audio Stream] Received audio chunk #{chunk_counter} ({total_audio_bytes} total bytes) -> writing to STT PushStream")
                stt_engine.write_audio_chunk(message["bytes"])
            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")
                    if msg_type == "playback_start":
                        active_call_state["is_playing_audio"] = True
                    elif msg_type == "playback_end":
                        active_call_state["is_playing_audio"] = False
                        active_call_state["last_playback_end_time"] = time.time()
                except Exception:
                    pass
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
    """Interactive WebRTC browser calling test client with real-time agentic transcript."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MedFront AI Voice Receptionist (Aura)</title>
        <script defer src="/api/telephony/static/bundle.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 1rem; box-sizing: border-box; }
            .card { background: #1e293b; padding: 2rem; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 520px; max-width: 100%; border: 1px solid #334155; }
            h2 { margin-top: 0; color: #38bdf8; font-size: 1.5rem; text-align: center; }
            p.subtitle { color: #94a3b8; font-size: 0.85rem; text-align: center; margin-top: -0.5rem; margin-bottom: 1.2rem; }
            .status { margin: 0.8rem 0; padding: 0.8rem; border-radius: 8px; font-size: 0.85rem; background: #0f172a; border: 1px solid #334155; color: #cbd5e1; word-break: break-word; text-align: center; }
            .badge-live { display: inline-block; background: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; animation: pulse 1.5s infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
            
            .mic-select-box { margin-bottom: 1rem; text-align: left; }
            .mic-select-box label { font-size: 0.8rem; color: #94a3b8; display: block; margin-bottom: 0.3rem; }
            select { width: 100%; padding: 0.6rem; background: #0f172a; border: 1px solid #334155; color: #f8fafc; border-radius: 6px; font-size: 0.85rem; }

            .console-title { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: #64748b; margin-top: 0.8rem; margin-bottom: 0.4rem; display: flex; justify-content: space-between; align-items: center; }
            .transcript-box { background: #0b1329; border: 1px solid #1e293b; border-radius: 8px; height: 230px; overflow-y: auto; padding: 0.8rem; font-size: 0.9rem; display: flex; flex-direction: column; gap: 0.6rem; }
            .transcript-entry { padding: 0.5rem 0.7rem; border-radius: 8px; line-height: 1.4; }
            .entry-user { background: #1e293b; color: #38bdf8; border-left: 3px solid #38bdf8; }
            .entry-assistant { background: #16243b; color: #e2e8f0; border-left: 3px solid #10b981; }
            .entry-interim { color: #94a3b8; font-style: italic; }
            .tag { display: inline-block; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; background: #0284c7; color: white; margin-left: 6px; font-weight: 600; text-transform: uppercase; }
            .tag-tool { background: #7c3aed; }
            
            button { width: 100%; padding: 0.85rem; font-size: 0.95rem; font-weight: 600; border-radius: 8px; border: none; cursor: pointer; transition: all 0.2s; margin-top: 0.5rem; }
            .btn-direct { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35); font-size: 1.05rem; }
            .btn-direct:hover { background: linear-gradient(135deg, #059669 0%, #047857 100%); }
            .btn-init { background: #3b82f6; color: white; font-size: 0.85rem; padding: 0.6rem; }
            .btn-init:hover { background: #2563eb; }
            .btn-call { background: #10b981; color: white; display: none; font-size: 0.85rem; padding: 0.6rem; }
            .btn-call:hover { background: #059669; }
            .btn-hangup { background: #ef4444; color: white; display: none; }
            .btn-hangup:hover { background: #dc2626; }
            .webrtc-details { margin-top: 1rem; border: 1px dashed #334155; border-radius: 8px; padding: 0.6rem 0.8rem; font-size: 0.8rem; color: #94a3b8; }
            .webrtc-details summary { cursor: pointer; font-weight: 600; color: #38bdf8; outline: none; }
            button:disabled { background: #475569; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>MedFront AI Voice Receptionist</h2>
            <p class="subtitle">Tri-Module Live Voice Loop: Telephony + Speech + Azure OpenAI</p>
            
            <div class="mic-select-box">
                <label for="micSelect">🎤 Select Microphone Hardware:</label>
                <select id="micSelect"></select>
            </div>

            <div id="status" class="status">Click "Start Voice Call" to begin speaking with Aura</div>

            <div class="console-title">
                <span>Agentic Conversation Stream</span>
                <span id="liveIndicator" style="display:none;" class="badge-live">MIC ACTIVE</span>
            </div>
            <div id="transcriptBox" class="transcript-box">
                <div style="color: #475569; font-style: italic;">Turn history will appear here in real time as you speak...</div>
            </div>

            <button id="directCallBtn" class="btn-direct" onclick="startDirectVoiceCall()">🎙️ Start Voice Call (Instant)</button>
            <button id="hangupBtn" class="btn-hangup" onclick="hangUp()">🔴 End Call</button>

            <details class="webrtc-details">
                <summary>📞 Advanced: ACS Carrier WebRTC Dialing</summary>
                <p style="margin: 0.5rem 0; font-size: 0.75rem; color: #64748b;">Tests 2-leg Azure Communication Services Call Automation with WebRTC inbound client.</p>
                <button id="initBtn" class="btn-init" onclick="initClient()">1. Initialize Web Client</button>
                <button id="callBtn" class="btn-call" onclick="startCall()">2. Call Virtual Receptionist</button>
            </details>

            <a href="/dashboard" style="display:block; text-align:center; margin-top:1rem; font-size:0.85rem; color:#38bdf8; text-decoration:none; padding:0.65rem; border:1px solid rgba(56,189,248,0.3); border-radius:8px; background:rgba(56,189,248,0.08); font-weight:600; transition:all 0.2s;">
                🏥 Open Hospital Dashboard & Patient Records
            </a>
        </div>

        <script>
            let callAgent = null;
            let currentCall = null;
            let myUserId = null;
            let audioWs = null;
            let audioContext = null;
            let micStream = null;
            let processorNode = null;

            const log = (msg) => document.getElementById('status').innerText = msg;

            async function populateMicrophones() {
                try {
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
                    log("Microphone ready. Click 'Start Voice Call (Instant)' to begin.");
                } catch (e) {
                    console.warn("Could not list audio devices:", e);
                    if (e.name === 'NotAllowedError' || e.name === 'PermissionDeniedError') {
                        log("⚠️ Mic permission blocked. Click the lock/mic icon in the browser address bar to allow.");
                    } else {
                        log("Microphone status: " + (e.message || "Ready"));
                    }
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

                    // Unified AudioContext initialization
                    if (!audioContext) {
                        const AudioCtx = window.AudioContext || window.webkitAudioContext;
                        try {
                            audioContext = new AudioCtx({ sampleRate: 16000 });
                        } catch (e) {
                            audioContext = new AudioCtx();
                        }
                    }
                    playbackAudioCtx = audioContext;
                    if (audioContext.state === 'suspended') {
                        await audioContext.resume();
                    }

                    await startMicStreaming();
                    directBtn.style.display = 'none';
                    document.getElementById('hangupBtn').style.display = 'block';
                    log("🟢 Call Active! Speak naturally into your microphone.");
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

            async function initClient() {
                try {
                    if (!window.CallClient) {
                        log("Loading WebRTC bundle... please wait a moment.");
                        await new Promise(r => setTimeout(r, 1500));
                        if (!window.CallClient) throw new Error("WebRTC library bundle still loading. Please retry in 2 seconds.");
                    }
                    log("Fetching VoIP token from backend...");
                    document.getElementById('initBtn').disabled = true;

                    const res = await fetch('/api/telephony/token');
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.error || "Failed to fetch token");

                    myUserId = data.caller_user_id;
                    log("Token acquired! Initializing WebRTC CallClient...");

                    const callClient = new window.CallClient();
                    const tokenCredential = new window.AzureCommunicationTokenCredential(data.token);

                    callAgent = await callClient.createCallAgent(tokenCredential, { displayName: "Patient Caller" });
                    
                    callAgent.on('incomingCall', async (args) => {
                        log("Incoming Call from Call Automation! Connecting...");
                        const incomingCall = args.incomingCall;
                        currentCall = await incomingCall.accept();
                        muteWebRtcRemoteAudio();
                        setInterval(muteWebRtcRemoteAudio, 1000);
                        document.getElementById('callBtn').style.display = 'none';
                        document.getElementById('directCallBtn').style.display = 'none';
                        document.getElementById('hangupBtn').style.display = 'block';

                        currentCall.on('stateChanged', () => {
                            log("Call State: " + currentCall.state);
                            if (currentCall.state === 'Connected') {
                                startMicStreaming();
                            } else if (currentCall.state === 'Disconnected') {
                                hangUp();
                            }
                        });
                    });

                    log("Web Client Ready! Click '2. Call Virtual Receptionist'");
                    document.getElementById('initBtn').style.display = 'none';
                    document.getElementById('callBtn').style.display = 'block';
                } catch (err) {
                    log("Initialization Error: " + err.message);
                    document.getElementById('initBtn').disabled = false;
                }
            }

            async function startCall() {
                try {
                    log("Requesting Call Automation to call browser...");
                    document.getElementById('callBtn').disabled = true;

                    const res = await fetch('/api/telephony/call-browser', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ caller_user_id: myUserId })
                    });
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.error || "Failed to trigger call");

                    log("Call Automation dialing your browser via WebRTC...");
                } catch (err) {
                    log("Call Error: " + err.message);
                    document.getElementById('callBtn').disabled = false;
                }
            }

            async function startMicStreaming() {
                try {
                    let stream = null;
                    const selectEl = document.getElementById('micSelect');
                    const selectedDeviceId = selectEl ? selectEl.value : null;
                    
                    try {
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
                    } catch (e1) {
                        console.warn("Device-specific constraint failed, falling back to audio:true", e1);
                        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    }
                    micStream = stream;

                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/api/telephony/ws/audio-stream`;
                    audioWs = new WebSocket(wsUrl);

                    audioWs.onopen = () => {
                        console.log("[WS] Audio stream connected.");
                        const liveIndicator = document.getElementById('liveIndicator');
                        if (liveIndicator) liveIndicator.style.display = 'inline-block';
                    };

                    audioWs.onerror = (err) => {
                        console.error("[WS] Audio stream error:", err);
                        log("⚠️ Voice stream connection error.");
                    };

                    audioWs.onclose = () => {
                        console.log("[WS] Audio stream closed.");
                        const liveIndicator = document.getElementById('liveIndicator');
                        if (liveIndicator) liveIndicator.style.display = 'none';
                    };

                    audioWs.onmessage = (event) => {
                        const msg = JSON.parse(event.data);
                        handleSpeechEvent(msg);
                    };

                    if (!audioContext) {
                        const AudioCtx = window.AudioContext || window.webkitAudioContext;
                        try {
                            audioContext = new AudioCtx({ sampleRate: 16000 });
                        } catch (e) {
                            audioContext = new AudioCtx();
                        }
                    }
                    playbackAudioCtx = audioContext;
                    if (audioContext.state === 'suspended') {
                        await audioContext.resume();
                    }
                    const actualRate = audioContext.sampleRate;
                    log(`Mic active (${actualRate}Hz -> 16000Hz). Listening...`);

                    const source = audioContext.createMediaStreamSource(micStream);
                    processorNode = audioContext.createScriptProcessor(4096, 1, 1);
                    
                    let packetCount = 0;
                    const liveIndicator = document.getElementById('liveIndicator');
                    processorNode.onaudioprocess = (e) => {
                        if (!audioWs || audioWs.readyState !== WebSocket.OPEN) return;
                        const rawFloatData = e.inputBuffer.getChannelData(0);

                        // Visual energy indicator
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

                        packetCount++;
                        if (packetCount === 1) {
                            log("🟢 Audio stream active! Say 'Hello' or 'Book an appointment'...");
                        }
                    };

                    source.connect(processorNode);
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

            function stopMicStreaming() {
                const liveIndicator = document.getElementById('liveIndicator');
                if (liveIndicator) liveIndicator.style.display = 'none';

                if (processorNode) {
                    try { processorNode.disconnect(); } catch (e) {}
                    processorNode = null;
                }
                if (audioContext) {
                    try { audioContext.close(); } catch (e) {}
                    audioContext = null;
                    playbackAudioCtx = null;
                }
                if (micStream) {
                    try {
                        micStream.getTracks().forEach(track => track.stop());
                    } catch (e) {}
                    micStream = null;
                }
                if (audioWs) {
                    try { audioWs.close(); } catch (e) {}
                    audioWs = null;
                }
            }

            let isAiSpeaking = false;
            let currentSourceNode = null;
            let playbackAudioCtx = null;

            function stopAiPlayback() {
                if (currentSourceNode) {
                    try {
                        currentSourceNode.stop();
                        currentSourceNode.disconnect();
                    } catch (e) {}
                    currentSourceNode = null;
                }
                isAiSpeaking = false;
            }

            function muteWebRtcRemoteAudio() {
                // Ensure WebRTC remote audio elements are muted so only direct WebSocket audio plays
                document.querySelectorAll('audio').forEach(el => {
                    el.muted = true;
                });
            }

            async function playAudioBuffer(base64Data) {
                try {
                    stopAiPlayback(); // Interrupt any existing audio buffer immediately
                    muteWebRtcRemoteAudio();
                    if (!audioContext) {
                        const AudioCtx = window.AudioContext || window.webkitAudioContext;
                        audioContext = new AudioCtx();
                    }
                    playbackAudioCtx = audioContext;
                    if (playbackAudioCtx.state === 'suspended') {
                        await playbackAudioCtx.resume();
                    }

                    if (audioWs && audioWs.readyState === WebSocket.OPEN) {
                        try { audioWs.send(JSON.stringify({ type: "playback_start" })); } catch(e) {}
                    }

                    const binaryString = window.atob(base64Data);
                    const len = binaryString.length;
                    const bytes = new Uint8Array(len);
                    for (let i = 0; i < len; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    const audioBuffer = await playbackAudioCtx.decodeAudioData(bytes.buffer);
                    const sourceNode = playbackAudioCtx.createBufferSource();
                    sourceNode.buffer = audioBuffer;
                    sourceNode.connect(playbackAudioCtx.destination);
                    currentSourceNode = sourceNode;

                    isAiSpeaking = true;
                    sourceNode.onended = () => {
                        if (currentSourceNode === sourceNode) {
                            currentSourceNode = null;
                            setTimeout(() => { 
                                isAiSpeaking = false; 
                                if (audioWs && audioWs.readyState === WebSocket.OPEN) {
                                    try { audioWs.send(JSON.stringify({ type: "playback_end" })); } catch(e) {}
                                }
                            }, 100);
                        }
                    };
                    sourceNode.start(0);
                } catch (err) {
                    console.warn("Direct audio playback warning:", err);
                    isAiSpeaking = false;
                }
            }

            function handleSpeechEvent(msg) {
                const box = document.getElementById('transcriptBox');
                let interimEl = document.getElementById('interimText');

                if (msg.type === 'interrupt') {
                    console.log("[BARGE-IN] Received interrupt command from server. Stopping audio.");
                    stopAiPlayback();
                    return;
                }

                if (msg.type === 'audio') {
                    playAudioBuffer(msg.data);
                    return;
                }

                if (msg.type === 'interim') {
                    if (!interimEl) {
                        interimEl = document.createElement('div');
                        interimEl.id = 'interimText';
                        interimEl.className = 'transcript-entry entry-interim';
                        box.appendChild(interimEl);
                    }
                    interimEl.innerText = "🗣️ " + msg.text + "...";
                    box.scrollTop = box.scrollHeight;

                } else if (msg.type === 'final') {
                    if (interimEl) interimEl.remove();

                    const finalEl = document.createElement('div');
                    finalEl.className = 'transcript-entry entry-user';
                    finalEl.innerHTML = `<strong>You:</strong> ${msg.text}`;
                    box.appendChild(finalEl);
                    box.scrollTop = box.scrollHeight;

                } else if (msg.type === 'assistant') {
                    const assistantEl = document.createElement('div');
                    assistantEl.className = 'transcript-entry entry-assistant';
                    
                    let tags = `<span class="tag">[${msg.intent || 'CONVERSATION'}]</span>`;
                    if (msg.tool_used) {
                        tags += ` <span class="tag tag-tool">[Tool: ${msg.tool_used}]</span>`;
                    }

                    assistantEl.innerHTML = `<div><strong>Aura:</strong> ${tags}</div><div style="margin-top:4px;">${msg.text}</div>`;
                    box.appendChild(assistantEl);
                    box.scrollTop = box.scrollHeight;
                }
            }

            async function hangUp() {
                log("Ending call...");
                stopAiPlayback();
                stopMicStreaming();
                if (currentCall) {
                    try {
                        await currentCall.hangUp();
                    } catch (e) {
                        console.warn("Call hangup error:", e);
                    }
                    currentCall = null;
                }
                const hangupBtn = document.getElementById('hangupBtn');
                if (hangupBtn) hangupBtn.style.display = 'none';

                const directBtn = document.getElementById('directCallBtn');
                if (directBtn) {
                    directBtn.style.display = 'block';
                    directBtn.disabled = false;
                }

                const callBtn = document.getElementById('callBtn');
                if (callBtn) {
                    callBtn.disabled = false;
                }

                const initBtn = document.getElementById('initBtn');
                if (initBtn && !callAgent) {
                    initBtn.disabled = false;
                }

                const liveIndicator = document.getElementById('liveIndicator');
                if (liveIndicator) liveIndicator.style.display = 'none';

                log("Call ended. Click 'Start Voice Call (Instant)' to speak again.");
            }
        </script>
    </body>
    </html>
    """
