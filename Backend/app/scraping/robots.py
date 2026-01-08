from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import httpx


@dataclass(frozen=True)
class RobotsPolicy:
    base_url: str
    parser: RobotFileParser

    def allowed(self, url: str, *, user_agent: str = "*") -> bool:
        return self.parser.can_fetch(user_agent, url)


async def fetch_robots(base_url: str, *, timeout_s: float = 10.0) -> RobotsPolicy:
    """Fetch and parse robots.txt. If unavailable, default-allow (common practical stance for MVP)."""
    robots_url = urljoin(base_url.rstrip("/") + "/", "robots.txt")
    rp = RobotFileParser()

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout_s) as client:
            resp = await client.get(robots_url, headers={"User-Agent": "Mozilla/5.0 (MeetingIntelMVP/0.1)"})
            if resp.status_code >= 400:
                rp.parse([])
                return RobotsPolicy(base_url=base_url, parser=rp)
            rp.parse(resp.text.splitlines())
    except Exception:
        rp.parse([])

    return RobotsPolicy(base_url=base_url, parser=rp)
