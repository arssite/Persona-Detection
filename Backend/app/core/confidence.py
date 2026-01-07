from __future__ import annotations

from typing import Sequence


def fallback_confidence(evidence: Sequence[dict]) -> dict:
    """Deterministic fallback when the model doesn't provide valid confidence."""
    n = len(evidence)
    sources = {str(e.get("source", "")) for e in evidence}

    # simple heuristic
    if n >= 6 and "company_site" in sources:
        return {"label": "high", "rationale": "Multiple public signals found including company website pages."}
    if n >= 3:
        return {"label": "medium", "rationale": "Some public signals found, mostly from search snippets."}
    return {"label": "low", "rationale": "Limited public signals found; recommendations are highly uncertain."}
