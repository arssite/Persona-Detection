# Flexible Input System Design (Multi-Mode Research)

## Problem Statement
Current MVP only accepts: **corporate email** (`firstname.lastname@company.com`).

Recruiter feedback: "Sometimes I have:
- Just a name + company
- A LinkedIn URL
- A Twitter/GitHub handle
- A phone number
- Or combinations (email + LinkedIn + phone)"

**Goal:** Support flexible inputs, intelligently prioritize sources, and adapt scraping strategy based on what the user provides.

---

## 1) Supported Input Modes (Priority Order)

### Mode 1: **Corporate Email** (current, highest confidence)
**Input:**
```json
{
  "email": "firstname.lastname@company.com"
}
```

**What we can extract:**
- ✅ Company domain (direct)
- ✅ Name guess (from local part)
- ✅ Email for validation

**Scraping strategy:**
1. Company website crawl (domain)
2. DuckDuckGo: company + person queries
3. GitHub: if found in search results

**Confidence:** HIGH (domain is authoritative)

---

### Mode 2: **Name + Company Name/Domain** (manual entry)
**Input:**
```json
{
  "name": {
    "first": "Alex",
    "last": "Smith"
  },
  "company": "OpenAI"  // or "openai.com"
}
```

**What we can extract:**
- ✅ Full name (explicit)
- ✅ Company domain (lookup or guess: `openai.com`)
- ⚠️ No email validation

**Scraping strategy:**
1. DuckDuckGo: `"Alex Smith" OpenAI`
2. Company website crawl (if domain known)
3. LinkedIn search snippet: `"Alex Smith" site:linkedin.com/in openai`
4. GitHub: `"Alex Smith" github`

**Confidence:** MEDIUM (no authoritative email, name is common → disambiguation risk)

**Edge case:** Common name like "John Smith" → need disambiguation from company context.

---

### Mode 3: **Social Handle (LinkedIn, Twitter, GitHub)** (direct profile link)
**Input:**
```json
{
  "linkedin_url": "https://www.linkedin.com/in/alex-smith-openai",
  "twitter_handle": "@alexsmith",
  "github_username": "alexsmith"
}
```

**What we can extract:**
- ✅ Name (from LinkedIn URL slug or bio)
- ✅ Company (from LinkedIn current role or bio)
- ⚠️ No email (unless public on GitHub)

**Scraping strategy (respecting ToS):**

#### LinkedIn
- ❌ **Do NOT scrape behind auth** (ToS violation)
- ✅ **Use public search snippet**:
  - DuckDuckGo: `site:linkedin.com/in/alex-smith-openai`
  - Extract: headline, current role (from snippet)
- ✅ **LinkedIn public profile API** (if available without auth)

#### Twitter/X
- ✅ **Twitter/X public API** (read-only, no auth needed for public profiles):
  - GET `/users/by/username/{handle}`
  - Extract: bio, website, pinned tweet
- ⚠️ Rate limits apply

#### GitHub
- ✅ **GitHub public API** (already implemented):
  - `/users/{username}`
  - `/users/{username}/repos`
  - Extract: bio, company, languages, top repos

**Confidence:** MEDIUM-HIGH (social profiles are usually accurate, but may be outdated)

**Edge case:** Handle doesn't exist or is private.

---

### Mode 4: **Phone Number** (reverse lookup)
**Input:**
```json
{
  "phone": "+1-415-555-1234"
}
```

**What we can extract:**
- ⚠️ Very limited (no direct public source without paid APIs)

**Scraping strategy (public-only):**
1. ❌ **Do NOT use paid reverse lookup** (violates "public-only" constraint)
2. ✅ **Search DuckDuckGo**: `"+1-415-555-1234"`
   - May find: press releases, contact pages, LinkedIn mentions
3. ✅ **Company website search**: if phone found on "About" or "Contact" page

**Confidence:** LOW (public phone mentions are rare)

**Recommendation:** Phone should be **optional enrichment** (use it to validate name/company if other inputs provided), not a primary input.

---

### Mode 5: **Combination Inputs** (most powerful)
**Input:**
```json
{
  "email": "alex@openai.com",
  "linkedin_url": "https://www.linkedin.com/in/alex-smith-openai",
  "github_username": "alexsmith",
  "phone": "+1-415-555-1234"
}
```

**Strategy:** Use all sources, cross-validate, prioritize by confidence.

**Scraping workflow:**
1. Email → company domain (authoritative)
2. LinkedIn snippet → current role validation
3. GitHub API → tech stack / languages
4. Phone → optional contact validation

**Confidence:** HIGHEST (multiple cross-validated sources)

---

## 2) Input Prioritization Logic (How to Handle Conflicts)

### Priority rules (when inputs conflict):
1. **Company domain from email > company from LinkedIn > company from user input**
   - Rationale: email domain is most authoritative
2. **Name from social profile > name from email guess > name from user input**
   - Rationale: social profiles are explicit, email guesses can be wrong
3. **Phone is always optional enrichment** (never primary)

### Validation flow:
```
IF email provided:
  extract domain → PRIMARY company
  extract name guess → SECONDARY name (validate against social if provided)
ELSE IF linkedin_url provided:
  extract name + company from snippet → PRIMARY
  search company domain → crawl
ELSE IF name + company provided:
  search "{name} {company}" → validate existence
  guess domain → crawl
ELSE:
  return error: "Need at least email OR (name + company) OR social handle"
```

---

## 3) Updated Input Schema (Backend)

### New Pydantic model: `FlexibleAnalyzeRequest`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class NameInput(BaseModel):
    first: str
    last: str

class SocialHandles(BaseModel):
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None  # e.g., "@alexsmith" or "alexsmith"
    github_username: Optional[str] = None

class FlexibleAnalyzeRequest(BaseModel):
    # Option 1: Corporate email (current)
    email: Optional[str] = None
    
    # Option 2: Name + company
    name: Optional[NameInput] = None
    company: Optional[str] = None  # "OpenAI" or "openai.com"
    
    # Option 3: Social handles
    social: Optional[SocialHandles] = None
    
    # Optional enrichment
    phone: Optional[str] = None
    
    @field_validator('*', mode='before')
    def validate_at_least_one_input(cls, values):
        # At least one of: email, (name+company), or social handle
        has_email = values.get('email')
        has_name_company = values.get('name') and values.get('company')
        has_social = values.get('social') and any([
            values.get('social').linkedin_url,
            values.get('social').twitter_handle,
            values.get('social').github_username
        ])
        
        if not (has_email or has_name_company or has_social):
            raise ValueError("Must provide: email OR (name + company) OR social handle")
        
        return values
```

---

## 4) Scraping Strategy Per Input Type

### Strategy Table

| Input Type | Sources to Hit | What to Extract | Confidence | Notes |
|------------|---------------|-----------------|------------|-------|
| **Email** | Company site, DDG (company+person), GitHub (if found) | Domain, name guess, role, tech stack | HIGH | Current MVP |
| **Name + Company** | DDG (name+company), company site, LinkedIn snippet, GitHub | Name validation, role, bio, tech stack | MEDIUM | Need disambiguation for common names |
| **LinkedIn URL** | DDG (LinkedIn snippet), company site (if found), GitHub | Current role, headline, company domain | MEDIUM-HIGH | No auth scraping |
| **Twitter handle** | Twitter API (public), DDG (handle), GitHub (if linked) | Bio, website, pinned content | MEDIUM | Rate limits |
| **GitHub username** | GitHub API (user + repos) | Bio, company, languages, top repos | MEDIUM | Already implemented |
| **Phone** | DDG (phone string search), company site search | Contact validation | LOW | Rarely useful alone |

---

## 5) How Scraping Works Per Input (Detailed)

### A) **Corporate Email** (current)
**Input:** `alex.smith@openai.com`

**Step 1: Parse**
- Domain: `openai.com`
- Name guess: `Alex Smith`

**Step 2: Collect signals**
1. **Company site crawl** (`openai.com`): `/`, `/about`, `/team`, `/careers`
2. **DuckDuckGo searches**:
   - `"openai.com about company"`
   - `"Alex Smith openai.com"`
   - `"openai.com funding OR press release"`
   - `"site:openai.com careers OR jobs"`
3. **GitHub hint search**: `"Alex Smith github"`
   - If found: call GitHub API

**Step 3: Dedupe + rank**
- Company site: weight 1.0
- DDG company: 0.8
- DDG person: 0.9
- GitHub: 0.7

**Output:** Evidence pack → LLM

---

### B) **Name + Company** (new)
**Input:**
```json
{
  "name": {"first": "Alex", "last": "Smith"},
  "company": "OpenAI"
}
```

**Step 1: Normalize company**
- If `company` is a domain (`openai.com`) → use directly
- Else: guess domain:
  - Search DDG: `"OpenAI official website"`
  - Extract domain from top result (e.g., `openai.com`)

**Step 2: Collect signals**
1. **DuckDuckGo searches**:
   - `"Alex Smith OpenAI"` (broad)
   - `"Alex Smith site:linkedin.com/in OpenAI"` (LinkedIn snippet)
   - `"Alex Smith github"` (GitHub hint)
2. **Company site crawl** (if domain found)
3. **GitHub API** (if username found)

**Step 3: Disambiguation**
- If multiple "Alex Smith" results → use company context to filter
- Example: prioritize snippets mentioning "OpenAI" in same sentence

**Output:** Evidence pack (may be thinner than email-based)

---

### C) **LinkedIn URL** (new)
**Input:** `https://www.linkedin.com/in/alex-smith-openai`

**Step 1: Extract from URL**
- Slug: `alex-smith-openai`
- Infer: Name ≈ `Alex Smith`, Company hint ≈ `openai`

**Step 2: Public snippet search**
- DuckDuckGo: `site:linkedin.com/in/alex-smith-openai`
- Extract from snippet:
  - Headline (e.g., "Software Engineer at OpenAI")
  - Current company
  - Location (if visible in snippet)

**Step 3: Company domain lookup**
- Search DDG: `"OpenAI official website"` → get `openai.com`
- Crawl company site

**Step 4: Cross-reference GitHub**
- Search: `"Alex Smith github openai"`

**Output:** Evidence pack with LinkedIn snippet + company site + optional GitHub

**Important:** We **never** log into LinkedIn or scrape behind auth (ToS compliant).

---

### D) **Twitter Handle** (new)
**Input:** `@alexsmith` or `alexsmith`

**Step 1: Normalize handle**
- Strip `@` if present

**Step 2: Twitter/X Public API**
- Endpoint: `GET https://api.twitter.com/2/users/by/username/{handle}`
- Auth: Bearer token (requires Twitter Developer account, free tier)
- Extract:
  - `name`, `bio`, `location`, `url` (website)
  - `public_metrics` (followers, tweets)
  - Optional: `pinned_tweet_id` → fetch pinned tweet

**Step 3: Company domain inference**
- If `bio` mentions a company → search for domain
- If `url` links to company site → use that domain

**Step 4: Evidence collection**
- Company site crawl (if domain found)
- DuckDuckGo: `"@alexsmith" OR "Alex Smith" {company}`

**Output:** Evidence with Twitter bio + optional company signals

**Rate limits (Twitter free tier):**
- 1,500 tweets read/month
- 50 user lookups/24h
→ Implement caching (24h TTL for Twitter profiles)

---

### E) **GitHub Username** (new, enhanced)
**Input:** `alexsmith`

**Step 1: GitHub API** (already implemented)
- `GET /users/alexsmith`
- `GET /users/alexsmith/repos?per_page=100&sort=updated`

**Extract:**
- `name`, `bio`, `company`, `location`, `blog` (website)
- Top languages (from repos)
- Recent repos

**Step 2: Company domain inference**
- If `company` field exists (e.g., "OpenAI") → search for domain
- If `blog` URL exists → extract domain

**Step 3: Evidence collection**
- Company site crawl (if domain found)
- DuckDuckGo: `"{name}" {company}"`

**Output:** Evidence with GitHub profile + optional company signals

---

### F) **Phone Number** (low priority, optional)
**Input:** `+1-415-555-1234`

**Step 1: Format normalization**
- Strip non-digits: `14155551234`
- Format variants: `(415) 555-1234`, `415-555-1234`

**Step 2: Public search**
- DuckDuckGo: `"+1-415-555-1234"` OR `"(415) 555-1234"`
- Look for:
  - Press releases mentioning phone
  - Company "Contact Us" pages
  - LinkedIn mentions (rare)

**Step 3: Validation only**
- If name/company already known → use phone to confirm
- Example: if company site lists phone → confidence boost

**Output:** Minimal evidence (phone is **not** a primary research signal)

**Recommendation:** Phone should be **optional input** for validation, not standalone.

---

## 6) UI Design (Frontend Changes)

### Current UI:
- Single input: "Enter corporate email"

### Proposed UI (tabbed input):

```
┌─────────────────────────────────────────────┐
│  Meeting Intelligence MVP                   │
├─────────────────────────────────────────────┤
│  How do you want to search?                 │
│  ┌───┐ ┌──────────┐ ┌────────┐ ┌──────┐   │
│  │ 📧 │ │ 👤+🏢    │ │ 🔗      │ │ ☎️    │   │
│  │Email│ │Name+Co  │ │Social  │ │Phone │   │
│  └───┘ └──────────┘ └────────┘ └──────┘   │
│                                             │
│  [Active tab content here]                  │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 📧 Email                             │   │
│  │ ┌─────────────────────────────────┐ │   │
│  │ │ alex.smith@company.com          │ │   │
│  │ └─────────────────────────────────┘ │   │
│  │                                     │   │
│  │ (Optional: Add LinkedIn, GitHub)   │   │
│  │ ┌─────────────────────────────────┐ │   │
│  │ │ LinkedIn URL (optional)         │ │   │
│  │ └─────────────────────────────────┘ │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  [Analyze]                                  │
└─────────────────────────────────────────────┘
```

**Tab 1: Email** (current, default)
- Input: email
- Optional: LinkedIn URL, GitHub username, phone

**Tab 2: Name + Company**
- Input: first name, last name, company name

**Tab 3: Social Handles**
- Input: LinkedIn URL, Twitter handle, GitHub username (at least one required)

**Tab 4: Phone** (disabled for MVP, show "Coming Soon" tooltip)

---

## 7) Backend Implementation Plan

### Phase 1: Schema + routing (1–2 days)
- [ ] Create `FlexibleAnalyzeRequest` schema
- [ ] Add input mode detection logic
- [ ] Route to appropriate scraping strategy

### Phase 2: New scrapers (3–4 days)
- [ ] LinkedIn snippet extractor (DDG-based, no auth)
- [ ] Twitter API client (public endpoints only)
- [ ] Enhanced GitHub enrichment (company inference)
- [ ] Phone number formatter + validator

### Phase 3: Evidence fusion (2 days)
- [ ] Cross-validation logic (email domain vs LinkedIn company)
- [ ] Conflict resolution (prioritize email > social > manual)
- [ ] Confidence adjustment based on input mode

### Phase 4: Frontend UI (2–3 days)
- [ ] Tabbed input component
- [ ] Validation messages per tab
- [ ] Optional field toggles

### Total estimate: **8–11 days** for full flexible input system

---

## 8) Risks + Mitigation

### Risk 1: **Rate limits (Twitter, GitHub)**
**Mitigation:**
- Cache social profiles (24h TTL)
- Implement request quotas per user (e.g., 5 analyses/hour)
- Graceful degradation: if Twitter quota hit, skip Twitter enrichment

### Risk 2: **Disambiguation (common names)**
**Mitigation:**
- Use company context as filter
- Show confidence warning: "Multiple 'John Smith' found—using company match"

### Risk 3: **LinkedIn scraping ToS**
**Mitigation:**
- **Never** scrape behind auth
- Only use public search snippets (same as DuckDuckGo results)
- Document in ethics docs

### Risk 4: **Phone number privacy**
**Mitigation:**
- Never store phone numbers
- Only use for validation, not primary research
- Add warning in UI: "Phone is optional and not stored"

---

## 9) Recruiter Talk Track (How to Explain This)

**When recruiter asks: "Can I use LinkedIn instead of email?"**

> "Yes! Version 2 supports flexible inputs:
> - Corporate email (most accurate)
> - Name + company (when you don't have email)
> - LinkedIn/Twitter/GitHub handles (cross-validate)
> - Phone (optional, for validation)
>
> The system intelligently prioritizes sources and cross-validates. For example:
> - If you provide email + LinkedIn, we use the email's company domain as authoritative and validate the role against LinkedIn's public snippet.
> - If you only have a LinkedIn URL, we extract the company from the headline and scrape their site.
>
> All scraping is public-only (no auth), so it's ToS-compliant and transparent."

---

## 10) Next Steps (Recommended Order)

### Option A: **Quick win (MVP+)**
Implement **Name + Company** input only (no social handles yet).
- Pros: Simple, addresses recruiter pain point
- Cons: Misses social enrichment

### Option B: **Full flexible input (V2)**
Implement all modes (email, name+company, social, phone).
- Pros: Complete solution
- Cons: 8–11 days dev time

### Option C: **Email + optional social enrichment (hybrid)**
Keep email as primary, add optional LinkedIn/GitHub fields.
- Pros: Incremental, low risk
- Cons: Still requires email

**Recommendation:** Start with **Option C** (email + optional social), then expand to **Option B** in V2.

---

## Summary

**Input modes (priority):**
1. Corporate email (HIGH confidence)
2. Name + company (MEDIUM confidence)
3. Social handles (MEDIUM-HIGH confidence)
4. Phone (LOW confidence, optional)

**Scraping strategy:**
- Email → company site + DDG + GitHub
- Name+company → DDG + LinkedIn snippet + GitHub
- LinkedIn → snippet + company site
- Twitter → public API + company inference
- GitHub → API + company inference
- Phone → validation only

**Implementation:** 8–11 days for full system, or 2–3 days for incremental (email + optional social).

**Next:** Do you want me to implement **Option C (incremental)** now, or create the full **Option B** plan with detailed code changes?
