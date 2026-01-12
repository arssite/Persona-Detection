from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Keep optional to allow app import/startup without secrets configured.
    # Endpoints that need it should error clearly.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    
    # Groq configuration (faster, better free tier)
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"  # Best model for complex reasoning
    llm_provider: str = "groq"  # "gemini" or "groq"


@lru_cache
def get_settings() -> Settings:
    return Settings()
