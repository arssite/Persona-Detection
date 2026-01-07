from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

from app.utils.text import normalize_whitespace


@dataclass(frozen=True)
class PageText:
    url: str
    title: str | None
    text: str


def _extract_title(html: str) -> str | None:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.I | re.S)
    if not m:
        return None
    return normalize_whitespace(re.sub(r"<[^>]+>", " ", m.group(1)))


def html_to_text(html: str) -> str:
    # lightweight cleaning; remove scripts/styles and tags
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.I)
    html = re.sub(r"<!--([\s\S]*?)-->", " ", html)
    html = re.sub(r"<[^>]+>", " ", html)
    return normalize_whitespace(html)


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _extract_links(base_url: str, html: str) -> list[str]:
    links = []
    for href in re.findall(r"href=\"([^\"]+)\"", html, flags=re.I):
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        abs_url = urljoin(base_url, href)
        if abs_url.startswith("http") and _same_host(base_url, abs_url):
            links.append(abs_url)
    # de-dupe
    out = []
    seen = set()
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def scrape_company_site(domain: str, *, timeout_s: float = 15.0, max_pages: int = 4) -> list[PageText]:
    """Fetch a small set of pages from a company domain.

    This is intentionally conservative for MVP demo stability.
    """
    base = f"https://{domain.strip().lower().rstrip('/')}"

    seed_paths = ["/", "/about", "/about-us", "/company", "/careers", "/blog"]
    seed_urls = [urljoin(base, p) for p in seed_paths]

    headers = {
        "User-Agent": "Mozilla/5.0 (MeetingIntelMVP/0.1; +https://example.local)",
        "Accept": "text/html,application/xhtml+xml",
    }

    pages: list[PageText] = []
    visited: set[str] = set()
    queue: list[str] = seed_urls[:]

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s, headers=headers) as client:
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    continue
                ct = resp.headers.get("content-type", "")
                if "text/html" not in ct:
                    continue
                html = resp.text
            except Exception:
                continue

            title = _extract_title(html)
            text = html_to_text(html)
            if text:
                pages.append(PageText(url=url, title=title, text=text[:2000]))

            # light crawl: add a few internal links
            for link in _extract_links(url, html)[:10]:
                if link not in visited and len(queue) < 20:
                    queue.append(link)

    return pages


def pages_to_evidence(pages: list[PageText]) -> list[dict]:
    evidence: list[dict] = []
    for p in pages:
        snippet = p.text
        if p.title:
            snippet = f"{p.title}: {snippet}"
        evidence.append({"source": "company_site", "snippet": snippet[:500], "url": p.url})
    return evidence
