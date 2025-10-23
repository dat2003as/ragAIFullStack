from fastapi import APIRouter
from .v1.endpoints import chat, health, upload_csv, upload_image, upload_doc

# Router gốc
api_router = APIRouter(prefix="/api/v1")

# Gắn từng router với prefix riêng
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(upload_csv.router, prefix="/upload-csv", tags=["Upload CSV"])
api_router.include_router(upload_image.router, prefix="/upload-image", tags=["Upload Image"])
api_router.include_router(upload_doc.router, prefix="/upload-document", tags=["Upload Document"])
