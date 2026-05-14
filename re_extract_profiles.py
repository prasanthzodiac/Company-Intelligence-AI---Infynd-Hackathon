#!/usr/bin/env python3
"""
Re-extract profiles for companies with empty or minimal data
"""
import json
import logging
import yaml
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from services.llm_extractor import extract_profile_for_company
from services.csv_loader import Company, load_companies_from_csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def is_profile_empty(profile_path: Path) -> bool:
    """Check if profile is mostly empty"""
    try:
        with profile_path.open('r', encoding='utf-8') as f:
            profile = json.load(f)
        
        # Check key fields
        has_name = bool(profile.get('company_name', '').strip())
        has_description = bool(profile.get('description_long', '').strip())
        has_services = len(profile.get('services', [])) > 0
        has_contact = bool(profile.get('contact', {}).get('email', '').strip()) or bool(profile.get('contact', {}).get('phone', '').strip())
        
        # Profile is considered empty if it has less than 2 of these key fields
        filled_fields = sum([has_name, has_description, has_services, has_contact])
        return filled_fields < 2
    except Exception as e:
        logger.error(f"Error checking profile {profile_path}: {e}")
        return True


def load_settings(base_dir: Path) -> dict:
    """Load settings from YAML"""
    settings_path = base_dir / "config" / "settings.yaml"
    with settings_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    base_dir = Path(__file__).parent
    settings = load_settings(base_dir)
    
    # Load companies
    csv_path = base_dir / "domains.csv"
    companies = load_companies_from_csv(csv_path, base_dir)
    
    output_dir = base_dir / settings["paths"]["output_dir"]
    data_dir = base_dir / settings["paths"]["data_dir"]
    
    # Find companies with empty profiles
    companies_to_reprocess = []
    for company in companies:
        profile_path = output_dir / company.domain / "profile.json"
        chunks_path = output_dir / company.domain / "chunks.json"
        
        if profile_path.exists() and chunks_path.exists():
            if is_profile_empty(profile_path):
                logger.info(f"Found empty profile for {company.domain}, will re-extract")
                companies_to_reprocess.append(company)
        elif chunks_path.exists():
            logger.info(f"Found chunks but no profile for {company.domain}, will extract")
            companies_to_reprocess.append(company)
    
    if not companies_to_reprocess:
        logger.info("No companies need re-extraction")
        return
    
    logger.info(f"Re-extracting profiles for {len(companies_to_reprocess)} companies...")
    
    for company in companies_to_reprocess:
        logger.info(f"Re-extracting profile for {company.domain}...")
        try:
            result = extract_profile_for_company(company, output_dir, settings, base_dir)
            logger.info(f"Result for {company.domain}: {result}")
        except Exception as e:
            logger.error(f"Error re-extracting {company.domain}: {e}")


if __name__ == "__main__":
    main()

