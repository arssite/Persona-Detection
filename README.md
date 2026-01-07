# Persona-Detection (Meeting Intelligence MVP)

This repo contains an MVP that turns a corporate email into AI-inferred meeting intelligence using public web signals.

## Structure
- `Backend/` - FastAPI server
- `Frontend/` - React + TypeScript UI (Vite)
- `Docs/` - step-by-step docs and runbook

## Quickstart

### Backend

```bash
cd Persona-Detection/Backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Configure Gemini
copy .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
# edit .env and set GEMINI_API_KEY

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd Persona-Detection/Frontend
npm install
# Create .env with VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open the Vite URL (typically `http://localhost:5173`).

## Docs
Start with:
- `Docs/00_overview.md`
- `Docs/04_demo_runbook.md`
