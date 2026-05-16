"""Write profile.json when scrape/LLM steps fail or partial data exists."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from .llm_extractor import (
    _calculate_extraction_confidence,
    _default_profile_schema,
    _fallback_profile_from_chunks,
)

logger = logging.getLogger(__name__)


def write_status_profile(
    output_dir: Path,
    domain: str,
    status: str,
    message: str,
) -> None:
    domain_dir = output_dir / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    profile = _default_profile_schema(domain)
    profile["company_name"] = domain.split(".")[0].replace("-", " ").title()
    profile["pipeline_status"] = status
    profile["pipeline_message"] = message
    profile["extraction_confidence"] = 0.0
    path = domain_dir / "profile.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    logger.info("Wrote status profile for %s: %s", domain, status)


def write_profile_from_chunks(output_dir: Path, domain: str) -> bool:
    chunks_path = output_dir / domain / "chunks.json"
    if not chunks_path.exists():
        return False
    try:
        with chunks_path.open("r", encoding="utf-8") as f:
            chunks = json.load(f)
    except Exception as e:
        logger.warning("Could not read chunks for %s: %s", domain, e)
        return False
    if not chunks:
        return False
    profile = _fallback_profile_from_chunks(domain, chunks)
    profile["data_source"] = "scraped_chunks"
    profile["pipeline_status"] = "crawled"
    profile["extraction_confidence"] = _calculate_extraction_confidence(profile)
    path = output_dir / domain / "profile.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)
    return True
