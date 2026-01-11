# Flexible Input: Detailed Algorithms & Edge Cases

This document provides **implementation-level detail** for each input mode: exact scraping steps, edge case handling, validation rules, and confidence scoring formulas.

---

## Input Mode 1: Corporate Email (Current, Reference Implementation)

### Input Format
```json
{
  "email": "alex.smith@company.com"
}
```

### Validation Rules
1. **Format check**: regex `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
2. **Free domain block**: reject if domain in `[gmail.com, yahoo.com, outlook.com, hotmail.com, ...]`
3. **Domain exists**: optional DNS MX record check (skip for MVP to avoid latency)

### Extraction Algorithm
```python
def parse_email(email: str) -> ParsedEmail:
    local, domain = email.split('@')
    
    # Name guess (best effort)
    separators = ['.', '_', '-']
    parts = local
    for sep in separators:
        parts = parts.replace(sep, ' ')
    
    words = parts.split()
    first_name = words[0].capitalize() if len(words) > 0 else None
    last_name = words[-1].capitalize() if len(words) > 1 else None
    
    return ParsedEmail(
        email=email,
        domain=domain,
        first_name=first_name,
        last_name=last_name,
        is_valid=True
    )
```

### Scraping Strategy
1. **Company website crawl** (primary source, weight 1.0):
   - Base: `https://{domain}`
   - Seed paths: `/`, `/about`, `/team`, `/careers`, `/blog`
   - Robots check: respect `robots.txt`
   - Max pages: 8
   - Extract: text content → chunks → evidence items

2. **DuckDuckGo searches** (weights 0.7–0.9):
   - Query 1: `"{domain} about company"` → company background
   - Query 2: `"{first_name} {last_name} {domain}"` → person mentions
   - Query 3: `"{domain} funding OR raises OR press release"` → news
   - Query 4: `"site:{domain} careers OR jobs OR hiring"` → hiring signals
   - Query 5: `"{first_name} {last_name} github"` → GitHub hint

3. **GitHub enrichment** (optional, weight 0.7):
   - If Query 5 returns a profile URL → call GitHub API
   - Extract: languages, top repos, bio

### Evidence Fusion
- Dedupe by `(url, snippet[:80])`
- Rank by source weight
- Top 20–25 items → LLM

### Confidence Calculation (Fallback)
```python
def email_confidence(evidence_count: int, sources: set[str]) -> str:
    if evidence_count >= 15 and 'company_site' in sources:
        return 'high'
    elif evidence_count >= 8:
        return 'medium'
    else:
        return 'low'
```

### Edge Cases
- **Common name** (e.g., `john.smith@company.com`):
  - Disambiguate using domain context in LLM prompt
  - Confidence: medium (even with strong evidence)
  
- **Domain doesn't exist** (typo, private domain):
  - Crawl fails → rely on DDG only
  - Confidence: low
  
- **No GitHub found**:
  - Skip enrichment, continue with other sources
  - Don't penalize confidence

---

## Input Mode 2: Name + Company (New)

### Input Format
```json
{
  "name": {
    "first": "Alex",
    "last": "Smith"
  },
  "company": "OpenAI"  // or "openai.com"
}
```

### Validation Rules
1. **Name**: both first and last required, 2–50 chars each, letters only (with hyphens/apostrophes OK)
2. **Company**: required, 2–100 chars
3. **No email**: if email also provided, use email mode instead (higher priority)

### Company Domain Lookup Algorithm
```python
async def resolve_company_domain(company_name: str) -> str | None:
    # Step 1: Check if already a domain
    if '.' in company_name and len(company_name.split('.')) >= 2:
        # Likely a domain: "openai.com"
        return company_name.lower().strip()
    
    # Step 2: Search DuckDuckGo
    query = f'"{company_name}" official website'
    results = await search_ddg(query, max_results=3)
    
    # Step 3: Extract domain from top result
    for result in results:
        url = result.get('url', '')
        domain = extract_domain(url)  # e.g., "https://openai.com/about" -> "openai.com"
        if domain:
            return domain
    
    # Step 4: Fallback: guess domain
    # "OpenAI" -> "openai.com"
    # "Acme Corp" -> "acmecorp.com"
    slug = company_name.lower().replace(' ', '').replace('inc', '').replace('corp', '').replace('llc', '')
    return f"{slug}.com"
```

### Scraping Strategy
1. **DuckDuckGo person+company search** (primary, weight 0.9):
   - Query: `"{first_name} {last_name}" "{company_name}"`
   - Extract: role mentions, LinkedIn snippets, news mentions

2. **LinkedIn snippet search** (weight 0.85):
   - Query: `"{first_name} {last_name}" site:linkedin.com/in "{company_name}"`
   - Extract from snippet:
     - Current role headline
     - Company name validation
     - Location (if visible)
   - **Important**: Only use public snippet, no auth scraping

3. **Company website crawl** (weight 1.0):
   - If domain resolved → crawl as in email mode
   - Look for "Team" or "About" pages mentioning the person

4. **GitHub hint search** (weight 0.7):
   - Query: `"{first_name} {last_name}" github "{company_name}"`
   - If profile found → GitHub API enrichment

### Disambiguation Strategy (Common Names)
```python
def disambiguate_name(results: list[SearchResult], company_name: str) -> list[SearchResult]:
    # Filter: keep only results where snippet mentions company
    filtered = []
    company_lower = company_name.lower()
    
    for r in results:
        snippet_lower = r.snippet.lower()
        if company_lower in snippet_lower:
            filtered.append(r)
    
    # If no matches, return all (can't disambiguate)
    return filtered if filtered else results
```

### Evidence Fusion
- Dedupe + rank (same as email mode)
- Cross-validate company mentions across sources
- Flag if company name appears in <50% of evidence (low confidence)

### Confidence Calculation
```python
def name_company_confidence(evidence_count: int, company_match_rate: float) -> str:
    # company_match_rate = % of evidence mentioning the company
    if evidence_count >= 12 and company_match_rate >= 0.6:
        return 'medium'  # Never 'high' without email
    elif evidence_count >= 6 and company_match_rate >= 0.4:
        return 'medium'
    else:
        return 'low'
```

### Edge Cases
- **Very common name** ("John Smith"):
  - Confidence capped at 'low' even if many results
  - Show warning: "Common name—using company context to filter"

- **Company name ambiguous** ("Delta"):
  - Could be airline, faucets, dental, etc.
  - Require user to clarify or provide domain

- **No LinkedIn snippet found**:
  - Proceed without LinkedIn
  - Confidence: low-medium

- **Domain guess wrong**:
  - Crawl fails → rely on DDG only
  - Confidence: low

---

## Input Mode 3A: LinkedIn URL (New)

### Input Format
```json
{
  "linkedin_url": "https://www.linkedin.com/in/alex-smith-openai"
}
```

### Validation Rules
1. **Format**: must match regex `^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9-]+/?$`
2. **Slug extraction**: `alex-smith-openai` from URL
3. **No auth**: never scrape behind login

### Extraction Algorithm
```python
def parse_linkedin_url(url: str) -> dict:
    # Extract slug
    match = re.search(r'linkedin\.com/in/([a-zA-Z0-9-]+)', url)
    if not match:
        raise ValueError("Invalid LinkedIn URL")
    
    slug = match.group(1)
    
    # Infer name + company hint from slug
    # "alex-smith-openai" -> name: Alex Smith, company_hint: openai
    parts = slug.split('-')
    
    # Heuristic: assume last part might be company
    if len(parts) >= 3:
        name_parts = parts[:-1]
        company_hint = parts[-1]
    else:
        name_parts = parts
        company_hint = None
    
    first_name = name_parts[0].capitalize() if len(name_parts) > 0 else None
    last_name = name_parts[-1].capitalize() if len(name_parts) > 1 else None
    
    return {
        'slug': slug,
        'first_name': first_name,
        'last_name': last_name,
        'company_hint': company_hint
    }
```

### Scraping Strategy (ToS-Compliant)
1. **DuckDuckGo LinkedIn snippet search** (primary, weight 0.9):
   - Query: `site:linkedin.com/in/{slug}`
   - Extract from snippet:
     - **Headline** (e.g., "Software Engineer at OpenAI")
     - Current company name
     - Location (sometimes visible)
   - Parse headline for role + company:
     ```python
     def parse_linkedin_headline(headline: str) -> dict:
         # "Software Engineer at OpenAI" -> role: Software Engineer, company: OpenAI
         # "CEO | Acme Corp" -> role: CEO, company: Acme Corp
         patterns = [
             r'(.+?)\s+at\s+(.+)',
             r'(.+?)\s+@\s+(.+)',
             r'(.+?)\s+\|\s+(.+)'
         ]
         for pattern in patterns:
             match = re.search(pattern, headline, re.IGNORECASE)
             if match:
                 return {'role': match.group(1).strip(), 'company': match.group(2).strip()}
         return {'role': headline, 'company': None}
     ```

2. **Company domain lookup** (if company extracted):
   - Use `resolve_company_domain(company_name)`
   - Crawl company site

3. **GitHub search** (weight 0.7):
   - Query: `"{first_name} {last_name}" github "{company}"`
   - If found → GitHub API

4. **DuckDuckGo person+company search** (weight 0.8):
   - Query: `"{first_name} {last_name}" "{company}"`
   - Cross-validate with non-LinkedIn sources

### Evidence Fusion
- LinkedIn snippet is **high-weight** (0.9) but single item
- Must combine with company site + DDG for full picture
- If LinkedIn is only source → confidence = low

### Confidence Calculation
```python
def linkedin_confidence(evidence_count: int, has_company_site: bool, headline_parsed: bool) -> str:
    if evidence_count >= 10 and has_company_site and headline_parsed:
        return 'medium'  # Can't be 'high' without email validation
    elif evidence_count >= 5:
        return 'medium'
    else:
        return 'low'
```

### Edge Cases
- **LinkedIn URL doesn't exist** (404):
  - DDG search returns empty
  - Error: "LinkedIn profile not found or private"

- **Headline doesn't mention company**:
  - E.g., "Entrepreneur | Investor"
  - Can't extract company → ask user or rely on slug hint

- **Slug parsing ambiguous**:
  - E.g., `john-doe-123` (numbers at end)
  - Parse as name only, no company hint

- **Private profile**:
  - Snippet may be minimal ("View John Doe's profile")
  - Confidence: very low

---

## Input Mode 3B: Twitter/X Handle (New)

### Input Format
```json
{
  "twitter_handle": "@alexsmith"  // or "alexsmith"
}
```

### Validation Rules
1. **Format**: strip `@`, validate alphanumeric + underscores, 1–15 chars
2. **API availability**: requires Twitter Developer account + Bearer token

### Twitter API Integration
```python
import httpx

TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

async def fetch_twitter_profile(handle: str) -> dict:
    handle = handle.lstrip('@')
    
    url = f'https://api.twitter.com/2/users/by/username/{handle}'
    headers = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}
    params = {
        'user.fields': 'name,description,location,url,public_metrics,pinned_tweet_id'
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
    
    user = data.get('data', {})
    return {
        'name': user.get('name'),
        'bio': user.get('description'),
        'location': user.get('location'),
        'website': user.get('url'),
        'followers': user.get('public_metrics', {}).get('followers_count'),
        'tweets': user.get('public_metrics', {}).get('tweet_count')
    }
```

### Company Inference from Bio
```python
def infer_company_from_twitter_bio(bio: str) -> str | None:
    # Common patterns:
    # "Software Engineer @OpenAI"
    # "CEO at Acme Corp"
    # "Working on AI | OpenAI"
    
    patterns = [
        r'@([A-Za-z0-9_]+)',  # @mentions (often company)
        r'at\s+([A-Z][A-Za-z\s]+)',  # "at OpenAI"
        r'\|\s+([A-Z][A-Za-z\s]+)'  # "| OpenAI"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, bio)
        if match:
            return match.group(1).strip()
    
    return None
```

### Scraping Strategy
1. **Twitter API call** (primary, weight 0.85):
   - Extract: name, bio, location, website
   - Infer company from bio

2. **Website domain extraction** (if `url` field exists):
   - If user's website is company site → crawl it

3. **Company domain lookup** (if company inferred):
   - Use `resolve_company_domain(company_name)`
   - Crawl company site

4. **DuckDuckGo cross-reference** (weight 0.7):
   - Query: `"@{handle}" OR "{name}" "{company}"`
   - Validate Twitter info against web mentions

5. **GitHub search** (weight 0.7):
   - Query: `"{name}" github`
   - If found → GitHub API

### Evidence Fusion
- Twitter bio is **single source** (1 evidence item)
- Must combine with company site + DDG
- If Twitter is only source → confidence = low

### Confidence Calculation
```python
def twitter_confidence(evidence_count: int, has_company: bool, follower_count: int) -> str:
    # High follower count suggests real/verified account
    verified = follower_count > 1000
    
    if evidence_count >= 8 and has_company and verified:
        return 'medium'
    elif evidence_count >= 5:
        return 'low-medium'
    else:
        return 'low'
```

### Edge Cases
- **Handle doesn't exist**:
  - Twitter API returns 404
  - Error: "Twitter handle not found"

- **Protected account**:
  - API may return minimal data
  - Confidence: very low

- **No company in bio**:
  - E.g., "Freelancer | Consultant"
  - Can't extract company → low confidence

- **Rate limit hit** (50 lookups/24h):
  - Cache profile for 24h
  - If cache miss + quota exceeded → error: "Twitter quota reached, try again later"

---

## Input Mode 3C: GitHub Username (Enhanced)

### Input Format
```json
{
  "github_username": "alexsmith"
}
```

### Validation Rules
1. **Format**: alphanumeric + hyphens, 1–39 chars (GitHub limit)
2. **Case-insensitive**: GitHub usernames are case-insensitive

### GitHub API Integration (Current + Enhanced)
```python
async def fetch_github_profile(username: str) -> dict:
    async with httpx.AsyncClient() as client:
        # User profile
        user_resp = await client.get(f'https://api.github.com/users/{username}')
        user_resp.raise_for_status()
        user = user_resp.json()
        
        # Repos
        repos_resp = await client.get(f'https://api.github.com/users/{username}/repos', params={'per_page': 100, 'sort': 'updated'})
        repos = repos_resp.json()
    
    # Extract top languages
    languages = {}
    for repo in repos[:20]:  # Top 20 repos
        lang = repo.get('language')
        if lang:
            languages[lang] = languages.get(lang, 0) + 1
    
    return {
        'name': user.get('name'),
        'bio': user.get('bio'),
        'company': user.get('company'),  # Key field for company inference
        'location': user.get('location'),
        'blog': user.get('blog'),  # May be company website
        'languages': sorted(languages.items(), key=lambda x: x[1], reverse=True),
        'top_repos': [{'name': r['name'], 'stars': r['stargazers_count'], 'description': r['description']} for r in repos[:5]]
    }
```

### Company Inference from GitHub Profile
```python
def infer_company_from_github(profile: dict) -> str | None:
    # GitHub 'company' field often has format: "@OpenAI" or "OpenAI"
    company_raw = profile.get('company')
    if company_raw:
        company = company_raw.lstrip('@').strip()
        return company
    
    # Fallback: check blog URL
    blog = profile.get('blog')
    if blog:
        domain = extract_domain(blog)
        if domain and domain not in ['github.io', 'github.com']:
            return domain
    
    return None
```

### Scraping Strategy
1. **GitHub API call** (primary, weight 0.85):
   - Extract: name, bio, company, languages, repos

2. **Company domain lookup** (if company extracted):
   - Use `resolve_company_domain(company_name)`
   - Crawl company site

3. **DuckDuckGo cross-reference** (weight 0.7):
   - Query: `"{name}" "{company}"`
   - Validate GitHub info against web

4. **LinkedIn hint search** (weight 0.8):
   - Query: `"{name}" site:linkedin.com/in "{company}"`
   - Cross-validate role

### Evidence Fusion
- GitHub profile is **strong technical signal** (languages, repos)
- But may lack business context (role, responsibilities)
- Combine with company site + DDG for full picture

### Confidence Calculation
```python
def github_confidence(evidence_count: int, has_company: bool, repo_count: int) -> str:
    # More repos = more established developer
    established = repo_count > 10
    
    if evidence_count >= 10 and has_company and established:
        return 'medium'
    elif evidence_count >= 6:
        return 'low-medium'
    else:
        return 'low'
```

### Edge Cases
- **Username doesn't exist**:
  - GitHub API returns 404
  - Error: "GitHub username not found"

- **No company field**:
  - Many developers don't fill this
  - Infer from blog URL or skip

- **Private repos**:
  - API doesn't return private repos (expected)
  - Use public repos only

- **Inactive account**:
  - No recent commits → repos may be outdated
  - Flag in output: "Last activity: {date}"

---

## Input Mode 4: Phone Number (Low Priority, Validation Only)

### Input Format
```json
{
  "phone": "+1-415-555-1234"
}
```

### Validation Rules
1. **Format**: accept various formats, normalize to E.164
   - Input: `(415) 555-1234`, `415-555-1234`, `+14155551234`
   - Normalized: `+14155551234`
2. **Length**: 10–15 digits (international)
3. **Country code**: optional but recommended

### Normalization Algorithm
```python
import phonenumbers

def normalize_phone(phone: str) -> str | None:
    try:
        parsed = phonenumbers.parse(phone, 'US')  # Default to US
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass
    
    # Fallback: strip non-digits
    digits = ''.join(c for c in phone if c.isdigit())
    if 10 <= len(digits) <= 15:
        return f"+{digits}"
    
    return None
```

### Scraping Strategy (Very Limited)
1. **DuckDuckGo search** (weight 0.5):
   - Query: `"{phone}"` (exact match)
   - Also try: `"{formatted_phone}"` (e.g., `"(415) 555-1234"`)
   - Look for:
     - Press releases
     - Company contact pages
     - LinkedIn mentions (rare)

2. **Company site search** (if domain known from other inputs):
   - Search site for phone number
   - Check "Contact Us" pages

### Evidence Fusion
- Phone produces **very few evidence items** (usually 0–2)
- **Do not use phone alone** for research
- Best use: **validation** (if name + company already known)

### Confidence Calculation
```python
def phone_confidence(evidence_count: int) -> str:
    # Phone should never be primary source
    if evidence_count >= 3:
        return 'low'  # Capped at low even with matches
    else:
        return 'very-low'
```

### Edge Cases
- **Phone not found**:
  - Most common case
  - Proceed without phone evidence

- **Multiple matches**:
  - E.g., company main line vs direct line
  - Can't disambiguate → list all

- **Privacy concerns**:
  - Never store phone numbers
  - Never call/SMS (out of scope)

---

## Cross-Input Validation & Conflict Resolution

### Scenario 1: Email + LinkedIn URL provided
**Priority:** Email domain is authoritative, LinkedIn validates role.

**Algorithm:**
1. Extract company from email domain
2. Extract company from LinkedIn headline
3. If domains match → confidence boost
4. If domains mismatch → flag in output: "LinkedIn shows different company—using email domain"

### Scenario 2: Name+Company + GitHub username provided
**Priority:** GitHub company field validates name+company input.

**Algorithm:**
1. Resolve company domain from name+company input
2. Extract company from GitHub profile
3. If companies match → confidence boost
4. If mismatch → use name+company input (user-provided is trusted)

### Scenario 3: LinkedIn + Twitter + GitHub all provided
**Priority:** Cross-validate all three.

**Algorithm:**
1. Extract name from each
2. Extract company from each
3. Count matches:
   - If 2+ agree on company → use that company
   - If all disagree → use LinkedIn (most professional context)

### Confidence Boost Formula
```python
def cross_validation_boost(base_confidence: str, num_sources: int, match_rate: float) -> str:
    # match_rate = % of sources agreeing on key facts (company, role)
    if num_sources >= 3 and match_rate >= 0.67:
        # Boost by one level
        if base_confidence == 'medium':
            return 'medium-high'  # New level
        elif base_confidence == 'low':
            return 'medium'
    return base_confidence
```

---

## Evidence Quality Scoring (Per Item)

Each evidence item gets a quality score (0.0–1.0) based on:

```python
def score_evidence_item(item: EvidenceItem, input_mode: str) -> float:
    score = 0.0
    
    # Base score by source type
    source_scores = {
        'company_site': 1.0,
        'linkedin_snippet': 0.9,
        'github_api': 0.85,
        'twitter_api': 0.85,
        'ddg_person': 0.8,
        'ddg_company': 0.75,
        'ddg_news': 0.7,
        'ddg_hiring': 0.65
    }
    score = source_scores.get(item.source, 0.5)
    
    # Bonus: if snippet mentions target name
    if input_mode in ['name_company', 'linkedin', 'twitter', 'github']:
        if name_mentioned_in_snippet(item.snippet, target_name):
            score += 0.1
    
    # Bonus: if snippet mentions target company
    if company_mentioned_in_snippet(item.snippet, target_company):
        score += 0.1
    
    # Penalty: if snippet is too short (likely truncated/low-quality)
    if len(item.snippet) < 50:
        score -= 0.15
    
    # Penalty: if URL is a generic aggregator
    if any(domain in item.url for domain in ['indeed.com', 'glassdoor.com', 'crunchbase.com']):
        score -= 0.1
    
    return max(0.0, min(1.0, score))
```

---

## Summary: Confidence Scoring Matrix

| Input Mode | Min Evidence | Company Match | Social Cross-Val | Max Confidence |
|------------|--------------|---------------|------------------|----------------|
| Email | 15 | N/A | N/A | HIGH |
| Email + LinkedIn | 12 | ✅ | ✅ | HIGH |
| Email + GitHub | 12 | ✅ | ✅ | HIGH |
| Name + Company | 12 | 60%+ | N/A | MEDIUM |
| LinkedIn URL | 10 | ✅ | N/A | MEDIUM |
| Twitter handle | 8 | ✅ | N/A | MEDIUM |
| GitHub username | 10 | ✅ | N/A | MEDIUM |
| LinkedIn + GitHub | 10 | ✅ | ✅ | MEDIUM-HIGH |
| Phone only | N/A | N/A | N/A | VERY LOW (error) |

---

## Next: Implementation Priority

Now that we have **detailed algorithms**, we'll implement in this order:

1. **Path A (Incremental):** Email + optional LinkedIn/GitHub
   - Backend: add optional fields, run enrichment in parallel
   - Frontend: add two optional input fields
   - Timeline: 2–3 days

2. **Path C (Name+Company):** Add name+company mode
   - Backend: company domain lookup, disambiguation logic
   - Frontend: second tab with name+company fields
   - Timeline: 3–4 days

3. **Path B (Full Flexible):** All modes + routing
   - Backend: FlexibleAnalyzeRequest schema, mode detection, all scrapers
   - Frontend: tabbed UI (4 tabs)
   - Timeline: 8–11 days (includes Twitter API setup)

Ready to start **Path A implementation** next?
