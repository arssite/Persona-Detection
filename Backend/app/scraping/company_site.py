from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from html.parser import HTMLParser

from app.utils.text import normalize_whitespace
from app.scraping.robots import fetch_robots


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


class _LinkAndTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self._texts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        t = tag.lower()
        if t in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if t == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    self.links.append(v)

    def handle_endtag(self, tag: str):
        t = tag.lower()
        if t in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str):
        if self._skip_depth > 0:
            return
        if data and data.strip():
            self._texts.append(data.strip())

    def text(self) -> str:
        return normalize_whitespace(" ".join(self._texts))


def html_to_text(html: str) -> str:
    """Dependency-light text extraction.

    This is less powerful than trafilatura/readability, but avoids installing
    compiled dependencies on Windows.
    """
    parser = _LinkAndTextParser()
    try:
        parser.feed(html)
        return parser.text()
    finally:
        parser.close()


def _same_host(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def _extract_links(base_url: str, html: str) -> list[str]:
    parser = _LinkAndTextParser()
    try:
        parser.feed(html)
        raw_links = parser.links
    finally:
        parser.close()

    links: list[str] = []
    for href in raw_links:
        href = (href or "").strip()
        if not href:
            continue
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        abs_url = urljoin(base_url, href)
        if abs_url.startswith("http") and _same_host(base_url, abs_url):
            links.append(abs_url)

    # de-dupe
    out: list[str] = []
    seen = set()
    for u in links:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


async def scrape_company_site(domain: str, *, timeout_s: float = 15.0, max_pages: int = 8) -> list[PageText]:
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

    robots = await fetch_robots(base)

    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s, headers=headers) as client:
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue

            # Respect robots.txt (user-agent: *)
            if not robots.allowed(url, user_agent="*"):
                visited.add(url)
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
