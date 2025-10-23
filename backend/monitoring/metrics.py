from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Chat metrics
chat_requests_counter = Counter(
    "chat_requests_total",
    "Total chat requests",
    ["status"]  
)
active_sessions = Gauge(
    "active_sessions",
    "Current active sessions"
)
chat_errors_counter = Counter(
    "chat_errors_total",
    "Total number of chat errors",
    ["error_type"]
)

message_length_histogram = Histogram(
    "message_length_chars",
    "Distribution of user message lengths",
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

gemini_api_duration = Histogram(
    "gemini_api_duration_seconds",
    "Gemini API latency",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

file_upload_counter = Counter(
    "file_uploads_total",
    "Total file uploads",
    ["file_type"]  
)

file_size_histogram = Histogram(
    "file_upload_size_bytes",
    "Uploaded file size",
    ["file_type"],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600]  
)

csv_rows_processed = Counter(
    "csv_rows_processed_total",
    "Total CSV rows processed"
)

image_processing_duration = Histogram(
    "image_processing_duration_seconds",
    "Image processing duration",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

image_dimensions_histogram = Histogram(
    "image_dimensions_pixels",
    "Distribution of image dimensions (width*height)",
    buckets=[10000, 50000, 100000, 500000, 1000000, 5000000, 10000000]
)


document_processing_duration = Histogram(
    "document_processing_duration_seconds",
    "Document processing duration",
    ["document_type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

document_processing_errors = Counter(
    "document_processing_errors_total",
    "Total document processing errors",
    ["document_type"]
)

document_chars_processed = Counter(
    "document_chars_processed_total",
    "Total characters processed from documents"
)

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)


def track_duration(metric_histogram):
    """
    Decorator to track function execution duration
    
    Usage:
        @track_duration(gemini_api_duration)
        async def call_gemini():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric_histogram.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric_histogram.observe(duration)
        
        # Check if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def increment_counter(counter, value=1, labels: dict = None):
    """
    Helper to increment counter with optional labels
    
    Args:
        counter: Prometheus Counter object
        value: Amount to increment (default: 1)
        labels: Dictionary of label values
    """
    if labels:
        counter.labels(**labels).inc(value)
    else:
        counter.inc(value)


def observe_histogram(histogram, value, labels: dict = None):
    """
    Helper to record histogram observation with optional labels
    
    Args:
        histogram: Prometheus Histogram object
        value: Value to observe
        labels: Dictionary of label values
    """
    if labels:
        histogram.labels(**labels).observe(value)
    else:
        histogram.observe(value)