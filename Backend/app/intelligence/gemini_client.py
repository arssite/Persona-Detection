from __future__ import annotations

from __future__ import annotations

from google import genai

from app.core.config import get_settings


def get_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. Create Backend/.env (see .env.example) "
            "or set GEMINI_API_KEY in your environment."
        )

    # Key loaded from env; never hardcode.
    return genai.Client(api_key=settings.gemini_api_key)
