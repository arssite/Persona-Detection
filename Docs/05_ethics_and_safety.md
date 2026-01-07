# Ethics & Safety

## Public-data-only policy
This MVP is designed to:
- use **public web content** only
- avoid paid enrichment APIs
- avoid scraping authenticated/behind-login pages

## Uncertainty handling
Outputs must be framed as AI inference:
- use probabilistic language ("likely", "appears")
- show a confidence label (low/medium/high)
- show rationale and evidence snippets (when implemented)

## Privacy
- Do not store personal data long-term in MVP
- `.env` files are gitignored
- Logs should avoid storing raw emails if not necessary
