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

## Next build steps
1. Implement web search collection (DuckDuckGo HTML)
2. Implement company-site scraping and content cleaning
3. Pass evidence snippets into Gemini prompt
4. Add confidence scoring rules based on evidence quality
