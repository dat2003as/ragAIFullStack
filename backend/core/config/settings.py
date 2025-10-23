from .design_pattern import singleton
from .env import Env


@singleton
class AppSettings:
    def __init__(self):
        # ========== API KEYS ==========
        self.GEMINI_API_KEY = Env.get("GEMINI_API_KEY", "")

        # ========== APP SETTINGS ==========
        self.APP_NAME = Env.get("APP_NAME", "AI Chat Backend")
        self.APP_VERSION = Env.get("APP_VERSION", "1.0.0")
        self.DEBUG = Env.get("DEBUG", "False").lower() == "true"

        # ========== SERVER ==========
        self.HOST = Env.get("HOST", "0.0.0.0")
        self.PORT = int(Env.get("PORT", 8000))
        self.METRICS_PORT = int(Env.get("METRICS_PORT", 8001))

        # ========== CORS ==========
        cors_origins = Env.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:6868")
        self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        if not self.CORS_ORIGINS:
            self.CORS_ORIGINS = ["*"]
        self.CORS_METHODS = Env.get("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
        self.CORS_HEADERS = Env.get("CORS_HEADERS", "Authorization,Content-Type").split(",")
        # ========== FILE UPLOAD ==========
        self.MAX_UPLOAD_SIZE_MB = int(Env.get("MAX_UPLOAD_SIZE_MB", 10))
        self.MAX_IMAGE_DIMENSION = int(Env.get("MAX_IMAGE_DIMENSION", 4096))
        self.IMAGE_QUALITY = int(Env.get("IMAGE_QUALITY", 85))

        # ========== CSV PROCESSING ==========
        self.MAX_CSV_ROWS = int(Env.get("MAX_CSV_ROWS", 100000))
        self.CSV_CHUNK_SIZE = int(Env.get("CSV_CHUNK_SIZE", 10000))

        # ========== GEMINI SETTINGS ==========
        self.GEMINI_MODEL = Env.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.GEMINI_TEMPERATURE = float(Env.get("GEMINI_TEMPERATURE", 0.7))
        self.GEMINI_MAX_TOKENS = int(Env.get("GEMINI_MAX_TOKENS", 2048))
        self.GEMINI_TIMEOUT = int(Env.get("GEMINI_TIMEOUT", 30))

        # ========== SESSION ==========
        self.SESSION_TIMEOUT_MINUTES = int(Env.get("SESSION_TIMEOUT_MINUTES", 30))
        self.MAX_HISTORY_MESSAGES = int(Env.get("MAX_HISTORY_MESSAGES", 50))

        # ========== MONITORING ==========
        self.ENABLE_METRICS = Env.get("ENABLE_METRICS", "True").lower() == "true"
        self.ENABLE_TRACING = Env.get("ENABLE_TRACING", "True").lower() == "true"

        # ========== LOGGING ==========
        self.LOG_LEVEL = Env.get("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = Env.get(
        "LOG_FORMAT", 
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    def is_production(self) -> bool:
        """Determine if the app is running in production mode."""
        return not self.DEBUG


APP_SETTINGS = AppSettings()
