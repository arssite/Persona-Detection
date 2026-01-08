from __future__ import annotations

from collections import defaultdict


_SOURCE_WEIGHT = {
    "company_site": 5,
    "ddg_news": 4,
    "ddg_hiring": 4,
    "ddg_company": 3,
    "ddg_person": 3,
    "ddg_github": 3,
}


def dedupe_and_rank(evidence: list[dict], *, max_items: int = 20) -> list[dict]:
    """De-dupe by url + snippet and rank by source weight."""
    seen = set()
    unique: list[dict] = []
    for e in evidence:
        url = (e.get("url") or "").strip()
        snip = (e.get("snippet") or "").strip()
        key = (url, snip[:120])
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)

    def score(item: dict) -> int:
        return _SOURCE_WEIGHT.get(str(item.get("source", "")), 1)

    unique.sort(key=score, reverse=True)
    return unique[:max_items]


def top_sources_summary(evidence: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in evidence:
        counts[str(e.get("source", "unknown"))] += 1
    return dict(counts)
