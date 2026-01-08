from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMRateLimit:
    retry_after_seconds: int | None = None


def is_rate_limited_error(exc: Exception) -> bool:
    msg = str(exc)
    return (
        "RESOURCE_EXHAUSTED" in msg
        or "quota" in msg.lower()
        or "rate limit" in msg.lower()
        or "429" in msg
    )


def parse_retry_after_seconds(exc: Exception) -> int | None:
    """Best-effort extraction of retry delay from common SDK error strings.

    Examples we try to handle:
    - "Please retry in 30.20297s."
    - "retryDelay': '30s'"
    """

    msg = str(exc)

    # "Please retry in 30.2029s"
    m = re.search(r"retry in\s+([0-9]+(?:\.[0-9]+)?)s", msg, flags=re.IGNORECASE)
    if m:
        try:
            return max(1, int(float(m.group(1))))
        except Exception:
            return None

    # "retryDelay': '30s'" or "retryDelay": "30s"
    m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]([0-9]+)s['\"]", msg)
    if m:
        try:
            return max(1, int(m.group(1)))
        except Exception:
            return None

    return None
