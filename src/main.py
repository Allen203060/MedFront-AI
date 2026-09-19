"""
AuraCare Main FastAPI Application Entrypoint.
Registers routers for isolated modules and provides health check endpoints.
"""

import logging
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.core.config import settings
from src.telephony.router import router as telephony_router
from src.dashboard.router import router as dashboard_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="MedFront / AuraCare Voice AI Platform",
    version="0.1.0",
    description="Enterprise Healthcare Voice AI Receptionist on Microsoft Azure",
)

# Register Module 1: Telephony Router & Hospital Dashboard
app.include_router(telephony_router)
app.include_router(dashboard_router)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root traffic directly to the Hospital & Voice AI Dashboard."""
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
