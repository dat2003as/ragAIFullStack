"""
AI Chat Backend API với cấu trúc v1
"""
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import logging
import time
from collections import defaultdict

# Config
from core.config import APP_SETTINGS
from prometheus_client import make_asgi_app

# API Router
from api.router import api_router

# Middleware
from middleware import (
    setup_cors,
    LoggingMiddleware,
    setup_error_handlers,
    RateLimiter
)

# Monitoring
from monitoring.tracing import setup_telemetry
from monitoring.metrics import http_request_duration, http_requests_total,active_sessions


# ========== LOGGING CONFIG ==========
logging.basicConfig(
    level=APP_SETTINGS.LOG_LEVEL,
    format=APP_SETTINGS.LOG_FORMAT
)
logger = logging.getLogger(__name__)


# ========== CREATE APP ==========
app = FastAPI(
    title=APP_SETTINGS.APP_NAME,
    version=APP_SETTINGS.APP_VERSION,
    description="AI-powered chat application with image and CSV support",
    debug=APP_SETTINGS.DEBUG
)


# ========== LIFESPAN EVENTS ==========
# main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    logger.info("🚀 Starting AI Chat Backend...")

    app.state.chat_history = defaultdict(list)
    
    app.state.sessions = defaultdict(lambda: {
        "images": {},      
        "csvs": {},        
        "documents": {},   
        "created_at":  time.time(),
        "last_activity": time.time()
    })
    
    app.state.session_timestamps = {}
    
    logger.info("✅ In-memory storage initialized")
    
    # Setup telemetry
    if APP_SETTINGS.ENABLE_TRACING:
        setup_telemetry(app, service_name=APP_SETTINGS.APP_NAME)
    
    logger.info(f"✅ {APP_SETTINGS.APP_NAME} v{APP_SETTINGS.APP_VERSION} is ready!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    app.state.chat_history.clear()
    app.state.sessions.clear()
    logger.info("✅ Cleanup completed")


app.router.lifespan_context = lifespan


# ========== MIDDLEWARE SETUP ==========
setup_cors(app)
app.add_middleware(RateLimiter, requests_per_minute=60)
app.add_middleware(LoggingMiddleware)


@app.middleware("http")
async def add_metrics_middleware(request: Request, call_next):
    """Middleware to track HTTP request metrics"""
    start_time = time.time()
    if hasattr(request.app.state, "sessions"):
        active_sessions.set(len(request.app.state.sessions))
    else:
        active_sessions.set(0)

    response = await call_next(request)
    duration = time.time() - start_time

    http_request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code
    ).inc()

    return response


# ========== ERROR HANDLERS ==========
setup_error_handlers(app)


# ========== METRICS ENDPOINT ==========
# Mount Prometheus metrics at /metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ========== INCLUDE API ROUTER ==========
app.include_router(api_router)


# ========== ROOT ENDPOINT ==========
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": APP_SETTINGS.APP_NAME,
        "version": APP_SETTINGS.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "metrics": "/metrics"  
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=APP_SETTINGS.HOST,
        port=APP_SETTINGS.PORT,
        reload=APP_SETTINGS.DEBUG
    )