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

    result = await generate_meeting_intel(parsed)
    return result
