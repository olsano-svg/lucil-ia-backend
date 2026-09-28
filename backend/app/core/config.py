from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_FILE = BASE_DIR / "lucil_personal.db"

class Settings(BaseSettings):
    # API Config
    PROJECT_NAME: str = "Lucil AI Backend"
    API_V1_STR: str = "/api/v1"
    
    # Security
    # MUST BE SET IN ENVIRONMENT VARIABLES FOR PRODUCTION!
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_OR_IT_WILL_FAIL" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 11520  # 8 days
    ALLOWED_ORIGINS: str = "" # Comma separated list of allowed origins, e.g. "https://lucil-ai.vercel.app,http://localhost:8081"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "delarosa00"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        default_local_origins = [
            "http://localhost:8081",
            "http://localhost:8082",
            "http://localhost:19006",
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8081",
            "http://127.0.0.1:8082",
            "https://lucileAI-app-2026.web.app",
            "https://lucileai-app-2026.web.app",
            "https://lucileAI-app-2026.firebaseapp.com",
            "https://lucileai-app-2026.firebaseapp.com",
            "https://lucile-ai.web.app",
            "https://lucile-ai.firebaseapp.com",
            "https://lucil-ia.web.app",
            "https://lucil-ia.firebaseapp.com",
            "https://lucile-ia.web.app",
            "https://lucile-ia.firebaseapp.com"
        ]
        origins = list(default_local_origins)
        if self.ALLOWED_ORIGINS and self.ALLOWED_ORIGINS.strip():
            parsed = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
            for p in parsed:
                if p not in origins:
                    origins.append(p)
        return origins
    
    # Database - Defaulting to SQLite for personal use, compatible with Cloud PostgreSQL (Supabase/Neon/Render)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_FILE.as_posix()}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    # AI Providers Configuration (Default to Local / Private AI)
    DEFAULT_LLM_PROVIDER: str = "local"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LOCAL_MODEL_NAME: str = "qwen2.5:14b"
    LOCAL_CONTEXT_WINDOW: int = 32768
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Vector DB / Local RAG Configuration
    VECTOR_DB_DIR: str = "E:/lucil_vector_db"
    LOCAL_EMBEDDING_MODEL: str = "nomic-embed-text"

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")

settings = Settings()
