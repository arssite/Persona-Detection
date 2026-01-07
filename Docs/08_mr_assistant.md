# Mr Assistant (RAG Agent) — Feature Notes

Mr Assistant is an optional, additive layer on top of the existing **Analysis** output.

It is designed for recruiter demos: after running **Analyze**, the UI exposes a second tab (**Mr Assistant**) where the user can ask follow-up questions and receive pitch/meeting coaching.

> Privacy & safety note: Mr Assistant uses **public web signals only** (search snippets + conservative company-site crawl). It avoids claiming certainty and can recommend a refresh only after user confirmation.

## Frontend UX
- The existing **Analyze** flow remains unchanged.
- After an analysis response is available, the UI shows two tabs:
  - **Analysis**: existing cards (confidence, study_of_person, recommendations, evidence)
  - **Mr Assistant**: onboarding + chat
- Mr Assistant includes an **info (i) button** describing capabilities.

## Backend endpoints
All endpoints are under `/v1`.

### `POST /v1/assistant/bootstrap`
Bootstraps a session using:
1) email validation
2) the existing analysis pipeline to create a grounded persona snapshot
3) a coaching generation step that returns starter questions + a pitch plan

Request:
```json
{
  "email": "firstname.lastname@company.com",
  "agenda": {
    "pitch": "What you are pitching/offering",
    "goal": "Desired outcome",
    "meeting_type": "intro call",
    "audience_context": null,
    "constraints": null
  },
  "refresh_public_signals": false
}
```

Response (high level):
- `session_id`
- `starter_questions` (5)
- pitch openers + structure
- objections + responses
- `citations` (subset of evidence)
- `analyze_snapshot` (full analysis object)

### `POST /v1/assistant/chat`
Continues the session.

Request:
```json
{
  "session_id": "...",
  "message": "How should I pitch this to them?",
  "confirm_refresh": false
}
```

If the message is time-sensitive, the backend can respond with:
- `refresh_recommended: true`
- `refresh_reason`

The UI should ask the user to confirm. If confirmed, re-send the same message with `confirm_refresh: true`.

## Session storage (MVP)
Default: in-memory TTL cache.

Optional persistence (SQLite):
- `ASSISTANT_PERSIST=1`
- `ASSISTANT_DB_PATH=assistant_sessions.sqlite3` (optional)

## Guardrails
- No vendor/model disclosure (Mr Assistant identifies itself as a "RAG-style agent")
- Probabilistic language (no false certainty)
- Evidence-aware answers with citations when possible
- Refresh of public signals only after user confirmation

## Troubleshooting
If you see `500` with `error_id=...`:
- Check backend console logs for the full exception with that `error_id`.
- Common causes:
  - Missing `GEMINI_API_KEY` in `Backend/.env`
  - Network problems or provider temporary unavailability
  - Public web sources timing out
