"""
Company domain resolution and normalization.

Converts company names to domains for crawling/research.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


def extract_domain_from_url(url: str) -> str | None:
    """Extract clean domain from a URL.
    
    Example:
        "https://www.openai.com/about" -> "openai.com"
        "http://subdomain.example.co.uk/" -> "example.co.uk"
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        
        # Strip "www." prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Remove trailing slashes
        domain = domain.rstrip('/')
        
        return domain if domain else None
    except Exception:
        return None


def is_likely_domain(company: str) -> bool:
    """Check if input looks like a domain already.
    
    Examples:
        "openai.com" -> True
        "example.co.uk" -> True
        "OpenAI" -> False
        "Acme Corp" -> False
    """
    # Has a dot and looks domain-like (no spaces, reasonable length)
    return (
        '.' in company
        and ' ' not in company
        and 2 <= len(company.split('.')) <= 4
        and len(company) < 100
    )


def normalize_company_name(company: str) -> str:
    """Normalize company name for search/matching.
    
    - Remove common suffixes (Inc, Corp, LLC, Ltd)
    - Lowercase
    - Strip whitespace
    """
    normalized = company.lower().strip()
    
    # Remove common corporate suffixes
    suffixes = [
        r'\s+inc\.?$',
        r'\s+corp\.?$',
        r'\s+corporation$',
        r'\s+llc\.?$',
        r'\s+ltd\.?$',
        r'\s+limited$',
        r'\s+co\.?$',
        r'\s+company$',
    ]
    
    for suffix in suffixes:
        normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)
    
    return normalized.strip()


def guess_domain_from_company(company: str) -> str:
    """Guess a domain from company name (last-resort fallback).
    
    Examples:
        "OpenAI" -> "openai.com"
        "Acme Corp" -> "acme.com"
        "Microsoft Corporation" -> "microsoft.com"
    
    This is a heuristic; real domain may differ.
    """
    normalized = normalize_company_name(company)
    
    # Take first word if multi-word
    # "acme widgets" -> "acme"
    first_word = normalized.split()[0] if normalized else company.lower()
    
    # Remove special chars
    slug = re.sub(r'[^a-z0-9]', '', first_word)
    
    return f"{slug}.com" if slug else f"{company.lower().replace(' ', '')}.com"


async def resolve_company_domain(company: str) -> dict[str, str | None]:
    """Resolve company name to a domain (best-effort).
    
    Strategy:
    1. If input looks like a domain already -> use it
    2. Search DuckDuckGo: "{company} official website"
    3. Extract domain from top result
    4. Fallback: guess domain from company name
    
    Returns:
        {
            'domain': str,
            'method': 'direct' | 'search' | 'guess',
            'confidence': 'high' | 'medium' | 'low'
        }
    """
    company = company.strip()
    
    # Step 1: Check if already a domain
    if is_likely_domain(company):
        return {
            'domain': company.lower(),
            'method': 'direct',
            'confidence': 'high'
        }
    
    # Step 2: Search DuckDuckGo
    from app.search.ddg import ddg_search
    
    query = f'"{company}" official website'
    results = await ddg_search(query, max_results=3)
    
    for result in results:
        # SearchResult is a dataclass, access attributes directly
        url = result.url if hasattr(result, 'url') else ''
        if url:
            domain = extract_domain_from_url(url)
            if domain:
                # Validate: domain should relate to company name
                # (avoid random results)
                normalized_company = normalize_company_name(company)
                domain_slug = domain.split('.')[0]  # "openai.com" -> "openai"
                
                # If company name appears in domain or vice versa
                if (
                    normalized_company in domain_slug
                    or domain_slug in normalized_company
                ):
                    return {
                        'domain': domain,
                        'method': 'search',
                        'confidence': 'medium'
                    }
    
    # Step 3: Fallback guess
    guessed = guess_domain_from_company(company)
    return {
        'domain': guessed,
        'method': 'guess',
        'confidence': 'low'
    }
