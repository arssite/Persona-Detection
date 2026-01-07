# Backend (FastAPI)

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create `Backend/.env` (not committed):

```env
GEMINI_API_KEY=your_key_here
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

## Endpoints
- `GET /health`
- `POST /analyze`
