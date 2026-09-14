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
    CORS_ORIGINS: list[str] = ["*"] # Configure for production
    
    # Database - Defaulting to SQLite for personal use (no Docker required)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DB_FILE.as_posix()}"
    
    # AI Providers Configuration (Default to Local / Private AI)
    DEFAULT_LLM_PROVIDER: str = "local"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LOCAL_MODEL_NAME: str = "qwen2.5:14b"
    LOCAL_CONTEXT_WINDOW: int = 32768
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Vector DB / Local RAG Configuration
    VECTOR_DB_DIR: str = "E:/lucil_vector_db"
    LOCAL_EMBEDDING_MODEL: str = "nomic-embed-text"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
