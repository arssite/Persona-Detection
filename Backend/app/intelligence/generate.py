from __future__ import annotations

import json
from pydantic import ValidationError

from app.core.email import ParsedEmail
from app.schemas.meeting_intel import (
    AnalyzeResponse,
    Confidence,
    Recommendations,
    StudyOfPerson,
    GitHubProfile,
    CompanyProfile,
    EmailOpeners,
)
from app.intelligence.defaults import coalesce_list, coalesce_str, coalesce_dict
from app.intelligence.json_guard import try_parse_json
from app.core.confidence import fallback_confidence
from app.intelligence.gemini_client import get_client
from app.core.config import get_settings
from app.core.llm_errors import is_rate_limited_error, parse_retry_after_seconds
from app.scraping.linkedin_snippet import fetch_linkedin_snippet


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
Return JSON with keys:
- confidence: {{label, rationale}}
- company_confidence (optional): {{label, rationale}}
- person_confidence (optional): {{label, rationale}}
- one_minute_brief (string)
- questions_to_ask (array of strings)
- email_openers: {{formal, warm, technical}}
- red_flags (array of strings)
- company_profile: {{summary, likely_products_services, hiring_signals, recent_public_mentions}}
- study_of_person
- recommendations
- evidence (array of {{source, snippet, url}})

Rules:
- If unknown, return the string "unknown" (not null).
"""


# Simple demo cache (in-memory)
from app.core.cache import TTLCache

_RESULT_CACHE: TTLCache[AnalyzeResponse] = TTLCache(ttl_s=300.0, max_items=256)


async def generate_meeting_intel(
    parsed: ParsedEmail,
    force_refresh: bool = False,
    linkedin_url: str | None = None,
    github_username: str | None = None,
    allow_discovery: bool = True,
    instagram_url: str | None = None,
    x_url: str | None = None,
    medium_url: str | None = None,
    other_urls: list[str] | None = None,
) -> AnalyzeResponse:
    # MVP v0: collect lightweight public signals via web search.
    from app.search.ddg import ddg_search, results_to_evidence

    settings = get_settings()

    cache_key = parsed.raw.lower().strip()
    cached = _RESULT_CACHE.get(cache_key)
    if cached is not None and not force_refresh:
        return cached

    collected_evidence: list[dict] = []

    # Social enrichment (snippets-only). We treat user-provided URLs as higher weight evidence,
    # and (optionally) discover additional candidates via search.
    social_candidates = []
    social_selected = []
    try:
        from app.intelligence.social_discovery import discover_social_candidates, fetch_user_profile_snippet

        selected_urls: list[tuple[str, str]] = []
        if instagram_url:
            selected_urls.append(("instagram", instagram_url))
        if x_url:
            selected_urls.append(("x", x_url))
        if medium_url:
            selected_urls.append(("medium", medium_url))
        if other_urls:
            for u in other_urls:
                if u:
                    selected_urls.append(("website", u))

        for platform, url in selected_urls:
            title, snippet = await fetch_user_profile_snippet(url)
            social_selected.append(
                {
                    "platform": platform,
                    "url": url,
                    "title": title,
                    "snippet": snippet,
                    "confidence": 1.0,
                    "source": "user",
                }
            )
            collected_evidence.append(
                {
                    "source": "social_user",
                    "snippet": (snippet or title or f"User-provided {platform} profile").strip(),
                    "url": url,
                }
            )

        if allow_discovery:
            name_guess = " ".join([p for p in [parsed.guessed_first_name, parsed.guessed_last_name] if p]) or None
            # company name hint: best-effort from domain.
            company_hint = parsed.domain.split(".")[0] if parsed.domain else None
            discovered = await discover_social_candidates(
                name_guess=name_guess,
                company_domain=parsed.domain,
                company_name_hint=company_hint,
                max_per_platform=3,
            )
            social_candidates = [c.__dict__ for c in discovered]
            # Add discovered candidates as low/medium weight evidence too.
            for c in discovered:
                collected_evidence.append(
                    {
                        "source": "social_discovered",
                        "snippet": (c.snippet or c.title or f"Discovered {c.platform} profile").strip(),
                        "url": c.url,
                    }
                )
    except Exception:
        # Non-fatal; proceed without social enrichment
        social_candidates = []
        social_selected = []

    # Optional: LinkedIn enrichment (Path A)
    if linkedin_url:
        try:
            linkedin_data = await fetch_linkedin_snippet(linkedin_url)
            if linkedin_data:
                headline = linkedin_data.get('headline', '')
                snippet = linkedin_data.get('snippet', '')
                role = linkedin_data.get('role', '')
                company = linkedin_data.get('company', '')
                
                # Build rich evidence snippet
                parts = []
                if headline:
                    parts.append(f"LinkedIn: {headline}")
                if role and company:
                    parts.append(f"Role: {role} at {company}")
                elif snippet:
                    parts.append(snippet)
                
                collected_evidence.append({
                    'source': 'linkedin_snippet',
                    'snippet': ' | '.join(parts) if parts else 'LinkedIn profile found',
                    'url': linkedin_data.get('source_url'),
                })
        except Exception:
            pass  # Skip if LinkedIn snippet fetch fails
    
    # Optional: GitHub enrichment (Path A, direct)
    if github_username:
        try:
            from app.enrichment.github import fetch_github_profile
            gh_data = await fetch_github_profile(github_username)
            if gh_data:
                # Format GitHub profile as evidence
                bio = gh_data.get('bio', '')
                company = gh_data.get('company', '')
                location = gh_data.get('location', '')
                top_langs = gh_data.get('top_languages', [])[:5]
                
                parts = []
                parts.append(f"GitHub: @{github_username}")
                if bio:
                    parts.append(f"Bio: {bio}")
                if company:
                    parts.append(f"Company: {company}")
                if location:
                    parts.append(f"Location: {location}")
                if top_langs:
                    parts.append(f"Languages: {', '.join(top_langs)}")
                
                collected_evidence.append({
                    'source': 'github_api_direct',
                    'snippet': ' | '.join(parts),
                    'url': f"https://github.com/{github_username}",
                })
        except Exception:
            pass  # Skip if GitHub API fails
    
    if parsed.domain:
        from app.scraping.company_site import scrape_company_site, pages_to_evidence
        from app.intelligence.evidence import dedupe_and_rank

        # 1) Company-level signals (search + company website)
        company_q = f"{parsed.domain} about company"
        company_results = await ddg_search(company_q, max_results=6)
        collected_evidence.extend(results_to_evidence(company_results, source="ddg_company"))

        pages = await scrape_company_site(parsed.domain, max_pages=8)
        collected_evidence.extend(pages_to_evidence(pages))

        # 2) News signals (press, funding, announcements)
        news_q = f"{parsed.domain} funding OR raises OR press release"
        news_results = await ddg_search(news_q, max_results=6)
        collected_evidence.extend(results_to_evidence(news_results, source="ddg_news"))

        # 3) Hiring signals (careers + job platforms)
        hiring_q = f"site:{parsed.domain} careers OR jobs OR hiring"
        hiring_results = await ddg_search(hiring_q, max_results=6)
        collected_evidence.extend(results_to_evidence(hiring_results, source="ddg_hiring"))

        # 4) Person-level signals (best-effort if we have a name guess)
        name_guess = " ".join([p for p in [parsed.guessed_first_name, parsed.guessed_last_name] if p]) or None
        if name_guess:
            person_q = f"{name_guess} {parsed.domain}"
            person_results = await ddg_search(person_q, max_results=6)
            collected_evidence.extend(results_to_evidence(person_results, source="ddg_person"))

            # GitHub hints
            gh_q = f"{name_guess} github"
            gh_results = await ddg_search(gh_q, max_results=4)
            collected_evidence.extend(results_to_evidence(gh_results, source="ddg_github"))

        # Final: dedupe + rank
        collected_evidence = dedupe_and_rank(collected_evidence, max_items=22)

    # Optional GitHub enrichment (public API) if we can confidently detect a profile URL
    github_profile = None
    try:
        from app.enrichment.github import extract_github_user, fetch_github_profile

        gh_users: list[str] = []
        for e in collected_evidence:
            if str(e.get("source")) not in {"ddg_github"}:
                continue
            u = extract_github_user(str(e.get("url") or ""))
            if u:
                gh_users.append(u)

        # Pick the first candidate for MVP
        if gh_users:
            gh = await fetch_github_profile(gh_users[0])
            if gh:
                github_profile = gh
    except Exception:
        github_profile = None

    client = get_client()
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=_prompt(parsed, collected_evidence),
            config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
        )
    except Exception as e:
        # Bubble up a stable sentinel so the API layer can map it to HTTP 429.
        if is_rate_limited_error(e):
            retry_s = parse_retry_after_seconds(e)
            raise RuntimeError(f"ANALYZE_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
        raise

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
        try:
            response2 = client.models.generate_content(
                model=settings.gemini_model,
                contents=repair_prompt,
                config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
            )
        except Exception as e:
            if is_rate_limited_error(e):
                retry_s = parse_retry_after_seconds(e)
                raise RuntimeError(f"ANALYZE_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
            raise
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

    sop = coalesce_dict(data.get("study_of_person"))
    recs = coalesce_dict(data.get("recommendations"))

    one_minute_brief = data.get("one_minute_brief") or "unknown"
    questions_to_ask = data.get("questions_to_ask") or [
        "What are your top priorities for this role in the next 30–60 days?",
        "What does success look like after the first 90 days?",
        "Which skills/traits differentiate strong candidates in your team?",
    ]
    email_openers = data.get("email_openers")
    red_flags = data.get("red_flags") or [
        "Avoid assuming the person’s exact title/seniority without confirmation.",
        "Avoid claiming information beyond the provided public evidence.",
    ]
    company_profile = coalesce_dict(data.get("company_profile"))
    # Coerce list-like fields inside company_profile
    if company_profile:
        company_profile["likely_products_services"] = coalesce_list(company_profile.get("likely_products_services"))
        company_profile["hiring_signals"] = coalesce_list(company_profile.get("hiring_signals"))
        company_profile["recent_public_mentions"] = coalesce_list(company_profile.get("recent_public_mentions"))
        company_profile["summary"] = coalesce_str(company_profile.get("summary"))

    company_conf = data.get("company_confidence")
    person_conf = data.get("person_confidence")

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
            social_candidates=social_candidates,
            social_selected=social_selected,
            confidence=Confidence(**confidence),
            company_confidence=Confidence(**_normalize_confidence(company_conf)) if isinstance(company_conf, dict) else None,
            person_confidence=Confidence(**_normalize_confidence(person_conf)) if isinstance(person_conf, dict) else None,
            one_minute_brief=coalesce_str(one_minute_brief),
            questions_to_ask=coalesce_list(questions_to_ask),
            email_openers=EmailOpeners(**email_openers) if isinstance(email_openers, dict) else EmailOpeners(formal="unknown", warm="unknown", technical="unknown"),
            red_flags=coalesce_list(red_flags),
            company_profile=CompanyProfile(**company_profile) if company_profile else None,
            study_of_person=StudyOfPerson(**sop),
            recommendations=Recommendations(**recs),
            evidence=evidence,
            github_profile=GitHubProfile(**github_profile.__dict__) if github_profile else None,
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
        try:
            response3 = client.models.generate_content(
                model=settings.gemini_model,
                contents=repair_prompt,
                config={"system_instruction": _SYSTEM, "response_mime_type": "application/json"},
            )
        except Exception as e:
            if is_rate_limited_error(e):
                retry_s = parse_retry_after_seconds(e)
                raise RuntimeError(f"ANALYZE_LLM_RATE_LIMIT:{retry_s if retry_s is not None else ''}") from e
            raise
        raw3 = getattr(response3, "text", None) or "{}"
        data3, _ = try_parse_json(raw3)
        if not isinstance(data3, dict):
            data3 = {}

        confidence3 = _normalize_confidence(data3.get("confidence"))
        sop3 = coalesce_dict(data3.get("study_of_person"))
        recs3 = coalesce_dict(data3.get("recommendations"))
        evidence3 = data3.get("evidence")
        if not isinstance(evidence3, list) or not evidence3:
            evidence3 = collected_evidence

        company_profile3 = coalesce_dict(data3.get("company_profile"))
        if company_profile3:
            company_profile3["likely_products_services"] = coalesce_list(company_profile3.get("likely_products_services"))
            company_profile3["hiring_signals"] = coalesce_list(company_profile3.get("hiring_signals"))
            company_profile3["recent_public_mentions"] = coalesce_list(company_profile3.get("recent_public_mentions"))
            company_profile3["summary"] = coalesce_str(company_profile3.get("summary"))

        # If still invalid, this will raise (surfacing a clear 500) but should be rare.
        return AnalyzeResponse(
            input_email=parsed.raw,
            person_name_guess=name_guess,
            company_domain=parsed.domain,
            social_candidates=social_candidates,
            social_selected=social_selected,
            confidence=Confidence(**confidence3),
            company_confidence=Confidence(**_normalize_confidence(data3.get("company_confidence"))) if isinstance(data3.get("company_confidence"), dict) else None,
            person_confidence=Confidence(**_normalize_confidence(data3.get("person_confidence"))) if isinstance(data3.get("person_confidence"), dict) else None,
            one_minute_brief=coalesce_str(data3.get("one_minute_brief")),
            questions_to_ask=coalesce_list(data3.get("questions_to_ask")),
            email_openers=EmailOpeners(**data3.get("email_openers")) if isinstance(data3.get("email_openers"), dict) else EmailOpeners(formal="unknown", warm="unknown", technical="unknown"),
            red_flags=coalesce_list(data3.get("red_flags")),
            company_profile=CompanyProfile(**company_profile3) if company_profile3 else None,
            study_of_person=StudyOfPerson(**sop3),
            recommendations=Recommendations(**recs3),
            evidence=evidence3,
            github_profile=GitHubProfile(**github_profile.__dict__) if github_profile else None,
        )
