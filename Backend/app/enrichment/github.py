from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx


_GH_PROFILE_RE = re.compile(r"^https?://(www\.)?github\.com/(?P<user>[A-Za-z0-9-]{1,39})(/)?$", re.I)


@dataclass(frozen=True)
class GitHubProfile:
    username: str
    html_url: str
    name: str | None
    company: str | None
    location: str | None
    bio: str | None
    public_repos: int | None
    followers: int | None
    following: int | None
    top_languages: list[str]
    top_repos: list[dict[str, Any]]


def extract_github_user(url: str) -> str | None:
    url = (url or "").strip()
    m = _GH_PROFILE_RE.match(url)
    if not m:
        return None
    return m.group("user")


async def fetch_github_profile(username: str, *, timeout_s: float = 12.0) -> GitHubProfile | None:
    headers = {
        "User-Agent": "MeetingIntelMVP/0.1",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient(timeout=timeout_s, headers=headers, follow_redirects=True) as client:
        u = f"https://api.github.com/users/{username}"
        r = await client.get(u)
        if r.status_code >= 400:
            return None
        user = r.json()

        # Pull a few repos and summarize languages by counting repo primary language.
        repos_r = await client.get(f"https://api.github.com/users/{username}/repos", params={"per_page": 100, "sort": "updated"})
        repos = repos_r.json() if repos_r.status_code < 400 else []

    lang_counts: dict[str, int] = {}
    top_repos: list[dict[str, Any]] = []

    for repo in repos[:50]:
        if repo.get("fork"):
            continue
        lang = repo.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
        top_repos.append(
            {
                "name": repo.get("name"),
                "html_url": repo.get("html_url"),
                "description": repo.get("description"),
                "language": lang,
                "stargazers_count": repo.get("stargazers_count"),
                "updated_at": repo.get("updated_at"),
            }
        )

    top_languages = [k for k, _ in sorted(lang_counts.items(), key=lambda kv: kv[1], reverse=True)][:5]

    return GitHubProfile(
        username=username,
        html_url=user.get("html_url") or f"https://github.com/{username}",
        name=user.get("name"),
        company=user.get("company"),
        location=user.get("location"),
        bio=user.get("bio"),
        public_repos=user.get("public_repos"),
        followers=user.get("followers"),
        following=user.get("following"),
        top_languages=top_languages,
        top_repos=top_repos[:8],
    )
