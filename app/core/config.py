"""
Configuration management for the application settings.
Loads settings from environment variables or a .env file using pydantic-settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    Defaults are developer-friendly so the app can boot more easily in local mode.
    """

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./tutorrag.db"

    # Vector Store (Qdrant)
    VECTOR_STORE_HOST: str = "localhost"
    VECTOR_STORE_PORT: int = 6333
    VECTOR_STORE_API_KEY: Optional[str] = None

    # LLM Configuration (Default to local Ollama)
    LLM_API_KEY: str = "ollama" 
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "gemma4" 

    # General
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "dev-secret-key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """
    return Settings()


settings = get_settings()