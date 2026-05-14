#!/usr/bin/env python3
"""
Test script to verify web scraping and LLM extraction
Tests a single domain to ensure everything works correctly
"""
import json
import logging
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))

from services.csv_loader import Company, load_companies_from_csv
from services.downloader import download_for_company
from services.crawler import crawl_company
from services.llm_extractor import extract_profile_for_company

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test")

def test_single_domain(domain: str):
    """Test scraping and LLM extraction for a single domain"""
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "settings.yaml"
    
    with config_path.open("r", encoding="utf-8") as f:
        settings = yaml.safe_load(f)
    
    data_dir = base_dir / settings["paths"]["data_dir"]
    output_dir = base_dir / settings["paths"]["output_dir"]
    
    # Create a test company
    company = Company(company_id=1, domain=domain, folder_path=data_dir / domain)
    
    logger.info("=" * 80)
    logger.info(f"Testing domain: {domain}")
    logger.info("=" * 80)
    
    # Step 1: Download
    logger.info("\n[STEP 1] Testing download...")
    download_status = download_for_company(company, settings, data_dir)
    logger.info(f"Download status: {download_status}")
    
    if download_status != "downloaded":
        logger.error("Download failed! Cannot continue.")
        return False
    
    # Verify download
    domain_dir = data_dir / domain
    html_files = list(domain_dir.rglob("*.html")) + list(domain_dir.rglob("*.htm"))
    logger.info(f"Downloaded {len(html_files)} HTML files")
    
    if len(html_files) == 0:
        logger.error("No HTML files downloaded!")
        return False
    
    # Step 2: Crawl
    logger.info("\n[STEP 2] Testing crawl...")
    crawl_status = crawl_company(company, data_dir, output_dir, settings)
    logger.info(f"Crawl status: {crawl_status}")
    
    if crawl_status != "crawled":
        logger.error("Crawl failed! Cannot continue.")
        return False
    
    # Verify crawl
    chunks_path = output_dir / domain / "chunks.json"
    if chunks_path.exists():
        with chunks_path.open("r", encoding="utf-8") as f:
            chunks = json.load(f)
        logger.info(f"Extracted {len(chunks)} chunks")
        
        # Show sample chunk
        if chunks:
            sample = chunks[0]
            logger.info(f"\nSample chunk:")
            logger.info(f"  Page: {sample.get('page', 'N/A')}")
            logger.info(f"  Section: {sample.get('section', 'N/A')}")
            logger.info(f"  Text length: {len(sample.get('text', ''))} chars")
            logger.info(f"  Text preview: {sample.get('text', '')[:200]}...")
    else:
        logger.error("chunks.json not created!")
        return False
    
    # Step 3: LLM Extraction
    logger.info("\n[STEP 3] Testing LLM extraction...")
    llm_status = extract_profile_for_company(company, output_dir, settings, base_dir)
    logger.info(f"LLM extraction status: {llm_status}")
    
    if llm_status != "profile_generated":
        logger.error("LLM extraction failed!")
        return False
    
    # Verify profile
    profile_path = output_dir / domain / "profile.json"
    if profile_path.exists():
        with profile_path.open("r", encoding="utf-8") as f:
            profile = json.load(f)
        
        logger.info(f"\n[VERIFICATION] Profile generated successfully!")
        logger.info(f"\nProfile Summary:")
        logger.info(f"  Company Name: {profile.get('company_name', 'N/A')}")
        logger.info(f"  Domain: {profile.get('domain', 'N/A')}")
        logger.info(f"  Industry: {profile.get('industry', 'N/A')}")
        logger.info(f"  Description (short): {profile.get('description_short', 'N/A')[:100]}...")
        logger.info(f"  Services: {len(profile.get('services', []))} items")
        logger.info(f"  Contact Email: {profile.get('contact', {}).get('email', 'N/A')}")
        logger.info(f"  Contact Phone: {profile.get('contact', {}).get('phone', 'N/A')}")
        logger.info(f"  Social Links: {len([k for k, v in profile.get('social', {}).items() if v])} found")
        logger.info(f"  People: {len(profile.get('people', []))} found")
        logger.info(f"  Certifications: {len(profile.get('certifications', []))} found")
        logger.info(f"  Extraction Confidence: {profile.get('extraction_confidence', 0.0)}")
        
        # Check quality
        quality_score = 0
        if profile.get('company_name') and profile.get('company_name') != 'Unknown':
            quality_score += 1
        if profile.get('description_long'):
            quality_score += 1
        if profile.get('industry'):
            quality_score += 1
        if profile.get('services') and len(profile.get('services', [])) > 0:
            quality_score += 1
        if profile.get('contact', {}).get('email') or profile.get('contact', {}).get('phone'):
            quality_score += 1
        
        logger.info(f"\nQuality Score: {quality_score}/5")
        
        if quality_score >= 3:
            logger.info("[OK] Profile quality is GOOD")
        elif quality_score >= 2:
            logger.info("[FAIR] Profile quality is FAIR")
        else:
            logger.warning("[POOR] Profile quality is POOR")
        
        return True
    else:
        logger.error("profile.json not created!")
        return False

if __name__ == "__main__":
    # Test with a small, simple domain
    test_domain = "acassure.com"  # Known to have data
    
    logger.info("Starting web scraping and LLM extraction test...")
    logger.info(f"Test domain: {test_domain}")
    logger.info("Make sure Ollama is running with llama3 model!")
    
    success = test_single_domain(test_domain)
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("[SUCCESS] ALL TESTS PASSED!")
        logger.info("=" * 80)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 80)
        logger.error("[FAILED] TESTS FAILED!")
        logger.error("=" * 80)
        sys.exit(1)

