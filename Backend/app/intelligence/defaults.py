from __future__ import annotations


def coalesce_str(v: object, default: str = "unknown") -> str:
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def coalesce_list(v: object) -> list[str]:
    """Coerce unknown input into a list of strings.

    - list -> cleaned list[str]
    - str  -> split on newlines / semicolons / bullets (best-effort)
    - other -> []
    """
    if isinstance(v, list):
        out: list[str] = []
        for x in v:
            xs = str(x).strip()
            if xs:
                out.append(xs)
        return out

    if isinstance(v, str):
        s = v.strip()
        if not s or s.lower() == "unknown":
            return []
        # split common separators
        parts = []
        for chunk in s.replace("\r", "").split("\n"):
            chunk = chunk.strip()
            if not chunk:
                continue
            # remove bullet prefixes
            chunk = chunk.lstrip("-*• ").strip()
            if chunk:
                parts.append(chunk)
        if len(parts) > 1:
            return parts
        # fallback: split on ';'
        if ";" in s:
            return [p.strip() for p in s.split(";") if p.strip()]
        # fallback: split on '.' only if multiple sentences
        if s.count(".") >= 2:
            return [p.strip() for p in s.split(".") if p.strip()]
        return [s]

    return []


def coalesce_dict(v: object) -> dict:
    return v if isinstance(v, dict) else {}
