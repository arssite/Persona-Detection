from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.schemas.assistant import (
    AssistantBootstrapRequest,
    AssistantBootstrapResponse,
    AssistantChatRequest,
    AssistantChatResponse,
)
from app.intelligence.assistant import bootstrap as assistant_bootstrap
from app.intelligence.assistant import chat as assistant_chat

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assistant"])


@router.post("/assistant/bootstrap", response_model=AssistantBootstrapResponse)
async def bootstrap(req: AssistantBootstrapRequest) -> AssistantBootstrapResponse:
    try:
        return await assistant_bootstrap(
            email=req.email,
            agenda=req.agenda,
            refresh_public_signals=req.refresh_public_signals,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Avoid leaking vendor/model details to the client.
        # But do log the full exception server-side with a correlation id.
        error_id = str(uuid.uuid4())
        logger.exception("assistant.bootstrap failed error_id=%s", error_id)

        msg = str(e)

        if "GEMINI_API_KEY" in msg or "not configured" in msg.lower():
            raise HTTPException(
                status_code=400,
                detail=(
                    "Mr Assistant needs an AI key configured on the backend. "
                    "Set GEMINI_API_KEY in Backend/.env and restart the server. "
                    f"(error_id={error_id})"
                ),
            )

        if msg.startswith("ASSISTANT_LLM_RATE_LIMIT") or msg.startswith("ANALYZE_LLM_RATE_LIMIT"):
            retry_s = None
            parts = msg.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                try:
                    retry_s = int(float(parts[1].strip()))
                except Exception:
                    retry_s = None
            headers = {"Retry-After": str(retry_s)} if retry_s else None
            raise HTTPException(
                status_code=429,
                detail=(
                    "Mr Assistant hit an AI quota/rate-limit. Please wait briefly and retry."
                    + (f" (retry_after={retry_s}s)" if retry_s else "")
                    + f" (error_id={error_id})"
                ),
                headers=headers,
            )

        if msg == "ASSISTANT_LLM_UNAVAILABLE" or "UNAVAILABLE" in msg or "503" in msg or "overloaded" in msg.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Mr Assistant is temporarily busy generating results. "
                    "Please retry in a few seconds (or proceed with Analysis only). "
                    f"(error_id={error_id})"
                ),
            )

        raise HTTPException(status_code=500, detail=f"Assistant bootstrap failed (error_id={error_id})")


@router.post("/assistant/chat", response_model=AssistantChatResponse)
async def chat(req: AssistantChatRequest) -> AssistantChatResponse:
    try:
        return await assistant_chat(
            session_id=req.session_id,
            message=req.message,
            confirm_refresh=req.confirm_refresh,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        error_id = str(uuid.uuid4())
        logger.exception("assistant.chat failed error_id=%s", error_id)

        msg = str(e)

        if "GEMINI_API_KEY" in msg or "not configured" in msg.lower():
            raise HTTPException(
                status_code=400,
                detail=(
                    "Mr Assistant needs an AI key configured on the backend. "
                    "Set GEMINI_API_KEY in Backend/.env and restart the server. "
                    f"(error_id={error_id})"
                ),
            )

        if msg.startswith("ASSISTANT_LLM_RATE_LIMIT") or msg.startswith("ANALYZE_LLM_RATE_LIMIT"):
            retry_s = None
            parts = msg.split(":", 1)
            if len(parts) == 2 and parts[1].strip():
                try:
                    retry_s = int(float(parts[1].strip()))
                except Exception:
                    retry_s = None
            headers = {"Retry-After": str(retry_s)} if retry_s else None
            raise HTTPException(
                status_code=429,
                detail=(
                    "Mr Assistant hit an AI quota/rate-limit. Please wait briefly and retry."
                    + (f" (retry_after={retry_s}s)" if retry_s else "")
                    + f" (error_id={error_id})"
                ),
                headers=headers,
            )

        if msg == "ASSISTANT_LLM_UNAVAILABLE" or "UNAVAILABLE" in msg or "503" in msg or "overloaded" in msg.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Mr Assistant is temporarily busy generating results. "
                    "Please retry in a few seconds. "
                    f"(error_id={error_id})"
                ),
            )

        raise HTTPException(status_code=500, detail=f"Assistant chat failed (error_id={error_id})")
