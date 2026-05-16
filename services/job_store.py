"""Persist pipeline job status on disk (safe across Gunicorn workers)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .session_store import get_session_paths, validate_session_id

logger = logging.getLogger(__name__)

# Same-process cache (optional; disk is source of truth)
_memory: Dict[str, Dict[str, Any]] = {}

TERMINAL_STAGES = frozenset({"complete", "error"})


def _job_path(repo_base: Path, session_id: str, job_id: str) -> Path:
    return get_session_paths(repo_base, session_id).root / "jobs" / f"{job_id}.json"


def write_job_status(
    repo_base: Path,
    session_id: str,
    job_id: str,
    status: Dict[str, Any],
) -> None:
    if not validate_session_id(session_id):
        return
    payload = {**status, "session_id": session_id, "job_id": job_id}
    path = _job_path(repo_base, session_id, job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    _memory[job_id] = payload


def read_job_status(
    repo_base: Path,
    job_id: str,
    session_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    cached = _memory.get(job_id)
    if cached:
        if session_id and cached.get("session_id") != session_id:
            return None
        return dict(cached)

    if session_id and validate_session_id(session_id):
        path = _job_path(repo_base, session_id, job_id)
        if path.is_file():
            return _load_job_file(path, job_id, session_id)

    # Find job under any session folder (poll without header edge case)
    sessions_dir = repo_base / "sessions"
    if not sessions_dir.is_dir():
        return None
    for session_dir in sessions_dir.iterdir():
        if not session_dir.is_dir() or not validate_session_id(session_dir.name):
            continue
        if session_id and session_dir.name != session_id:
            continue
        path = session_dir / "jobs" / f"{job_id}.json"
        if path.is_file():
            data = _load_job_file(path, job_id, session_dir.name)
            if data and (not session_id or data.get("session_id") == session_id):
                return data
    return None


def _load_job_file(path: Path, job_id: str, session_id: str) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        data.setdefault("job_id", job_id)
        data.setdefault("session_id", session_id)
        _memory[job_id] = data
        return dict(data)
    except Exception as e:
        logger.warning("Could not read job status %s: %s", path, e)
        return {}


def session_has_active_jobs(repo_base: Path, session_id: str) -> bool:
    jobs_dir = get_session_paths(repo_base, session_id).root / "jobs"
    if not jobs_dir.is_dir():
        return False
    for path in jobs_dir.glob("*.json"):
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            stage = (data.get("stage") or "").lower()
            if stage and stage not in TERMINAL_STAGES:
                return True
        except Exception:
            continue
    return False
