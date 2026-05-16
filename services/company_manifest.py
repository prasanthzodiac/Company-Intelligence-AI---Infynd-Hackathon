"""
Company manifest for a single ephemeral session (no global output/ scan).
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .csv_loader import Company, write_manifest
from .session_store import SessionPaths

logger = logging.getLogger(__name__)


def _status_for_output_dir(domain_dir: Path) -> str:
    profile = domain_dir / "profile.json"
    chunks = domain_dir / "chunks.json"
    if profile.exists() and profile.stat().st_size > 10:
        return "profile_generated"
    if chunks.exists() and chunks.stat().st_size > 10:
        return "crawled"
    return "pending"


def list_companies_from_output(paths: SessionPaths) -> List[Dict[str, Any]]:
    output_dir = paths.output_dir
    if not output_dir.is_dir():
        return []

    rows: List[Dict[str, Any]] = []
    for idx, domain_dir in enumerate(sorted(output_dir.iterdir()), start=1):
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name
        if not (domain_dir / "profile.json").exists() and not (
            domain_dir / "chunks.json"
        ).exists():
            continue
        rows.append(
            {
                "company_id": idx,
                "domain": domain,
                "folder_path": str(paths.data_dir / domain),
                "status": _status_for_output_dir(domain_dir),
            }
        )
    return rows


def load_companies_manifest(paths: SessionPaths) -> List[Dict[str, Any]]:
    companies: List[Dict[str, Any]] = []
    if paths.manifest_json.exists():
        try:
            with paths.manifest_json.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                companies = loaded
        except Exception as e:
            logger.warning("Could not read %s: %s", paths.manifest_json, e)

    by_domain = {c.get("domain"): c for c in companies if c.get("domain")}
    for row in list_companies_from_output(paths):
        domain = row["domain"]
        if domain not in by_domain:
            by_domain[domain] = row
        else:
            existing = by_domain[domain]
            if existing.get("status") == "pending" and row.get("status") != "pending":
                existing["status"] = row["status"]

    merged = list(by_domain.values())
    merged.sort(key=lambda c: (c.get("company_id") or 0, c.get("domain") or ""))
    for i, c in enumerate(merged, start=1):
        c["company_id"] = i
    return merged


def save_companies_manifest(paths: SessionPaths, companies: List[Company]) -> None:
    paths.root.mkdir(parents=True, exist_ok=True)
    write_manifest(companies, paths.manifest_csv, paths.manifest_json)
