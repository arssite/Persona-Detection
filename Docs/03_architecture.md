# Architecture (MVP)

## Components
- Frontend: React + TypeScript (Vite)
- Backend: FastAPI
- LLM: Gemini (`gemini-2.5-flash`)

## Current state
- Backend has working endpoints:
  - `GET /health`
  - `POST /v1/analyze`
- Frontend calls `/v1/analyze` and renders:
  - confidence
  - study_of_person
  - recommendations
  - evidence

## Current data sources (implemented)
- DuckDuckGo HTML search snippets
- Company website pages (small crawl)

## LinkedIn policy
We do **not** scrape LinkedIn directly. If a LinkedIn URL appears in DuckDuckGo results, we may include the public snippet and link as evidence.

## Next build steps (optional enhancements)
- Better HTML parsing (BeautifulSoup) + stronger dedupe
- More deterministic confidence scoring
- Streaming progress to the UI
