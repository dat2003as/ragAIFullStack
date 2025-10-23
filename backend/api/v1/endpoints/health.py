from fastapi import APIRouter, Request
from models.schemas import HealthResponse
from core.config import APP_SETTINGS
import time

router = APIRouter()

startup_time = time.time()


@router.get("", response_model=HealthResponse, tags=["Health"])
async def health_check(request: Request):
    """
    Health check endpoint — returns service status and component health.
    """
    components = {
        "metrics": "enabled" if APP_SETTINGS.ENABLE_METRICS else "disabled",
        "tracing": "enabled" if APP_SETTINGS.ENABLE_TRACING else "disabled",
    }

    components["gemini_api"] = (
        "configured" if APP_SETTINGS.GEMINI_API_KEY else "not_configured"
    )

    return HealthResponse(
        status="healthy",
        version=APP_SETTINGS.APP_VERSION,
        timestamp=time.time(),
        components=components,
    )
