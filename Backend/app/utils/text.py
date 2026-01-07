from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()
