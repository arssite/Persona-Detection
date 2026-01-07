from __future__ import annotations

import re
from dataclasses import dataclass


_CORP_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class ParsedEmail:
    raw: str
    is_valid: bool
    local_part: str | None
    domain: str | None
    guessed_first_name: str | None
    guessed_last_name: str | None


def _guess_name(local_part: str) -> tuple[str | None, str | None]:
    # Best-effort: firstname.lastname or firstname_lastname
    cleaned = re.sub(r"[^a-zA-Z0-9._-]", "", local_part)
    for sep in [".", "_", "-"]:
        if sep in cleaned:
            parts = [p for p in cleaned.split(sep) if p]
            if len(parts) >= 2:
                return parts[0].title(), parts[1].title()
    return None, None


def parse_email(email: str) -> ParsedEmail:
    email = (email or "").strip()
    if not _CORP_EMAIL_RE.match(email):
        return ParsedEmail(raw=email, is_valid=False, local_part=None, domain=None,
                           guessed_first_name=None, guessed_last_name=None)

    local, domain = email.split("@", 1)
    # Very light "corporate" heuristic: block common free providers
    free_domains = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "proton.me", "protonmail.com"}
    if domain.lower() in free_domains:
        return ParsedEmail(raw=email, is_valid=False, local_part=local, domain=domain,
                           guessed_first_name=None, guessed_last_name=None)

    first, last = _guess_name(local)
    return ParsedEmail(raw=email, is_valid=True, local_part=local, domain=domain,
                       guessed_first_name=first, guessed_last_name=last)
