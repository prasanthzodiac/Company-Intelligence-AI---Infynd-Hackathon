"""Resolve output/data paths when CSV domain differs from stored folder name."""
from __future__ import annotations

from pathlib import Path


def domain_folder_variants(domain: str) -> list[str]:
    domain = (domain or "").strip().lower()
    variants = [domain]
    if domain.startswith("www."):
        bare = domain[4:]
        if bare not in variants:
            variants.append(bare)
    else:
        www = f"www.{domain}"
        if www not in variants:
            variants.append(www)
    return variants


def resolve_domain_dir(parent: Path, domain: str) -> Path:
    """Pick existing subfolder for domain (handles www vs apex)."""
    for variant in domain_folder_variants(domain):
        candidate = parent / variant
        if candidate.is_dir():
            return candidate
    return parent / (domain or "").strip().lower()
