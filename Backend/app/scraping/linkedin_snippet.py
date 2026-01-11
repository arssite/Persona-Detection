"""
LinkedIn snippet extraction via DuckDuckGo (ToS-compliant, public search only).

NO AUTH SCRAPING - only uses public search result snippets.
"""

from __future__ import annotations

import re
from typing import Any

from app.search.ddg import ddg_search


def extract_linkedin_slug(linkedin_url: str) -> str | None:
    """Extract LinkedIn profile slug from URL.
    
    Example:
        "https://www.linkedin.com/in/alex-smith-openai" -> "alex-smith-openai"
    """
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', linkedin_url, re.IGNORECASE)
    return match.group(1) if match else None


def parse_linkedin_headline(headline: str) -> dict[str, str | None]:
    """Parse LinkedIn headline to extract role and company.
    
    Common patterns:
    - "Software Engineer at OpenAI"
    - "CEO @ Acme Corp"
    - "Product Manager | Microsoft"
    """
    patterns = [
        (r'(.+?)\s+at\s+(.+)', 'at'),
        (r'(.+?)\s+@\s+(.+)', '@'),
        (r'(.+?)\s+\|\s+(.+)', '|'),
    ]
    
    for pattern, sep in patterns:
        match = re.search(pattern, headline, re.IGNORECASE)
        if match:
            return {
                'role': match.group(1).strip(),
                'company': match.group(2).strip(),
                'separator': sep
            }
    
    # No pattern matched -> treat entire headline as role
    return {'role': headline.strip(), 'company': None, 'separator': None}


async def fetch_linkedin_snippet(linkedin_url: str) -> dict[str, Any] | None:
    """Fetch LinkedIn profile snippet via DuckDuckGo (public search only).
    
    Returns:
        {
            'slug': str,
            'headline': str | None,
            'role': str | None,
            'company': str | None,
            'snippet': str,
            'source_url': str
        }
    
    Returns None if profile not found or private.
    """
    slug = extract_linkedin_slug(linkedin_url)
    if not slug:
        return None
    
    # Search DuckDuckGo for this specific LinkedIn profile
    # This returns the public snippet visible in search results
    query = f'site:linkedin.com/in/{slug}'
    results = await ddg_search(query, max_results=1)
    
    if not results:
        return None
    
    result = results[0]
    # SearchResult is a dataclass, access attributes directly
    snippet = result.snippet if hasattr(result, 'snippet') else ''
    title = result.title if hasattr(result, 'title') else ''
    
    # LinkedIn search results typically format title as:
    # "FirstName LastName - Headline"
    # Extract headline if present
    headline = None
    if ' - ' in title:
        parts = title.split(' - ', 1)
        if len(parts) == 2:
            headline = parts[1].strip()
    
    # Parse headline to extract role + company
    parsed = parse_linkedin_headline(headline) if headline else {'role': None, 'company': None}
    
    return {
        'slug': slug,
        'headline': headline,
        'role': parsed.get('role'),
        'company': parsed.get('company'),
        'snippet': snippet,
        'source_url': result.url if hasattr(result, 'url') else linkedin_url,
    }
