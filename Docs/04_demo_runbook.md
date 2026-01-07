# Demo Runbook

## 1) Start backend

```bash
cd Persona-Detection/Backend
# activate venv
uvicorn app.main:app --reload --port 8000
```

## 2) Start frontend

```bash
cd Persona-Detection/Frontend
npm run dev
```

## 3) Demo script (MVP)
1. Explain: "We only use public web signals and AI inference."
2. Enter a corporate email.
3. Show confidence + rationale.
4. Show recommendations.
5. Show evidence panel with the snippets used (search + company site).

## Troubleshooting
- If `/v1/analyze` errors with `GEMINI_API_KEY is not configured`, create `Backend/.env`.
- If browser blocks requests, ensure `VITE_API_BASE_URL` matches the backend URL.
