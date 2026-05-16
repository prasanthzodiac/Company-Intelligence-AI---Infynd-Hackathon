"""Normalize domains from CSV and URLs."""
from __future__ import annotations

import re

DOMAIN_REGEX = re.compile(r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$")


def normalize_domain(raw: str) -> str:
    """
    Clean domain for storage and API keys.
    Strips protocol, paths, and leading www.
    """
    domain = (raw or "").strip().lower()
    if domain.startswith("http://"):
        domain = domain[7:]
    elif domain.startswith("https://"):
        domain = domain[8:]
    domain = domain.split("/")[0].split("?")[0].strip()
    if domain.startswith("www."):
        domain = domain[4:]
    if not DOMAIN_REGEX.match(domain):
        raise ValueError(f"Invalid domain format: {domain}")
    return domain


def crawl_hosts(domain: str) -> list[str]:
    """Hostnames to try when downloading (www + apex)."""
    hosts = [domain]
    www = f"www.{domain}"
    if www not in hosts:
        hosts.insert(0, www)
    return hosts


def display_company_name(domain: str, profile_name: str | None = None) -> str:
    if profile_name and str(profile_name).strip() and profile_name.strip().lower() not in (
        "unknown",
        "www",
    ):
        return profile_name.strip()
    base = domain.replace(".co.uk", "").split(".")[0] or domain
    if base in ("www", ""):
        return domain
    return base.replace("-", " ").title()
