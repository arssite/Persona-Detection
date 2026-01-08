from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.cache import TTLCache


@dataclass
class AssistantSession:
    session_id: str
    created_at: float
    email: str
    agenda: dict[str, Any]
    analyze_snapshot: dict[str, Any]
    chat_history: list[dict[str, str]]


_SESSION_CACHE: TTLCache[AssistantSession] = TTLCache(ttl_s=60 * 60, max_items=512)  # 1 hour


def _persist_enabled() -> bool:
    return os.getenv("ASSISTANT_PERSIST", "0").strip() == "1"


def _db_path() -> str:
    return os.getenv("ASSISTANT_DB_PATH", "assistant_sessions.sqlite3")


def _ensure_db() -> None:
    if not _persist_enabled():
        return

    conn = sqlite3.connect(_db_path())
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assistant_sessions (
              session_id TEXT PRIMARY KEY,
              created_at REAL NOT NULL,
              email TEXT NOT NULL,
              agenda_json TEXT NOT NULL,
              analyze_json TEXT NOT NULL,
              chat_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def new_session(*, email: str, agenda: dict[str, Any], analyze_snapshot: dict[str, Any]) -> AssistantSession:
    session_id = str(uuid.uuid4())
    s = AssistantSession(
        session_id=session_id,
        created_at=time.time(),
        email=email,
        agenda=agenda,
        analyze_snapshot=analyze_snapshot,
        chat_history=[],
    )
    _SESSION_CACHE.set(session_id, s)

    if _persist_enabled():
        _ensure_db()
        conn = sqlite3.connect(_db_path())
        try:
            conn.execute(
                "INSERT OR REPLACE INTO assistant_sessions (session_id, created_at, email, agenda_json, analyze_json, chat_json) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    s.session_id,
                    s.created_at,
                    s.email,
                    json.dumps(s.agenda, ensure_ascii=False),
                    json.dumps(s.analyze_snapshot, ensure_ascii=False),
                    json.dumps(s.chat_history, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    return s


def get_session(session_id: str) -> AssistantSession | None:
    s = _SESSION_CACHE.get(session_id)
    if s is not None:
        return s

    if not _persist_enabled():
        return None

    _ensure_db()
    conn = sqlite3.connect(_db_path())
    try:
        row = conn.execute(
            "SELECT session_id, created_at, email, agenda_json, analyze_json, chat_json FROM assistant_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        s = AssistantSession(
            session_id=row[0],
            created_at=float(row[1]),
            email=row[2],
            agenda=json.loads(row[3]),
            analyze_snapshot=json.loads(row[4]),
            chat_history=json.loads(row[5]),
        )
        _SESSION_CACHE.set(session_id, s)
        return s
    finally:
        conn.close()


def append_chat(session_id: str, role: str, content: str) -> None:
    s = get_session(session_id)
    if s is None:
        return
    s.chat_history.append({"role": role, "content": content})
    # Keep last N turns for prompt size control
    if len(s.chat_history) > 16:
        s.chat_history = s.chat_history[-16:]

    _SESSION_CACHE.set(session_id, s)

    if _persist_enabled():
        _ensure_db()
        conn = sqlite3.connect(_db_path())
        try:
            conn.execute(
                "UPDATE assistant_sessions SET chat_json = ? WHERE session_id = ?",
                (json.dumps(s.chat_history, ensure_ascii=False), session_id),
            )
            conn.commit()
        finally:
            conn.close()
