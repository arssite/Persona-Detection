"""
Social media profile scraping (public data only).

This module scrapes public profile information from Instagram, Medium, and X/Twitter
without authentication, respecting ethical boundaries and robots.txt where applicable.

Note: These scrapers are fragile and may break if platforms change their HTML structure.
They only extract publicly visible information without login.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup


@dataclass
class InstagramProfile:
    """Public Instagram profile data."""
    username: str
    url: str
    full_name: str | None = None
    bio: str | None = None
    followers_count: int | None = None
    following_count: int | None = None
    posts_count: int | None = None
    is_verified: bool = False
    profile_pic_url: str | None = None
    is_private: bool = False


@dataclass
class MediumProfile:
    """Public Medium profile data."""
    username: str
    url: str
    name: str | None = None
    bio: str | None = None
    followers_count: int | None = None
    following_count: int | None = None
    profile_image_url: str | None = None
    recent_stories: list[dict[str, Any]] = None


@dataclass
class XProfile:
    """Public X/Twitter profile data."""
    username: str
    url: str
    name: str | None = None
    bio: str | None = None
    followers_count: int | None = None
    following_count: int | None = None
    tweets_count: int | None = None
    is_verified: bool = False
    location: str | None = None
    website: str | None = None
    joined_date: str | None = None


async def scrape_instagram_profile(url: str, timeout: int = 10) -> InstagramProfile | None:
    """
    Scrape public Instagram profile data.
    
    Note: Instagram heavily restricts scraping. This attempts to extract data from
    the public-facing page without authentication. Success rate is low due to
    Instagram's anti-scraping measures (requires login for most data).
    
    Alternative: Use Instagram's public API or oEmbed endpoint for basic data.
    """
    try:
        # Extract username from URL
        username_match = re.search(r'instagram\.com/([^/\?]+)', url, re.I)
        if not username_match:
            return None
        username = username_match.group(1)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # Try to get oEmbed data first (public API)
            oembed_url = f"https://graph.facebook.com/v18.0/instagram_oembed?url={url}&access_token=&fields=author_name,author_url,provider_name"
            
            try:
                oembed_resp = await client.get(oembed_url, headers=headers)
                if oembed_resp.status_code == 200:
                    oembed_data = oembed_resp.json()
                    author_name = oembed_data.get('author_name')
                    
                    return InstagramProfile(
                        username=username,
                        url=url,
                        full_name=author_name,
                        bio=None,
                        followers_count=None,
                        following_count=None,
                        posts_count=None,
                        is_verified=False,
                        profile_pic_url=None,
                        is_private=False
                    )
            except Exception:
                pass
            
            # Fallback: Try to scrape the page directly
            # Note: This often fails due to Instagram requiring login
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return None
            
            html = response.text
            
            # Try to extract JSON-LD structured data
            json_ld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            if json_ld_match:
                import json
                try:
                    data = json.loads(json_ld_match.group(1))
                    if isinstance(data, dict):
                        return InstagramProfile(
                            username=username,
                            url=url,
                            full_name=data.get('name'),
                            bio=data.get('description'),
                            followers_count=None,
                            following_count=None,
                            posts_count=None,
                            is_verified=False,
                            profile_pic_url=data.get('image'),
                            is_private=False
                        )
                except Exception:
                    pass
            
            # Try to extract from meta tags
            soup = BeautifulSoup(html, 'html.parser')
            
            full_name = None
            bio = None
            profile_pic = None
            
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title_text = og_title.get('content', '')
                # Format: "Name (@username) • Instagram photos and videos"
                name_match = re.search(r'^([^(]+)', title_text)
                if name_match:
                    full_name = name_match.group(1).strip()
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                bio = og_description.get('content', '')
            
            og_image = soup.find('meta', property='og:image')
            if og_image:
                profile_pic = og_image.get('content')
            
            return InstagramProfile(
                username=username,
                url=url,
                full_name=full_name,
                bio=bio,
                followers_count=None,
                following_count=None,
                posts_count=None,
                is_verified=False,
                profile_pic_url=profile_pic,
                is_private=False
            )
            
    except Exception as e:
        print(f"Instagram scraping error for {url}: {e}")
        return None


async def scrape_medium_profile(url: str, timeout: int = 10) -> MediumProfile | None:
    """
    Scrape public Medium profile data.
    
    Medium is more scraper-friendly than Instagram. We can extract basic profile
    info and recent stories from the public profile page.
    """
    try:
        # Extract username from URL - handle both @username and regular username formats
        username_match = re.search(r'medium\.com/@?([^/\?]+)', url, re.I)
        if not username_match:
            return None
        username = username_match.group(1).lstrip('@')
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return None
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract structured data
            name = None
            bio = None
            followers = None
            profile_image = None
            recent_stories = []
            
            # Try to get name from meta tags
            og_title = soup.find('meta', property='og:title')
            if og_title:
                name = og_title.get('content', '').strip()
                # Clean up "Stories by Name - Medium"
                name = re.sub(r'\s*-\s*Medium\s*$', '', name)
                name = re.sub(r'^Stories by\s+', '', name)
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                bio = og_description.get('content', '').strip()
            
            og_image = soup.find('meta', property='og:image')
            if og_image:
                profile_image = og_image.get('content')
            
            # Try to extract recent stories from article links
            # Medium uses various class names, look for article titles
            articles = soup.find_all('h2', limit=5)
            for article in articles:
                link = article.find_parent('a')
                if link and link.get('href'):
                    story_title = article.get_text(strip=True)
                    story_url = link.get('href')
                    if story_url and story_title:
                        # Make URL absolute
                        if story_url.startswith('/'):
                            story_url = f"https://medium.com{story_url}"
                        recent_stories.append({
                            'title': story_title,
                            'url': story_url
                        })
            
            return MediumProfile(
                username=username,
                url=url,
                name=name,
                bio=bio,
                followers_count=followers,
                following_count=None,
                profile_image_url=profile_image,
                recent_stories=recent_stories if recent_stories else None
            )
            
    except Exception as e:
        print(f"Medium scraping error for {url}: {e}")
        return None


async def scrape_x_profile(url: str, timeout: int = 10) -> XProfile | None:
    """
    Scrape public X/Twitter profile data.
    
    Note: X/Twitter has strong anti-scraping measures. This attempts to extract
    data from meta tags and structured data without authentication.
    Success rate is moderate - some data may be unavailable.
    """
    try:
        # Extract username from URL
        username_match = re.search(r'(?:x\.com|twitter\.com)/([^/\?]+)', url, re.I)
        if not username_match:
            return None
        username = username_match.group(1)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                return None
            
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data from meta tags
            name = None
            bio = None
            profile_image = None
            
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '')
                # Format: "Name (@username) / X" or "Name (@username) on X"
                name_match = re.search(r'^([^(]+)', title)
                if name_match:
                    name = name_match.group(1).strip()
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                bio = og_description.get('content', '').strip()
            
            og_image = soup.find('meta', property='og:image')
            if og_image:
                profile_image = og_image.get('content')
            
            return XProfile(
                username=username,
                url=url,
                name=name,
                bio=bio,
                followers_count=None,
                following_count=None,
                tweets_count=None,
                is_verified=False,
                location=None,
                website=None,
                joined_date=None
            )
            
    except Exception as e:
        print(f"X/Twitter scraping error for {url}: {e}")
        return None
