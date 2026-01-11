from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.search.ddg import SearchResult, ddg_search


@dataclass(frozen=True)
class SocialCandidate:
    platform: str  # instagram|x|medium|website
    url: str
    title: str | None
    snippet: str | None
    confidence: float
    source: str  # discovered|user


_PLATFORM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("instagram", re.compile(r"^https?://(www\\.)?instagram\\.com/", re.I)),
    ("x", re.compile(r"^https?://(www\\.)?(x\\.com|twitter\\.com)/", re.I)),
    ("medium", re.compile(r"^https?://(www\\.)?medium\\.com/", re.I)),
]


def _normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _name_tokens(name_guess: str | None) -> list[str]:
    if not name_guess:
        return []
    tokens = re.split(r"[^a-zA-Z0-9]+", name_guess.lower())
    return [t for t in tokens if len(t) >= 2]


def _score_candidate(*, url: str, snippet: str, title: str, name_tokens: list[str], company_hints: list[str]) -> float:
    """Return confidence in [0,1] that this profile matches the person/company context.

    This is intentionally heuristic + conservative for MVP.
    """
    u = url.lower()
    text = f"{title} {snippet}".lower()

    score = 0.15  # base

    # Name tokens appearing in URL or snippet/title
    if name_tokens:
        hits = 0
        for t in name_tokens:
            if t in u or re.search(rf"\\b{re.escape(t)}\\b", text):
                hits += 1
        if hits >= 2:
            score += 0.45
        elif hits == 1:
            score += 0.25

    # Company/domain hints
    for h in company_hints:
        h_l = h.lower().strip()
        if not h_l:
            continue
        if h_l in u:
            score += 0.18
        elif re.search(rf"\\b{re.escape(h_l)}\\b", text):
            score += 0.25

    # Cap and floor
    if score < 0.0:
        score = 0.0
    if score > 1.0:
        score = 1.0
    return float(score)


def _platform_for_url(url: str) -> str | None:
    for platform, pat in _PLATFORM_PATTERNS:
        if pat.match(url):
            return platform
    return None


def _filter_results(results: Iterable[SearchResult]) -> list[SearchResult]:
    out: list[SearchResult] = []
    for r in results:
        if not r.url:
            continue
        platform = _platform_for_url(r.url)
        if platform is None:
            continue
        out.append(r)
    return out


async def discover_social_candidates(
    *,
    name_guess: str | None,
    company_domain: str | None,
    company_name_hint: str | None = None,
    max_per_platform: int = 3,
) -> list[SocialCandidate]:
    """Discover social profile candidates using search snippets.

    This does NOT scrape platforms directly. It only uses DDG HTML search results.
    """
    name_guess = _normalize_space(name_guess or "") or None
    name_tokens = _name_tokens(name_guess)

    company_hints: list[str] = []
    if company_domain:
        company_hints.append(company_domain)
        company_hints.append(company_domain.split(".")[0])
    if company_name_hint:
        company_hints.append(company_name_hint)

    # Construct a small query set. Keep it minimal to avoid rate limiting.
    queries: list[tuple[str, str]] = []
    if name_guess and company_domain:
        queries.append(("instagram", f"site:instagram.com {name_guess} {company_domain}"))
        queries.append(("x", f"site:x.com {name_guess} {company_domain}"))
        queries.append(("medium", f"site:medium.com {name_guess} {company_domain}"))
    elif name_guess and company_name_hint:
        queries.append(("instagram", f"site:instagram.com {name_guess} {company_name_hint}"))
        queries.append(("x", f"site:x.com {name_guess} {company_name_hint}"))
        queries.append(("medium", f"site:medium.com {name_guess} {company_name_hint}"))
    elif name_guess:
        queries.append(("instagram", f"site:instagram.com {name_guess}"))
        queries.append(("x", f"site:x.com {name_guess}"))
        queries.append(("medium", f"site:medium.com {name_guess}"))

    # Fetch results
    found: list[SocialCandidate] = []
    for _, q in queries:
        try:
            results = await ddg_search(q, max_results=6)
        except Exception:
            continue
        for r in _filter_results(results):
            platform = _platform_for_url(r.url) or "website"
            conf = _score_candidate(
                url=r.url,
                snippet=r.snippet or "",
                title=r.title or "",
                name_tokens=name_tokens,
                company_hints=company_hints,
            )
            found.append(
                SocialCandidate(
                    platform=platform,
                    url=r.url,
                    title=r.title,
                    snippet=r.snippet,
                    confidence=conf,
                    source="discovered",
                )
            )

    # Deduplicate by URL and keep top-N per platform by confidence.
    dedup: dict[str, SocialCandidate] = {}
    for c in found:
        if c.url in dedup:
            if c.confidence > dedup[c.url].confidence:
                dedup[c.url] = c
        else:
            dedup[c.url] = c

    by_platform: dict[str, list[SocialCandidate]] = {}
    for c in dedup.values():
        by_platform.setdefault(c.platform, []).append(c)

    out: list[SocialCandidate] = []
    for plat, items in by_platform.items():
        items.sort(key=lambda x: x.confidence, reverse=True)
        out.extend(items[:max_per_platform])

    # Stable ordering
    out.sort(key=lambda x: (x.platform, -x.confidence, x.url))
    return out


async def fetch_user_profile_snippet(url: str) -> tuple[str | None, str | None]:
    """Best-effort: get a short snippet/title about a user-provided URL via search.

    This avoids scraping the social platform directly.
    """
    if not url:
        return None, None
    try:
        # Quoted URL tends to return that exact page.
        results = await ddg_search(f'"{url}"', max_results=1)
    except Exception:
        return None, None

    if not results:
        return None, None

    r = results[0]
    return r.title, r.snippet
