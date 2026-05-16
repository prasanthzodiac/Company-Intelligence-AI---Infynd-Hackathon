"""Request session resolution for ephemeral API data."""
from __future__ import annotations

from flask import abort, request

from services.session_store import (
    SessionPaths,
    create_session,
    get_session_paths,
    session_exists,
    touch_session,
    validate_session_id,
)


def require_session_id(repo_base) -> str:
    sid = (request.headers.get("X-Session-Id") or "").strip()
    if not sid or not validate_session_id(sid):
        abort(401, description="Missing or invalid X-Session-Id header")
    if not session_exists(repo_base, sid):
        abort(401, description="Session expired or not found — refresh the page")
    touch_session(repo_base, sid)
    return sid


def optional_session_id(repo_base) -> str | None:
    sid = (request.headers.get("X-Session-Id") or "").strip()
    if not sid or not validate_session_id(sid) or not session_exists(repo_base, sid):
        return None
    touch_session(repo_base, sid)
    return sid


def paths_for_request(repo_base) -> SessionPaths:
    return get_session_paths(repo_base, require_session_id(repo_base))
