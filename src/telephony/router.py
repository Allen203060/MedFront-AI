"""
FastAPI Router for Telephony Call Automation and Web Calling Interface.
Connects Module 1 (Telephony) and Module 2 (Speech: STT & TTS) for real-time
full-duplex conversational testing with live visual transcription and barge-in.
"""
import asyncio
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
            logger.info(f"Call {call_connection_id} connected! Synthesizing neural greeting...")

            greeting_text = (
                "Hello, thank you for calling MedFront Clinic. "
                "My name is Jenny, your virtual medical receptionist. "
                "I am listening. Please speak to test our real-time voice recognition."
            )

            if tts_engine and settings.azure_speech_key:
                audio_bytes = tts_engine.synthesize_text(greeting_text)
                audio_id = f"greeting_{int(time.time())}"
                audio_cache[audio_id] = audio_bytes
                audio_url = f"{base_url}/api/telephony/audio/dynamic/{audio_id}.wav"
            else:
                audio_url = "https://raw.githubusercontent.com/Azure-Samples/communication-services-python-quickstarts/main/CallAutomation_Play/hello.wav"

            # Allow WebRTC jitter buffer to settle before playing
            await asyncio.sleep(1.0)
            active_call_state["is_playing_audio"] = True
            telephony_service.play_audio(call_connection_id=call_connection_id, audio_url=audio_url)

        elif event_type == "Microsoft.Communication.PlayCompleted":
            active_call_state["is_playing_audio"] = False
            logger.info(f"Playback completed on {call_connection_id}. Call remains open for caller speech.")

        elif event_type == "Microsoft.Communication.PlayFailed":
            active_call_state["is_playing_audio"] = False
            result_info = data.get("resultInformation", {})
            logger.error(f"Audio playback FAILED on call {call_connection_id}. Reason: {result_info}")

        elif event_type == "Microsoft.Communication.CallDisconnected":
            active_call_state["call_connection_id"] = None
            active_call_state["is_playing_audio"] = False
            logger.info(f"Call {call_connection_id} disconnected.")

    return Response(status_code=status.HTTP_200_OK)


@router.websocket("/ws/audio-stream")
async def audio_stream_websocket(websocket: WebSocket) -> None:
    """
    WebSocket endpoint that receives raw 16kHz PCM audio from the browser microphone,
    pipes it into SpeechToTextEngine, and returns real-time interim and final transcripts.
    """
    await websocket.accept()
    logger.info("Browser audio WebSocket connected. Initializing STT stream...")

    loop = asyncio.get_running_loop()

    def on_interim(text: str) -> None:
        """Fires when interim speech is recognized (Barge-in trigger)."""
        # 1. Barge-In: If the AI is currently playing TTS and user speaks, cancel playback immediately!
        if active_call_state.get("is_playing_audio") and active_call_state.get("call_connection_id"):
            call_id = active_call_state["call_connection_id"]
            logger.info(f"[BARGE-IN TRIGGERED] User spoke: '{text}'. Canceling audio on {call_id}...")
            try:
                if telephony_service.client:
                    conn = telephony_service.client.get_call_connection(call_id)
                    conn.cancel_all_media_operations()
                active_call_state["is_playing_audio"] = False
            except Exception as e:
                logger.warning(f"Barge-in cancel error: {e}")

        # 2. Push interim text back to browser UI
        asyncio.run_coroutine_threadsafe(
            websocket.send_json({"type": "interim", "text": text}),
            loop,
        )

    def on_final(text: str) -> None:
        """Fires when user pauses and sentence is finalized."""
        logger.info(f"[STT Finalized]: '{text}'")

        # 1. Push final transcript to browser UI
        asyncio.run_coroutine_threadsafe(
            websocket.send_json({"type": "final", "text": text}),
            loop,
        )

        # 2. Conversational Voice Echo: Speak back over the call!
        call_id = active_call_state.get("call_connection_id")
        if call_id and tts_engine and settings.acs_callback_base_url:
            try:
                echo_text = f"I heard you say: {text}. How else may I assist you?"
                audio_bytes = tts_engine.synthesize_text(echo_text)
                audio_id = f"echo_{int(time.time())}"
                audio_cache[audio_id] = audio_bytes
                base_url = settings.acs_callback_base_url.rstrip("/")
                audio_url = f"{base_url}/api/telephony/audio/dynamic/{audio_id}.wav"
                active_call_state["is_playing_audio"] = True
                telephony_service.play_audio(call_connection_id=call_id, audio_url=audio_url)
            except Exception as e:
                logger.error(f"Failed to play echo response: {e}")

    # Initialize continuous STT engine with 800ms silence timeout
    stt_engine = SpeechToTextEngine(
        on_interim_result=on_interim,
        on_final_result=on_final,
        end_silence_timeout_ms=1200,
    )
    stt_engine.start_recognition()

    try:
        while True:
            # Ingest binary 16kHz PCM audio packets from browser
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                stt_engine.write_audio_chunk(message["bytes"])
    except WebSocketDisconnect:
        logger.info("Browser audio WebSocket disconnected.")
    except Exception as e:
        logger.error(f"WebSocket error in audio stream: {e}")
    finally:
        stt_engine.close_stream()
        stt_engine.stop_recognition()


@router.get("/web-caller", response_class=HTMLResponse, summary="Browser VoIP Web Calling Test Page")
async def get_web_caller_page() -> str:
    """Interactive WebRTC browser calling test client with live speech transcription."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MedFront AI Voice Receptionist</title>
        <!-- Load local Azure Calling SDK bundle -->
        <script src="/api/telephony/static/bundle.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 1rem; box-sizing: border-box; }
            .card { background: #1e293b; padding: 2rem; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 500px; max-width: 100%; border: 1px solid #334155; }
            h2 { margin-top: 0; color: #38bdf8; font-size: 1.5rem; text-align: center; }
            p.subtitle { color: #94a3b8; font-size: 0.85rem; text-align: center; margin-top: -0.5rem; margin-bottom: 1.5rem; }
            .status { margin: 1rem 0; padding: 0.8rem; border-radius: 8px; font-size: 0.85rem; background: #0f172a; border: 1px solid #334155; color: #cbd5e1; word-break: break-word; text-align: center; }
            .badge-live { display: inline-block; background: #ef4444; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: bold; animation: pulse 1.5s infinite; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
            
            /* Transcript Console */
            .console-title { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; color: #64748b; margin-top: 1rem; margin-bottom: 0.4rem; display: flex; justify-content: space-between; }
            .transcript-box { background: #0b1329; border: 1px solid #1e293b; border-radius: 8px; height: 160px; overflow-y: auto; padding: 0.8rem; font-size: 0.9rem; display: flex; flex-direction: column; gap: 0.5rem; }
            .transcript-entry { padding: 0.4rem 0.6rem; border-radius: 6px; }
            .entry-user { background: #1e293b; color: #38bdf8; border-left: 3px solid #38bdf8; }
            .entry-interim { color: #94a3b8; font-style: italic; }
            
            button { width: 100%; padding: 0.85rem; font-size: 0.95rem; font-weight: 600; border-radius: 8px; border: none; cursor: pointer; transition: all 0.2s; margin-top: 0.5rem; }
            .btn-init { background: #3b82f6; color: white; }
            .btn-init:hover { background: #2563eb; }
            .btn-call { background: #10b981; color: white; display: none; }
            .btn-call:hover { background: #059669; }
            .btn-hangup { background: #ef4444; color: white; display: none; }
            .btn-hangup:hover { background: #dc2626; }
            button:disabled { background: #475569; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>MedFront AI Voice Receptionist</h2>
            <p class="subtitle">Modules 1 & 2: Telephony + Neural Voice + Real-Time STT</p>
            
            <div id="status" class="status">Click "Initialize Web Client" to begin</div>

            <div class="console-title">
                <span>Live Speech Transcript</span>
                <span id="liveIndicator" style="display:none;" class="badge-live">MIC ACTIVE</span>
            </div>
            <div id="transcriptBox" class="transcript-box">
                <div style="color: #475569; font-style: italic;">Transcripts will appear here in real time as you speak...</div>
            </div>

            <button id="initBtn" class="btn-init" onclick="initClient()">1. Initialize Web Client</button>
            <button id="callBtn" class="btn-call" onclick="startCall()">2. Call AI Receptionist</button>
            <button id="hangupBtn" class="btn-hangup" onclick="hangUp()">End Call</button>
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

            async function initClient() {
                try {
                    log("Fetching VoIP token from backend...");
                    document.getElementById('initBtn').disabled = true;

                    const res = await fetch('/api/telephony/token');
                    const data = await res.json();
                    if (!res.ok) throw new Error(data.error || "Failed to fetch token");

                    myUserId = data.caller_user_id;
                    log("Token acquired! Initializing WebRTC CallClient...");

                    const callClient = new window.CallClient();
                    const tokenCredential = new window.AzureCommunicationTokenCredential(data.token);

                    callAgent = await callClient.createCallAgent(tokenCredential, { displayName: "Browser Patient" });
                    
                    // Listen for incoming call from Call Automation
                    callAgent.on('incomingCall', async (args) => {
                        log("Incoming Call from Call Automation! Connecting...");
                        const incomingCall = args.incomingCall;
                        currentCall = await incomingCall.accept();
                        document.getElementById('callBtn').style.display = 'none';
                        document.getElementById('hangupBtn').style.display = 'block';

                        currentCall.on('stateChanged', () => {
                            log("Call State: " + currentCall.state);
                            if (currentCall.state === 'Connected') {
                                startMicStreaming();
                            } else if (currentCall.state === 'Disconnected') {
                                stopMicStreaming();
                                log("Call disconnected.");
                                document.getElementById('hangupBtn').style.display = 'none';
                                document.getElementById('callBtn').style.display = 'block';
                                document.getElementById('callBtn').disabled = false;
                            }
                        });
                    });

                    log("Web Client Ready! Click 'Call AI Receptionist'");
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

            // Downsamples arbitrary hardware audio (48kHz/44.1kHz) down to exactly 16kHz
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

            async function startMicStreaming() {
                try {
                    document.getElementById('liveIndicator').style.display = 'inline-block';
                    
                    // 1. Connect WebSocket to backend audio streamer
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/api/telephony/ws/audio-stream`;
                    audioWs = new WebSocket(wsUrl);

                    audioWs.onmessage = (event) => {
                        const msg = JSON.parse(event.data);
                        handleSpeechEvent(msg);
                    };

                    // 2. Request user microphone with active hardware Noise & Echo Cancellation
                    micStream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            channelCount: 1,
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true,
                        }
                    });

                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const actualRate = audioContext.sampleRate;
                    log(`Microphone active (Hardware rate: ${actualRate}Hz -> Downsampling to 16000Hz)`);

                    const source = audioContext.createMediaStreamSource(micStream);

                    // 3. Process buffer and downsample to 16kHz before transmission
                    processorNode = audioContext.createScriptProcessor(4096, 1, 1);
                    processorNode.onaudioprocess = (e) => {
                        if (!audioWs || audioWs.readyState !== WebSocket.OPEN) return;
                        const rawFloatData = e.inputBuffer.getChannelData(0);
                        
                        // Downsample 48kHz/44.1kHz to 16kHz
                        const downsampled = downsampleTo16k(rawFloatData, actualRate);

                        // Convert Float32Array [-1.0, 1.0] to 16-bit Mono PCM bytes
                        const pcmData = new Int16Array(downsampled.length);
                        for (let i = 0; i < downsampled.length; i++) {
                            const s = Math.max(-1, Math.min(1, downsampled[i]));
                            pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                        }
                        audioWs.send(pcmData.buffer);
                    };

                    source.connect(processorNode);
                    // Prevent local loopback echo to speaker
                    const muteGain = audioContext.createGain();
                    muteGain.gain.value = 0;
                    processorNode.connect(muteGain);
                    muteGain.connect(audioContext.destination);

                } catch (err) {
                    console.error("Failed to start mic stream:", err);
                    log("Microphone access error: " + err.message);
                }
            }


            function stopMicStreaming() {
                document.getElementById('liveIndicator').style.display = 'none';
                if (processorNode) processorNode.disconnect();
                if (audioContext) audioContext.close();
                if (micStream) micStream.getTracks().forEach(track => track.stop());
                if (audioWs) audioWs.close();
            }

            function handleSpeechEvent(msg) {
                const box = document.getElementById('transcriptBox');
                let interimEl = document.getElementById('interimText');

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
                }
            }

            async function hangUp() {
                stopMicStreaming();
                if (currentCall) {
                    await currentCall.hangUp();
                }
            }
        </script>
    </body>
    </html>
    """
