"""
FastAPI Router for Telephony Call Automation and Web Calling Interface.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from src.core.config import settings
from src.telephony.service import telephony_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telephony", tags=["Telephony"])

AUDIO_DIR = Path(__file__).resolve().parent / "audio"
STATIC_DIR = Path(__file__).resolve().parent / "static"


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


@router.get("/audio/hello.wav", summary="Serve static greeting WAV file to ACS")
async def get_hello_audio() -> FileResponse:
    """Serves the hello.wav audio file to ACS for playback."""
    audio_path = AUDIO_DIR / "hello.wav"
    if not audio_path.exists():
        logger.error(f"Audio file not found at: {audio_path}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, 
            content={"error": "Audio file not found"}
        )
    return FileResponse(path=str(audio_path), media_type="audio/wav")


@router.post("/callbacks", summary="ACS Call Automation Lifecycle Events")
async def handle_call_callbacks(request: Request) -> Response:
    """Receives call state events (CallConnected, PlayCompleted, CallDisconnected)."""
    events: List[Dict[str, Any]] = await request.json()
    logger.info(f"ACS Call Callback received: {events}")

    if not settings.acs_callback_base_url:
        logger.error("ACS_CALLBACK_BASE_URL is not configured during callback processing.")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    base_url = settings.acs_callback_base_url.rstrip("/")

    for event in events:
        event_type = event.get("type")
        data = event.get("data", {})
        call_connection_id = data.get("callConnectionId")

        logger.info(f"Event: {event_type} for CallConnectionId: {call_connection_id}")

        if event_type == "Microsoft.Communication.CallConnected":
            logger.info(f"Call {call_connection_id} connected! Streaming greeting audio.")
            audio_url = "https://raw.githubusercontent.com/Azure-Samples/communication-services-python-quickstarts/main/CallAutomation_Play/hello.wav"
            await asyncio.sleep(1.0)
            telephony_service.play_audio(call_connection_id=call_connection_id, audio_url=audio_url)

        elif event_type == "Microsoft.Communication.PlayCompleted":
            logger.info(f"Audio playback completed on call {call_connection_id}. Hanging up.")
            telephony_service.hang_up(call_connection_id=call_connection_id)
        
        elif event_type == "Microsoft.Communication.PlayFailed":
            result_info = data.get("resultInformation", {})
            logger.error(f"Audio playback FAILED on call {call_connection_id}. Reason: {result_info}")
            telephony_service.hang_up(call_connection_id=call_connection_id)

        elif event_type == "Microsoft.Communication.CallDisconnected":
            logger.info(f"Call {call_connection_id} has disconnected.")

    return Response(status_code=status.HTTP_200_OK)


@router.get("/web-caller", response_class=HTMLResponse, summary="Browser VoIP Web Calling Test Page")
async def get_web_caller_page() -> str:
    """Interactive WebRTC browser calling test client using local SDK bundle."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MedFront Web Calling Test</title>
        <!-- Load local Azure Calling SDK bundle (zero CORS/MIME issues) -->
        <script src="/api/telephony/static/bundle.js"></script>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: #1e293b; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); width: 440px; text-align: center; border: 1px solid #334155; }
            h2 { margin-top: 0; color: #38bdf8; font-size: 1.5rem; }
            p { color: #94a3b8; font-size: 0.9rem; line-height: 1.5; margin-bottom: 1.5rem; }
            .status { margin: 1.5rem 0; padding: 1rem; border-radius: 8px; font-size: 0.9rem; background: #0f172a; border: 1px solid #334155; color: #cbd5e1; min-height: 20px; word-break: break-word; }
            button { width: 100%; padding: 0.9rem; font-size: 1rem; font-weight: 600; border-radius: 8px; border: none; cursor: pointer; transition: all 0.2s; margin-top: 0.5rem; }
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
            <p>Module 1: WebRTC Calling Test<br><small style="color:#64748b">Azure Call Automation (No phone number required)</small></p>
            <div id="status" class="status">Click "Initialize Web Client" to begin</div>
            <button id="initBtn" class="btn-init" onclick="initClient()">1. Initialize Web Client</button>
            <button id="callBtn" class="btn-call" onclick="startCall()">2. Call AI Receptionist</button>
            <button id="hangupBtn" class="btn-hangup" onclick="hangUp()">Hang Up</button>
        </div>

        <script>
            let callAgent = null;
            let currentCall = null;
            let myUserId = null;

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
                            if (currentCall.state === 'Disconnected') {
                                log("Audio completed. Call disconnected.");
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

            async function hangUp() {
                if (currentCall) {
                    await currentCall.hangUp();
                }
            }
        </script>
    </body>
    </html>
    """
