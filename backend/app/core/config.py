from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # Async driver is required by create_async_engine.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:YOUR_PASSWORD@YOUR_SUPABASE_HOST:6543/postgres"

    VECTOR_STORE_HOST: Optional[str] = "localhost"
    VECTOR_STORE_PORT: int = 6333
    VECTOR_STORE_API_KEY: Optional[str] = None

    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key"

    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "tutorrag_chunks"

    SUPABASE_URL: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None

    PLATFORM_LLM_PROVIDER: str = "google_ai"
    PLATFORM_LLM_API_KEY: Optional[str] = None
    PLATFORM_LLM_BASE_URL: Optional[str] = None
    PLATFORM_LLM_MODEL: str = "gemma-4-31b-it"

    AUTO_CREATE_TABLES: bool = False

    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL")
    @classmethod
    def _validate_async_database_url(cls, value: str) -> str:
        url = (value or "").strip()
        allowed_prefixes = (
            "postgresql+asyncpg://",
            "sqlite+aiosqlite://",
            "mysql+aiomysql://",
        )
        if not any(url.startswith(prefix) for prefix in allowed_prefixes):
            raise ValueError(
                "DATABASE_URL must use an async SQLAlchemy driver such as "
                "postgresql+asyncpg://, sqlite+aiosqlite://, or mysql+aiomysql://"
            )
        return url

    @field_validator("SUPABASE_URL", mode="before")
    @classmethod
    def _normalize_supabase_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        url = str(value).strip()
        if not url:
            return None

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        return url.rstrip("/")

    def get_cors_origins(self) -> list[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()
        if not raw:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()