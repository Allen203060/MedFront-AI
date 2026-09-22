"""
MedFront Main FastAPI Application Entrypoint.
Registers routers for isolated modules and provides health check endpoints.
"""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from src.core.config import settings
from src.telephony.router import router as telephony_router
from src.dashboard.router import router as dashboard_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="MedFront / MedFront Voice AI Platform",
    version="0.1.0",
    description="Enterprise Healthcare Voice AI Receptionist on Microsoft Azure",
)

# Enable CORS for modern React Single-Page Application (Vite / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from fastapi.staticfiles import StaticFiles

# Register Module 1: Telephony Router & Hospital Dashboard
app.include_router(telephony_router)
app.include_router(dashboard_router)


@app.websocket("/ws/audio")
@app.websocket("/ws/audio-stream")
async def root_audio_websocket(websocket: WebSocket):
    """Direct root proxy to full-duplex telephony audio stream WebSocket."""
    from src.telephony.router import audio_stream_websocket
    await audio_stream_websocket(websocket)


# Mount dedicated React Single-Page Application when built
if os.path.exists("frontend/dist"):
    app.mount("/app", StaticFiles(directory="frontend/dist", html=True), name="react_app")


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root traffic directly to the React Application if built, else /dashboard."""
    if os.path.exists("frontend/dist"):
        return RedirectResponse(url="/app/")
    return RedirectResponse(url="/dashboard")


@app.get("/web-caller", include_in_schema=False)
async def web_caller_redirect():
    """Redirect /web-caller to Module 1 WebRTC / Web Audio Calling Interface."""
    return RedirectResponse(url="/api/telephony/web-caller")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "module_1_telephony": "enabled",
        "hospital_dashboard": "enabled",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.environment == "development"),
    )
