import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


SECRET_FILE = Path(__file__).parent.parent / ".secret_key"


def _load_or_create_secret_key() -> str:
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text().strip()
    key = secrets.token_urlsafe(64)
    SECRET_FILE.write_text(key)
    return key


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Multi-Agent AI Customer Support"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    API_PREFIX: str = "/api/v1"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "multi_agent_ai"

    CORS_ORIGINS: str = "http://localhost:3000"

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    AI_PRIMARY_MODEL: str = "gemini-2.5-flash"
    AI_FALLBACK_MODEL: str = "llama-3.3-70b-versatile"
    AI_FALLBACK_PROVIDER: str = "groq"

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 10
    TOP_K_RERANK: int = 5

    TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 2048

    RATE_LIMIT_PER_MINUTE: int = 60

    LOG_LEVEL: str = "INFO"

    @property
    def secret_key(self) -> str:
        if self.SECRET_KEY:
            return self.SECRET_KEY
        return _load_or_create_secret_key()

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
