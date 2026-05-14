import csv
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List


logger = logging.getLogger(__name__)


DOMAIN_REGEX = re.compile(
    r"^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$"
)


@dataclass
class Company:
    company_id: int
    domain: str
    folder_path: str
    status: str = "pending"


def _validate_domain(domain: str) -> str:
    domain = domain.strip()
    # Reject protocol or paths
    if domain.startswith(("http://", "https://")):
        raise ValueError(f"Domain must not include protocol: {domain}")
    if "/" in domain:
        raise ValueError(f"Domain must not include paths: {domain}")
    if not DOMAIN_REGEX.match(domain):
        raise ValueError(f"Invalid domain format: {domain}")
    return domain


def load_companies_from_csv(csv_path: Path, data_dir: Path) -> List[Company]:
    if not csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    data_dir.mkdir(parents=True, exist_ok=True)

    companies: List[Company] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if "domain" not in reader.fieldnames:
            raise ValueError("Input CSV must contain a 'domain' column")

        next_company_id = 1
        for row in reader:
            raw_domain = (row.get("domain") or "").strip()
            if not raw_domain:
                logger.warning("Skipping empty domain row")
                continue
            try:
                domain = _validate_domain(raw_domain)
            except ValueError as e:
                logger.warning("Skipping domain '%s': %s", raw_domain, e)
                continue

            folder_path = str(data_dir / domain)
            company = Company(
                company_id=next_company_id,
                domain=domain,
                folder_path=folder_path,
                status="pending",
            )
            companies.append(company)
            next_company_id += 1

            # Ensure per-company data folder exists
            Path(folder_path).mkdir(parents=True, exist_ok=True)

    logger.info("Loaded %d companies from CSV", len(companies))
    return companies


def write_manifest(companies: List[Company], csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["company_id", "domain", "folder_path", "status"]

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in companies:
            writer.writerow(
                {
                    "company_id": c.company_id,
                    "domain": c.domain,
                    "folder_path": c.folder_path,
                    "status": c.status,
                }
            )

    with json_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(c) for c in companies], f, ensure_ascii=False, indent=2)

    logger.info("Wrote manifest CSV to %s and JSON to %s", csv_path, json_path)


