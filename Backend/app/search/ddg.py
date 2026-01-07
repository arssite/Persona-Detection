from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import httpx


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


_DDG_HTML_URL = "https://duckduckgo.com/html/"


def _strip_tags(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_results(html: str) -> list[SearchResult]:
    # DDG HTML results are fairly stable: results in .result elements.
    # We intentionally avoid heavy parsers for MVP; regex-based extraction with guardrails.
    results: list[SearchResult] = []

    # Each result has an <a class="result__a" href="...">Title</a>
    for block in re.findall(r"<div[^>]*class=\"result[^\"]*\"[\s\S]*?</div>\s*</div>", html):
        a = re.search(r"<a[^>]*class=\"result__a\"[^>]*href=\"([^\"]+)\"[^>]*>([\s\S]*?)</a>", block)
        if not a:
            continue
        url = a.group(1)
        title = _strip_tags(a.group(2))

        sn = re.search(r"<a[^>]*class=\"result__snippet\"[^>]*>([\s\S]*?)</a>", block)
        snippet = _strip_tags(sn.group(1)) if sn else ""

        if url and title:
            results.append(SearchResult(title=title, url=url, snippet=snippet))

    # Fallback: sometimes snippet is in <div class="result__snippet">
    if not results:
        for a in re.finditer(r"class=\"result__a\"[^>]*href=\"([^\"]+)\"[^>]*>([\s\S]*?)</a>", html):
            url = a.group(1)
            title = _strip_tags(a.group(2))
            results.append(SearchResult(title=title, url=url, snippet=""))

    # Deduplicate by URL
    seen = set()
    deduped: list[SearchResult] = []
    for r in results:
        if r.url in seen:
            continue
        seen.add(r.url)
        deduped.append(r)
    return deduped


async def ddg_search(query: str, *, max_results: int = 5, timeout_s: float = 15.0) -> list[SearchResult]:
    params = {"q": query}
    headers = {
        "User-Agent": "Mozilla/5.0 (MeetingIntelMVP/0.1; +https://example.local)",
        "Accept": "text/html,application/xhtml+xml",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s, headers=headers) as client:
        resp = await client.get(_DDG_HTML_URL, params=params)
        resp.raise_for_status()

    results = _extract_results(resp.text)
    return results[:max_results]


def results_to_evidence(results: Iterable[SearchResult], source: str) -> list[dict]:
    evidence = []
    for r in results:
        snippet = (r.snippet or r.title).strip()
        if not snippet:
            continue
        evidence.append({"source": source, "snippet": snippet[:500], "url": r.url})
    return evidence
