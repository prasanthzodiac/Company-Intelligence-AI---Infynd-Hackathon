"""
Build and read the company manifest (data/companies.json) from CSV pipeline and output/.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .csv_loader import Company, write_manifest

logger = logging.getLogger(__name__)


def _status_for_output_dir(domain_dir: Path) -> str:
    profile = domain_dir / "profile.json"
    chunks = domain_dir / "chunks.json"
    if profile.exists() and profile.stat().st_size > 10:
        return "profile_generated"
    if chunks.exists() and chunks.stat().st_size > 10:
        return "crawled"
    return "pending"


def list_companies_from_output(base_dir: Path) -> List[Dict[str, Any]]:
    """Discover companies from output/<domain>/ profiles or chunks."""
    output_dir = base_dir / "output"
    if not output_dir.is_dir():
        return []

    rows: List[Dict[str, Any]] = []
    data_dir = base_dir / "data"
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
                "folder_path": str(data_dir / domain),
                "status": _status_for_output_dir(domain_dir),
            }
        )
    return rows


def load_companies_manifest(base_dir: Path) -> List[Dict[str, Any]]:
    """
    Return all companies: manifest JSON merged with any domains found under output/.
    """
    manifest_path = base_dir / "data" / "companies.json"
    companies: List[Dict[str, Any]] = []

    if manifest_path.exists():
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                companies = loaded
        except Exception as e:
            logger.warning("Could not read %s: %s", manifest_path, e)

    by_domain = {c.get("domain"): c for c in companies if c.get("domain")}
    for row in list_companies_from_output(base_dir):
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


def save_companies_manifest(base_dir: Path, companies: List[Company]) -> None:
    manifest_csv = base_dir / "data" / "companies.csv"
    manifest_json = base_dir / "data" / "companies.json"
    write_manifest(companies, manifest_csv, manifest_json)


def sync_manifest_from_output(base_dir: Path) -> List[Dict[str, Any]]:
    """Rebuild manifest from output/ and return company list."""
    rows = list_companies_from_output(base_dir)
    if not rows:
        return load_companies_manifest(base_dir)

    companies = [
        Company(
            company_id=r["company_id"],
            domain=r["domain"],
            folder_path=r["folder_path"],
            status=r.get("status", "pending"),
        )
        for r in rows
    ]
    save_companies_manifest(base_dir, companies)
    logger.info("Synced manifest with %d companies from output/", len(companies))
    return [asdict(c) for c in companies]
