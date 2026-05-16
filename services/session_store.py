"""
Ephemeral per-browser sessions: all crawl/LLM data lives under sessions/<id>/ and is deleted on demand.
"""
from __future__ import annotations

import logging
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import uuid

logger = logging.getLogger(__name__)

SESSION_ID_RE = re.compile(r"^[a-f0-9]{32}$")
DEFAULT_TTL_SECONDS = 24 * 3600


@dataclass
class SessionPaths:
    session_id: str
    root: Path
    data_dir: Path
    output_dir: Path

    @property
    def manifest_json(self) -> Path:
        return self.root / "companies.json"

    @property
    def manifest_csv(self) -> Path:
        return self.root / "companies.csv"


def sessions_root(repo_base: Path) -> Path:
    return repo_base / "sessions"


def validate_session_id(session_id: str) -> bool:
    return bool(session_id and SESSION_ID_RE.match(session_id))


def create_session(repo_base: Path) -> SessionPaths:
    session_id = uuid.uuid4().hex
    paths = get_session_paths(repo_base, session_id)
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Created session %s at %s", session_id, paths.root)
    return paths


def get_session_paths(repo_base: Path, session_id: str) -> SessionPaths:
    if not validate_session_id(session_id):
        raise ValueError("Invalid session id")
    root = sessions_root(repo_base) / session_id
    return SessionPaths(
        session_id=session_id,
        root=root,
        data_dir=root / "data",
        output_dir=root / "output",
    )


def session_exists(repo_base: Path, session_id: str) -> bool:
    if not validate_session_id(session_id):
        return False
    return get_session_paths(repo_base, session_id).root.is_dir()


def delete_session(repo_base: Path, session_id: str) -> bool:
    if not validate_session_id(session_id):
        return False
    root = get_session_paths(repo_base, session_id).root
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
        logger.info("Deleted session %s", session_id)
        return True
    return False


def cleanup_stale_sessions(
    repo_base: Path, max_age_seconds: int = DEFAULT_TTL_SECONDS
) -> int:
    """Remove session folders older than max_age (safety net if browser close beacon fails)."""
    root = sessions_root(repo_base)
    if not root.is_dir():
        return 0
    cutoff = time.time() - max_age_seconds
    removed = 0
    for entry in root.iterdir():
        if not entry.is_dir() or not validate_session_id(entry.name):
            continue
        try:
            if entry.stat().st_mtime < cutoff:
                shutil.rmtree(entry, ignore_errors=True)
                removed += 1
        except OSError as e:
            logger.warning("Could not stat session %s: %s", entry.name, e)
    if removed:
        logger.info("Cleaned up %d stale sessions", removed)
    return removed


def touch_session(repo_base: Path, session_id: str) -> None:
    """Update folder mtime so TTL cleanup respects active use."""
    root = get_session_paths(repo_base, session_id).root
    if root.exists():
        root.mkdir(parents=True, exist_ok=True)
        try:
            root.touch()
        except OSError:
            pass
