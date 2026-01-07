from __future__ import annotations

import json
from typing import Any


def try_parse_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Parse JSON text. Returns (data, error)."""
    if not text:
        return None, "empty response"

    # Some models may wrap JSON in code fences; strip if present.
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        # also remove optional 'json' label
        stripped = stripped.replace("json\n", "", 1)

    try:
        return json.loads(stripped), None
    except json.JSONDecodeError as e:
        return None, f"invalid json: {e}"
