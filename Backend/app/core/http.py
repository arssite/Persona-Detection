from __future__ import annotations

from fastapi import HTTPException


def bad_gateway(detail: str) -> HTTPException:
    return HTTPException(status_code=502, detail=detail)
