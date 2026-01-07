from __future__ import annotations

import json
from pydantic import ValidationError

from app.core.email import ParsedEmail
from app.schemas.meeting_intel import (
    AnalyzeResponse,
    Confidence,
    Recommendations,
    StudyOfPerson,
)
from app.intelligence.json_guard import try_parse_json
from app.core.confidence import fallback_confidence
from app.intelligence.gemini_client import get_client
from app.core.config import get_settings


_SYSTEM = """You are an AI assistant that creates meeting intelligence from public web signals.

Rules:
- Use probabilistic language; never claim certainty.
- Output MUST be valid JSON only (no markdown, no commentary).
- Follow the provided schema keys exactly.
- confidence MUST be an object with keys: label (low|medium|high) and rationale (string).
- recommendations MUST contain arrays for: dos, donts, connecting_points, suggested_agenda (can be empty).
"""


def _prompt(parsed: ParsedEmail, evidence: list[dict]) -> str:
    name_guess = " ".join([p for p in [parsed.guessed_first_name, parsed.guessed_last_name] if p]) or None
    bullets = "\n".join([f"- ({e.get('source')}) {e.get('snippet')} [{e.get('url','')}]" for e in evidence])
    if not bullets.strip():
        bullets = "- None"

    return f"""Input:
- email: {parsed.raw}
- name_guess: {name_guess}
- company_domain: {parsed.domain}

Evidence (public web signals):
{bullets}

Task:
Return JSON with keys: confidence, study_of_person, recommendations, evidence.
- Evidence should be a list of items with: source, snippet, url (optional)
"""


# Simple demo cache (in-memory)
from app.core.cache import TTLCache

_RESULT_CACHE: TTLCache[AnalyzeResponse] = TTLCache(ttl_s=300.0, max_items=256)


async def generate_meeting_intel(parsed: ParsedEmail) -> AnalyzeResponse:
    # MVP v0: collect lightweight public signals via web search.
    from app.search.ddg import ddg_search, results_to_evidence

    settings = get_settings()

    cache_key = parsed.raw.lower().strip()
    cached = _RESULT_CACHE.get(cache_key)
    if cached is not None:
        return cached

    collected_evidence: list[dict] = []
    if parsed.domain:
        # Company-level signals (search + company website)
        company_q = f"{parsed.domain} about company"
        company_results = await ddg_search(company_q, max_results=5)
        collected_evidence.extend(results_to_evidence(company_results, source="ddg_company"))

        from app.scraping.company_site import scrape_company_site, pages_to_evidence

        pages = await scrape_company_site(parsed.domain, max_pages=4)
        collected_evidence.extend(pages_to_evidence(pages))

        # Person-level signals (best-effort if we have a name guess)
        name_guess = " ".join([p for p in [parsed.guessed_first_name, parsed.guessed_last_name] if p]) or None
        if name_guess:
            person_q = f"{name_guess} {parsed.domain}"
            person_results = await ddg_search(person_q, max_results=5)
            collected_evidence.extend(results_to_evidence(person_results, source="ddg_person"))

    client = get_client()
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=_prompt(parsed, collected_evidence),
        config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
    )

    # google-genai may return response.text as JSON when response_mime_type is set.
    raw = getattr(response, "text", None) or "{}"

    data, parse_err = try_parse_json(raw)
    if data is None:
        # Retry once with a stricter repair instruction.
        repair_prompt = (
            _prompt(parsed, collected_evidence)
            + "\n\nThe previous response was not valid JSON (error: "
            + str(parse_err)
            + "). Return ONLY valid JSON matching the required schema."
        )
        response2 = client.models.generate_content(
            model=settings.gemini_model,
            contents=repair_prompt,
            config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
        )
        raw2 = getattr(response2, "text", None) or "{}"
        data, _ = try_parse_json(raw2)

    if data is None:
        data = {}

    def _normalize_confidence(obj: object) -> dict:
        # Gemini sometimes returns different key names. Make it resilient.
        if not isinstance(obj, dict):
            return {"label": "low", "rationale": "No confidence returned; defaulting to low."}

        # Accept a few common variants.
        label = obj.get("label") or obj.get("confidence") or obj.get("level")
        rationale = obj.get("rationale") or obj.get("reason") or obj.get("explanation")

        # If Gemini returns a numeric score, map it.
        score = obj.get("score") or obj.get("overall_confidence_score")
        if label is None and isinstance(score, (int, float)):
            if score >= 0.75:
                label = "high"
            elif score >= 0.45:
                label = "medium"
            else:
                label = "low"

        if label is None:
            label = "low"
        if rationale is None:
            rationale = "Confidence keys did not match schema; defaulted safely."

        # Coerce label into expected values
        label_s = str(label).lower().strip()
        if label_s not in {"low", "medium", "high"}:
            label_s = "low"

        return {"label": label_s, "rationale": str(rationale)}

    # Fallback-safe defaults
    confidence = _normalize_confidence(data.get("confidence"))
    if confidence.get("label") == "low" and "default" in confidence.get("rationale", "").lower():
        confidence = fallback_confidence(collected_evidence)

    sop = data.get("study_of_person") or {}
    recs = data.get("recommendations") or {}

    # Prefer model-produced evidence if it matches schema; otherwise fall back to collected evidence.
    evidence = data.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        evidence = collected_evidence

    name_guess = " ".join([p for p in [parsed.guessed_first_name, parsed.guessed_last_name] if p]) or None

    # Validate/repair full response once if needed
    try:
        result = AnalyzeResponse(
            input_email=parsed.raw,
            person_name_guess=name_guess,
            company_domain=parsed.domain,
            confidence=Confidence(**confidence),
            study_of_person=StudyOfPerson(**sop),
            recommendations=Recommendations(**recs),
            evidence=evidence,
        )
        _RESULT_CACHE.set(cache_key, result)
        return result
    except ValidationError as ve:
        repair_prompt = (
            _prompt(parsed, collected_evidence)
            + "\n\nThe JSON did not validate against the schema. Fix ONLY the JSON so it validates. "
            + "Validation error: "
            + str(ve)
        )
        response3 = client.models.generate_content(
            model=settings.gemini_model,
            contents=repair_prompt,
            config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
        )
        raw3 = getattr(response3, "text", None) or "{}"
        data3, _ = try_parse_json(raw3)
        if not isinstance(data3, dict):
            data3 = {}

        confidence3 = _normalize_confidence(data3.get("confidence"))
        sop3 = data3.get("study_of_person") or {}
        recs3 = data3.get("recommendations") or {}
        evidence3 = data3.get("evidence")
        if not isinstance(evidence3, list) or not evidence3:
            evidence3 = collected_evidence

        # If still invalid, this will raise (surfacing a clear 500) but should be rare.
        return AnalyzeResponse(
            input_email=parsed.raw,
            person_name_guess=name_guess,
            company_domain=parsed.domain,
            confidence=Confidence(**confidence3),
            study_of_person=StudyOfPerson(**sop3),
            recommendations=Recommendations(**recs3),
            evidence=evidence3,
        )
