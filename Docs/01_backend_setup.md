# Backend Setup (FastAPI)

## Prerequisites
- Python 3.10+ recommended

## Install

```bash
cd Persona-Detection/Backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Configure Gemini

1. Create a Gemini API key in Google AI Studio / Google Cloud.
2. Create `Persona-Detection/Backend/.env` (this file is gitignored):

```env
GEMINI_API_KEY=YOUR_KEY
GEMINI_MODEL=gemini-2.5-flash
```

Security note:
- Never commit `.env`
- If a key is accidentally shared publicly, revoke/rotate it immediately.

## Run

```bash
cd Persona-Detection/Backend
uvicorn app.main:app --reload --port 8000
```

## Test quickly
- `GET http://localhost:8000/health`
- `POST http://localhost:8000/v1/analyze` with JSON body:

```json
{ "email": "firstname.lastname@company.com" }
```
