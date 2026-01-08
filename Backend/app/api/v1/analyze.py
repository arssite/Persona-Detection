from fastapi import APIRouter, HTTPException

from app.core.email import parse_email
from app.intelligence.generate import generate_meeting_intel
from app.schemas.meeting_intel import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    parsed = parse_email(req.email)
    if not parsed.is_valid:
        raise HTTPException(status_code=400, detail="Invalid corporate email")

    try:
        result = await generate_meeting_intel(parsed)
        return result
    except RuntimeError as e:
        msg = str(e)
        if msg.startswith("ANALYZE_LLM_RATE_LIMIT"):
            # msg format: ANALYZE_LLM_RATE_LIMIT:<seconds>
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
                    "The AI generation quota/rate-limit was reached. "
                    "Please wait briefly and retry."
                    + (f" (retry_after={retry_s}s)" if retry_s else "")
                ),
                headers=headers,
            )
        raise
