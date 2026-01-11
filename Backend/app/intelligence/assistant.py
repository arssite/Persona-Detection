from __future__ import annotations

import json
import re
from typing import Any

from app.core.email import parse_email
from app.core.config import get_settings
from app.core.llm_errors import is_rate_limited_error, parse_retry_after_seconds
from app.intelligence.gemini_client import get_client
from app.intelligence.json_guard import try_parse_json
from app.schemas.assistant import (
    AssistantAgenda,
    AssistantBootstrapResponse,
    AssistantChatResponse,
)
from app.schemas.meeting_intel import AnalyzeResponse, EvidenceItem
from app.core.assistant_store import append_chat, get_session, new_session


_ASSISTANT_NAME = "Mr Assistant"

_SYSTEM = """You are Mr Assistant, a recruiter/sales meeting-prep RAG agent.

You help the user prepare to pitch/present to a person inferred from a corporate email.

Rules (critical):
- Do NOT claim certainty. Use probabilistic language.
- Do NOT invent facts about the person or company.
- Ground company/person statements in the provided evidence snippets; add citations (URLs) when possible.
- If the user asks something not supported by evidence, say what is unknown and suggest refreshing public signals.
- Do NOT mention model/vendor/provider names. If asked, say: "This MVP uses a RAG-style agent over public web signals." 
- Output MUST be valid JSON only.
"""


def _evidence_bullets(evidence: list[dict[str, Any]]) -> str:
    bullets = "\n".join([f"- ({e.get('source')}) {e.get('snippet')} [{e.get('url','')}]" for e in evidence[:22]])
    return bullets if bullets.strip() else "- None"


def _pick_citations(evidence: list[dict[str, Any]], max_items: int = 6) -> list[EvidenceItem]:
    out: list[EvidenceItem] = []
    seen: set[str] = set()
    for e in evidence:
        url = (e.get("url") or "")
        key = f"{e.get('source')}::{url}::{(e.get('snippet') or '')[:80]}"
        if key in seen:
            continue
        seen.add(key)
        out.append(EvidenceItem(source=str(e.get("source") or "unknown"), snippet=str(e.get("snippet") or ""), url=url or None))
        if len(out) >= max_items:
            break
    return out


def _refresh_recommended(message: str) -> tuple[bool, str | None]:
    m = message.lower()
    triggers = [
        "latest",
        "recent",
        "today",
        "yesterday",
        "this week",
        "now",
        "current",
        "still",
        "confirm",
        "verify",
        "updated",
        "funding",
        "press release",
        "news",
        "layoff",
    ]
    if any(t in m for t in triggers):
        return True, "Your question sounds time-sensitive. I can refresh public web signals (search + company-site crawl) before answering."
    return False, None


async def bootstrap(*, email: str, agenda: AssistantAgenda, refresh_public_signals: bool) -> AssistantBootstrapResponse:
    parsed = parse_email(email)
    if not parsed.is_valid:
        raise ValueError("Invalid corporate email")

    # Reuse existing pipeline to create a grounded snapshot.
    from app.intelligence.generate import generate_meeting_intel

    snapshot: AnalyzeResponse = await generate_meeting_intel(
        parsed,
        force_refresh=refresh_public_signals,
        allow_discovery=True,
    )  # type: ignore[arg-type]

    # Create session
    session = new_session(
        email=email.strip(),
        agenda=agenda.model_dump(),
        analyze_snapshot=snapshot.model_dump(),
    )

    # Ask model for starter questions + pitch plan.
    evidence_dicts = [e.model_dump() if hasattr(e, "model_dump") else dict(e) for e in snapshot.evidence]

    prompt = f"""Context:
- Target email: {snapshot.input_email}
- Person name guess: {snapshot.person_name_guess}
- Company domain: {snapshot.company_domain}

User agenda:
- pitch: {agenda.pitch}
- goal: {agenda.goal}
- meeting_type: {agenda.meeting_type}
- audience_context: {agenda.audience_context}
- constraints: {agenda.constraints}

Persona snapshot (AI-inferred):
- One-minute brief: {snapshot.one_minute_brief}
- Study of person: {json.dumps(snapshot.study_of_person.model_dump(), ensure_ascii=False)}

Evidence (public web signals):
{_evidence_bullets(evidence_dicts)}

Task:
Return JSON with keys:
- intro (string)
- starter_questions (array of 5 strings)
- pitch_openers (array of 3 strings)
- pitch_structure (array of 5-8 bullet strings)
- likely_objections (array of 4 strings)
- objection_responses (array of 4 strings)
- confidence (low|medium|high)

Rules:
- Keep it recruiter-friendly and action-oriented.
- If evidence is thin, lower confidence and say what you would verify next.
"""

    settings = get_settings()
    client = get_client()
    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
        )
    except Exception as e:
        msg = str(e)
        if is_rate_limited_error(e):
            retry_s = parse_retry_after_seconds(e)
            raise RuntimeError(f"ASSISTANT_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
        if "UNAVAILABLE" in msg or "503" in msg or "overloaded" in msg.lower():
            raise RuntimeError("ASSISTANT_LLM_UNAVAILABLE") from e
        raise

    raw = getattr(resp, "text", None) or "{}"
    data, err = try_parse_json(raw)
    if data is None:
        try:
            resp2 = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt + f"\n\nReturn ONLY valid JSON. Previous JSON error: {err}",
                config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
            )
        except Exception as e:
            msg = str(e)
            if is_rate_limited_error(e):
                retry_s = parse_retry_after_seconds(e)
                raise RuntimeError(f"ASSISTANT_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
            if "UNAVAILABLE" in msg or "503" in msg or "overloaded" in msg.lower():
                raise RuntimeError("ASSISTANT_LLM_UNAVAILABLE") from e
            raise
        data, _ = try_parse_json(getattr(resp2, "text", None) or "{}")
    if not isinstance(data, dict):
        data = {}

    append_chat(session.session_id, "system", f"bootstrap for {email}")

    return AssistantBootstrapResponse(
        session_id=session.session_id,
        assistant_name=_ASSISTANT_NAME,
        intro=str(data.get("intro") or "I’m Mr Assistant. Tell me what you’re pitching and I’ll help you tailor a confident, evidence-aware approach."),
        starter_questions=list(data.get("starter_questions") or [])[:5],
        pitch_openers=list(data.get("pitch_openers") or [])[:5],
        pitch_structure=list(data.get("pitch_structure") or [])[:10],
        likely_objections=list(data.get("likely_objections") or [])[:8],
        objection_responses=list(data.get("objection_responses") or [])[:8],
        confidence=str(data.get("confidence") or "medium").lower().strip(),
        citations=_pick_citations(evidence_dicts),
        analyze_snapshot=snapshot,
    )


async def chat(*, session_id: str, message: str, confirm_refresh: bool) -> AssistantChatResponse:
    s = get_session(session_id)
    if s is None:
        raise ValueError("Unknown/expired session. Please bootstrap again.")

    refresh_needed, refresh_reason = _refresh_recommended(message)
    if refresh_needed and not confirm_refresh:
        return AssistantChatResponse(
            session_id=session_id,
            assistant_name=_ASSISTANT_NAME,
            message=(
                "Your question sounds like it may require up-to-date public info. "
                "If you want, I can refresh public signals (search + company-site crawl) before answering. "
                "Confirm refresh to proceed, or ask a non-time-sensitive question."
            ),
            refresh_recommended=True,
            refresh_reason=refresh_reason,
            citations=_pick_citations(list(s.analyze_snapshot.get("evidence") or [])),
        )

    # Optionally refresh snapshot
    if refresh_needed and confirm_refresh:
        parsed = parse_email(s.email)
        from app.intelligence.generate import generate_meeting_intel

        snapshot = await generate_meeting_intel(
            parsed,
            force_refresh=True,
            allow_discovery=True,
        )  # type: ignore[arg-type]
        s.analyze_snapshot = snapshot.model_dump()

    agenda = s.agenda
    snapshot = s.analyze_snapshot
    evidence = list(snapshot.get("evidence") or [])

    # Build prompt
    evidence_bullets = _evidence_bullets(evidence)

    history = s.chat_history[-10:]
    history_text = "\n".join([f"{h.get('role')}: {h.get('content')}" for h in history])

    prompt = f"""You are continuing an assistant session.

User agenda:
{json.dumps(agenda, ensure_ascii=False)}

Persona snapshot:
{json.dumps({k: snapshot.get(k) for k in ['input_email','person_name_guess','company_domain','one_minute_brief','study_of_person','company_profile','recommendations']}, ensure_ascii=False)}

Evidence (public web signals):
{evidence_bullets}

Conversation so far (most recent last):
{history_text}

User message:
{message}

Task:
Return JSON with keys:
- message (string)
- follow_up_questions (array of up to 3 strings)
- confidence (low|medium|high)

Rules:
- If you cannot ground a factual claim, say it’s unknown and suggest what evidence would help.
- Include 0-3 follow-up questions if they help clarify user’s pitch.
"""

    settings = get_settings()
    client = get_client()

    try:
        resp = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
        )
    except Exception as e:
        msg = str(e)
        if is_rate_limited_error(e):
            retry_s = parse_retry_after_seconds(e)
            raise RuntimeError(f"ASSISTANT_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
        if "UNAVAILABLE" in msg or "503" in msg or "overloaded" in msg.lower():
            raise RuntimeError("ASSISTANT_LLM_UNAVAILABLE") from e
        raise

    raw = getattr(resp, "text", None) or "{}"
    data, err = try_parse_json(raw)
    if data is None:
        try:
            resp2 = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt + f"\n\nReturn ONLY valid JSON. Previous JSON error: {err}",
                config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
            )
        except Exception as e:
            msg = str(e)
            if is_rate_limited_error(e):
                retry_s = parse_retry_after_seconds(e)
                raise RuntimeError(f"ASSISTANT_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
            if "UNAVAILABLE" in msg or "503" in msg or "overloaded" in msg.lower():
                raise RuntimeError("ASSISTANT_LLM_UNAVAILABLE") from e
            raise
        data, _ = try_parse_json(getattr(resp2, "text", None) or "{}")
    if not isinstance(data, dict):
        data = {}

    append_chat(session_id, "user", message)
    append_chat(session_id, "assistant", str(data.get("message") or ""))

    # Simple citation selection: return top few evidence items.
    citations = _pick_citations(evidence)

    return AssistantChatResponse(
        session_id=session_id,
        assistant_name=_ASSISTANT_NAME,
        message=str(data.get("message") or ""),
        follow_up_questions=list(data.get("follow_up_questions") or [])[:3],
        refresh_recommended=False,
        refresh_reason=None,
        citations=citations,
    )
