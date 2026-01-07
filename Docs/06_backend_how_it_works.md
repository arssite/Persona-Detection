# Backend: How it Works

This document explains the current backend pipeline for the Meeting Intelligence MVP.

## Endpoint
### `POST /v1/analyze`
Input:
```json
{ "email": "firstname.lastname@company.com" }
```
Output: JSON (validated by Pydantic) containing:
- `confidence` (low/medium/high + rationale)
- `study_of_person`
- `recommendations`
- `evidence`

## Pipeline (today)
1. **Email parsing** (`app/core/email.py`)
   - Validates email format.
   - Blocks common free email domains (gmail/outlook/etc).
   - Best-effort name guess from local part (`firstname.lastname` → `Firstname Lastname`).

2. **Public signal collection** (`app/intelligence/generate.py`)
   - **DuckDuckGo HTML search** (`app/search/ddg.py`)
     - Company query: `"{domain} about company"`
     - Person query (if name guess exists): `"{name_guess} {domain}"`
     - Extracts title/snippet/url into evidence items.

   - **Company website scraping** (`app/scraping/company_site.py`)
     - Fetches a small set of pages from `https://{domain}` (seed paths like `/about`, `/careers`, `/blog`).
     - Light internal link crawl (conservative) to collect more text.
     - Cleans HTML → text and produces evidence snippets.

3. **LLM generation (Gemini)**
   - Gemini model: `gemini-2.5-flash`
   - We prompt Gemini with:
     - input email
     - name guess + company domain
     - the collected evidence bullets
   - Gemini returns JSON (we request `application/json`).

4. **JSON robustness**
   - `app/intelligence/json_guard.py` attempts to parse JSON.
   - If JSON is invalid, we do a **repair retry** with an instruction to return valid JSON.
   - If the JSON still fails schema validation, we do one more repair attempt with the validation error.

5. **Confidence handling**
   - We normalize model confidence keys into `{label, rationale}`.
   - If Gemini doesn’t return usable confidence, we apply a deterministic fallback based on evidence amount/sources (`app/core/confidence.py`).

6. **Caching**
   - In-memory TTL cache (5 minutes) prevents repeated scraping and stabilizes demo performance.

## LinkedIn, GitHub & other sources — what we do / do not do
### What we DO
- We run DuckDuckGo web search.
- If DuckDuckGo results include a LinkedIn page **as a public snippet**, that snippet + URL may appear in `evidence`.
- If DuckDuckGo results include a **GitHub profile URL**, we may call the **GitHub public API** to summarize public info (languages, recent repos).

### What we DO NOT do
- We do **not** log into LinkedIn.
- We do **not** scrape authenticated LinkedIn profile pages.
- We do **not** use any paid enrichment APIs.
- We do **not** bypass robots restrictions for company-site crawling.

This keeps the MVP in the "public web signals" category.

## Notes / Limitations
- Search HTML page structures can change; this MVP uses lightweight parsing.
- Scraping is conservative by design (timeouts, small page limits) for demo stability.
