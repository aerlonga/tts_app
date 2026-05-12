from __future__ import annotations

from fastapi import Request


def resolve_gemini_api_key(request: Request, explicit_api_key: str | None = None) -> str | None:
    direct_key = (explicit_api_key or "").strip()
    if direct_key:
        return direct_key

    session = getattr(request, "session", None) or {}
    session_key = str(session.get("gemini_api_key") or "").strip()
    return session_key or None
