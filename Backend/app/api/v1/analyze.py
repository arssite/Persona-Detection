from fastapi import APIRouter, HTTPException

from app.core.email import parse_email
from app.intelligence.generate import generate_meeting_intel
from app.schemas.meeting_intel import AnalyzeRequest, AnalyzeResponse

router = APIRouter(tags=["analyze"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    # Path C: support name+company mode
    if req.email:
        # Mode 1: Email (current)
        parsed = parse_email(req.email)
        if not parsed.is_valid:
            raise HTTPException(status_code=400, detail="Invalid corporate email")
    elif req.name and req.company:
        # Mode 2: Name + Company (Path C)
        from app.core.company_resolver import resolve_company_domain
        from app.core.email import ParsedEmail
        
        # Resolve company to domain
        domain_info = await resolve_company_domain(req.company)
        domain = domain_info.get('domain')
        
        # Create a pseudo-ParsedEmail for name+company mode
        synthetic_email = f"{req.name.first.lower()}.{req.name.last.lower()}@{domain}"
        parsed = ParsedEmail(
            raw=synthetic_email,
            is_valid=True,
            local_part=f"{req.name.first.lower()}.{req.name.last.lower()}",
            domain=domain,
            guessed_first_name=req.name.first,
            guessed_last_name=req.name.last,
        )
    else:
        raise HTTPException(status_code=400, detail="Must provide: email OR (name + company)")

    try:
        result = await generate_meeting_intel(
            parsed,
            linkedin_url=req.linkedin_url,
            github_username=req.github_username,
            allow_discovery=req.allow_discovery,
            instagram_url=req.instagram_url,
            x_url=req.x_url,
            medium_url=req.medium_url,
            other_urls=req.other_urls,
        )
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
