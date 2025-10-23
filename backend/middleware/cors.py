from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config.settings import APP_SETTINGS 


def setup_cors(app: FastAPI):
    """Setup CORS middleware"""
    
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=APP_SETTINGS.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=APP_SETTINGS.CORS_METHODS,
        allow_headers=APP_SETTINGS.CORS_HEADERS,
        expose_headers=["*"], 
    )
    
    print("✅ CORS middleware configured")