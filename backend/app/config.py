"""TRSM Backend configuration settings with resilient fallback."""

import os
from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",
        )

        HOST: str = "127.0.0.1"
        PORT: int = 8000
        ENVIRONMENT: str = "development"
        LOG_LEVEL: str = "INFO"
        DATABASE_PATH: str = "./trsm_runtime.db"
        CORS_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
        OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
        DEFAULT_MODEL: str = "llama3:8b"
        POLICY_VERSION: str = "1.0.0"

    settings = Settings()

except ImportError:
    # Graceful fallback when pydantic-settings is not yet installed
    class FallbackSettings:
        HOST: str = os.getenv("HOST", "127.0.0.1")
        PORT: int = int(os.getenv("PORT", "8000"))
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./trsm_runtime.db")
        CORS_ORIGINS: List[str] = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
        OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama3:8b")
        POLICY_VERSION: str = os.getenv("POLICY_VERSION", "1.0.0")

    settings = FallbackSettings()  # type: ignore
