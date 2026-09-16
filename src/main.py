"""
AuraCare Main FastAPI Application Entrypoint.
Registers routers for isolated modules and provides health check endpoints.
"""

import logging
from fastapi import FastAPI
from src.core.config import settings
from src.telephony.router import router as telephony_router

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="MedFront / AuraCare Voice AI Platform",
    version="0.1.0",
    description="Enterprise Healthcare Voice AI Receptionist on Microsoft Azure",
)

# Register Module 1: Telephony Router
app.include_router(telephony_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend status."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "module_1_telephony": "enabled",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=(settings.environment == "development"),
    )
