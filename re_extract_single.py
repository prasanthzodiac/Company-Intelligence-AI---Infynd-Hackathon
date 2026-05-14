#!/usr/bin/env python3
"""
Re-extract profile for a single company using improved LLM extraction.
Usage: python re_extract_single.py <domain>
"""
import sys
import logging
from pathlib import Path
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.csv_loader import load_companies_from_csv, Company
from services.llm_extractor import extract_profile_for_company

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("reextract")

def main():
    if len(sys.argv) < 2:
        print("Usage: python re_extract_single.py <domain>")
        print("Example: python re_extract_single.py acorncompliance.com")
        sys.exit(1)
    
    target_domain = sys.argv[1].strip()
    base_dir = Path(__file__).parent
    
    # Load settings
    settings_path = base_dir / "config" / "settings.yaml"
    with settings_path.open("r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    
    output_dir = base_dir / settings["paths"]["output_dir"]
    
    # Load companies
    csv_path = base_dir / "domains.csv"
    data_dir = base_dir / settings["paths"]["data_dir"]
    companies = load_companies_from_csv(csv_path, data_dir)
    
    # Find the target company
    target_company = None
    for company in companies:
        if company.domain == target_domain:
            target_company = company
            break
    
    if not target_company:
        logger.error(f"Company with domain '{target_domain}' not found in domains.csv")
        sys.exit(1)
    
    # Check if chunks exist
    chunks_path = output_dir / target_domain / "chunks.json"
    if not chunks_path.exists():
        logger.error(f"Chunks file not found for {target_domain}. Please run download and crawl first.")
        sys.exit(1)
    
    logger.info(f"Re-extracting profile for {target_domain}...")
    try:
        status = extract_profile_for_company(target_company, output_dir, settings, base_dir)
        logger.info(f"Re-extraction result for {target_domain}: {status}")
        if status == "profile_generated":
            logger.info(f"✓ Profile successfully re-extracted! Check output/{target_domain}/profile.json")
        else:
            logger.warning(f"✗ Re-extraction failed. Check logs for details.")
    except Exception as e:
        logger.error(f"Error re-extracting {target_domain}: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

