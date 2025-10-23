"""
Prometheus monitoring setup for FastAPI
"""
from prometheus_client import start_http_server, REGISTRY, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry
from fastapi import Response
import logging

logger = logging.getLogger(__name__)


def setup_telemetry(app, service_name: str = "ai-chat-backend"):
    """
    Setup Prometheus metrics for FastAPI app.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service (for logging purposes)
    """
    logger.info(f"🚀 Setting up Prometheus monitoring for {service_name}")
    
    # Add Prometheus metrics endpoint to FastAPI
    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics"""
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    
    # Start Prometheus metrics HTTP server on separate port (optional)
    try:
        start_http_server(port=8001, addr="0.0.0.0", registry=REGISTRY)
        logger.info("✅ Prometheus metrics server started on port 8001")
    except OSError as e:
        logger.warning(f"⚠️ Could not start metrics server on port 8001: {e}")
        logger.info("📊 Metrics still available at /metrics endpoint")
    
    logger.info("✅ Prometheus monitoring setup complete")
    
    return None  # No tracer needed for Prometheus


def get_tracer():
    return None


def create_span(name: str, attributes: dict = None):
    """
    Dummy span context manager for backwards compatibility.
    
    Usage:
        with create_span("operation_name", {"key": "value"}):
            # your code here
            pass
    """
    from contextlib import contextmanager
    
    @contextmanager
    def dummy_span():
        class DummySpan:
            def set_attribute(self, key, value):
                """No-op for compatibility"""
                pass
            
            def add_event(self, name, attributes=None):
                """No-op for compatibility"""
                pass
            
            def set_status(self, status):
                """No-op for compatibility"""
                pass
        
        yield DummySpan()
    
    return dummy_span()


def get_meter(name: str = __name__):
    return None