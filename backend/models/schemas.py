# backend/models/schemas.py
"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Types of messages"""
    TEXT = "text"
    IMAGE = "image"
    CSV = "csv"
    ERROR = "error"


# ========== CHAT SCHEMAS ==========
class ChatMessage(BaseModel):
    """Single chat message"""
    role: MessageRole
    content: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What's in this image?",
                "timestamp": 1704067200.0,
                "message_type": "text"
            }
        }


class ChatRequest(BaseModel):
    """Request to send a chat message"""
    session_id: str = Field(..., min_length=1, description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate message is not empty or just whitespace"""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "What is the average price in this dataset?"
            }
        }


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    response: str = Field(..., description="Assistant's response")
    session_id: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Based on the uploaded CSV, the average price is $45.30.",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": 1704067200.0
            }
        }


class ChatHistoryResponse(BaseModel):
    """Response containing chat history"""
    session_id: str
    messages: List[ChatMessage]
    total_messages: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [],
                "total_messages": 0
            }
        }


# ========== FILE UPLOAD SCHEMAS ==========
class FileUploadResponse(BaseModel):
    """Response after successful file upload"""
    status: str = "uploaded"
    filename: str
    file_type: str
    size_bytes: int
    session_id: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "uploaded",
                "filename": "product_photo.jpg",
                "file_type": "image",
                "size_bytes": 1024000,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "metadata": {
                    "width": 1920,
                    "height": 1080
                }
            }
        }


class ImageUploadResponse(FileUploadResponse):
    """Response after image upload"""
    preview_url: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "uploaded",
                "filename": "photo.jpg",
                "file_type": "image",
                "size_bytes": 2048000,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "preview_url": "/uploads/images/550e8400_photo.jpg",
                "dimensions": {"width": 1920, "height": 1080}
            }
        }


class CSVUploadResponse(FileUploadResponse):
    """Response after CSV upload"""
    rows: int
    columns: List[str]
    sample_data: Optional[List[Dict]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "uploaded",
                "filename": "sales_data.csv",
                "file_type": "csv",
                "size_bytes": 512000,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "rows": 1000,
                "columns": ["date", "product", "price", "quantity"]
            }
        }


class CSVUrlRequest(BaseModel):
    """Request to load CSV from URL"""
    session_id: str = Field(..., min_length=1)
    url: str = Field(..., description="URL to CSV file")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://raw.githubusercontent.com/user/repo/main/data.csv"
            }
        }


# ========== ERROR SCHEMAS ==========
class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Invalid file format",
                "detail": "Only PNG and JPG images are supported",
                "timestamp": 1704067200.0
            }
        }


# ========== HEALTH CHECK SCHEMAS ==========
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    components: Optional[Dict[str, str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": 1704067200.0,
                "components": {
                    "gemini_api": "connected",
                    "metrics": "enabled"
                }
            }
        }


# ========== METRICS SCHEMAS ==========
class MetricsResponse(BaseModel):
    """Metrics summary response"""
    total_requests: int
    total_errors: int
    active_sessions: int
    uptime_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_requests": 1523,
                "total_errors": 12,
                "active_sessions": 5,
                "uptime_seconds": 3600.5
            }
        }