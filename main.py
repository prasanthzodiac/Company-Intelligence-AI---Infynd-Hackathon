import argparse
import json
import logging
import multiprocessing
from pathlib import Path
import sys
from typing import Dict, Tuple

import yaml

from services.csv_loader import Company, load_companies_from_csv, write_manifest
from services.downloader import download_for_company
from services.crawler import crawl_company
from services.llm_extractor import extract_profile_for_company


def setup_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "run.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_settings(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_downloaded(domain_dir: Path) -> bool:
    """Check if website is already downloaded (has HTML files with content)."""
    if not domain_dir.exists():
        return False
    html_files = list(domain_dir.rglob("*.html")) + list(domain_dir.rglob("*.htm"))
    if not html_files:
        return False
    # Verify at least one file has content
    for html_file in html_files[:3]:
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore").strip()
            if len(content) > 100:
                return True
        except Exception:
            continue
    return False


def check_scraped(chunks_path: Path) -> bool:
    """Check if website is already scraped (has chunks.json with content)."""
    if not chunks_path.exists():
        return False
    try:
        with chunks_path.open("r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        if chunks_data and isinstance(chunks_data, list) and len(chunks_data) > 0:
            # Verify chunks have actual text content
            valid_chunks = [c for c in chunks_data if c.get("text", "").strip() and len(c.get("text", "").strip()) > 20]
            return len(valid_chunks) > 0
    except Exception:
        pass
    return False


def process_company_llm(args: Tuple) -> Tuple[int, str, str]:
    """Process LLM extraction for a single company (for parallel processing)"""
    company, output_dir, settings, base_dir = args
    
    # Setup per-process logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger = logging.getLogger(f"llm-worker-{company.company_id}")
    
    try:
        chunks_path = output_dir / company.domain / "chunks.json"
        if not chunks_path.exists():
            logger.error("chunks.json not found for %s", company.domain)
            return (company.company_id, company.domain, "failed_crawl")
        
        # Validate chunks before LLM processing
        try:
            import json
            with chunks_path.open("r", encoding="utf-8") as f:
                chunks_data = json.load(f)
            if not chunks_data or len(chunks_data) == 0:
                logger.error("chunks.json is empty for %s", company.domain)
                return (company.company_id, company.domain, "failed_crawl")
            logger.info("Processing LLM for %s with %d chunks", company.domain, len(chunks_data))
        except Exception as e:
            logger.error("Could not validate chunks.json for %s: %s", company.domain, e)
            return (company.company_id, company.domain, "failed_crawl")
        
        status = extract_profile_for_company(company, output_dir, settings, base_dir)
        logger.info("LLM extraction completed for %s: %s", company.domain, status)
        return (company.company_id, company.domain, status)
    except Exception as e:
        logger.exception("LLM exception for %s: %s", company.domain, e)
        return (company.company_id, company.domain, "failed_llm")


def process_company_download_crawl(args: Tuple[Company, Dict, Path, Path]) -> Tuple[int, str, str]:
    """
    Worker function for parallel download and crawl processing.
    Returns: (company_id, domain, status)
    """
    company, settings, data_dir, output_dir = args
    
    # Setup per-process logging with proper initialization
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    logger = logging.getLogger(f"worker-{company.company_id}")
    
    try:
        domain_dir = data_dir / company.domain
        chunks_path = output_dir / company.domain / "chunks.json"
        
        # Check if already downloaded and scraped
        is_downloaded = check_downloaded(domain_dir)
        is_scraped = check_scraped(chunks_path)
        
        if is_downloaded and is_scraped:
            logger.info("Skipping %s: already downloaded and scraped", company.domain)
            return (company.company_id, company.domain, "crawled")
        
        # Download if needed
        if not is_downloaded:
            logger.info("Downloading %s (worker %d)", company.domain, company.company_id)
            try:
                download_status = download_for_company(company, settings, data_dir)
                if download_status != "downloaded":
                    logger.error("Download failed for %s: %s", company.domain, download_status)
                    return (company.company_id, company.domain, download_status)
                
                # Validate download with better checks
                if not domain_dir.exists():
                    logger.error("Validation failed: Domain directory not created for %s", company.domain)
                    return (company.company_id, company.domain, "failed_download")
                
                html_files = list(domain_dir.rglob("*.html")) + list(domain_dir.rglob("*.htm"))
                if not html_files:
                    logger.error("Validation failed: No HTML files found for %s", company.domain)
                    return (company.company_id, company.domain, "failed_download")
                
                # Verify at least one file has content
                has_content = False
                for html_file in html_files[:10]:
                    try:
                        content = html_file.read_text(encoding="utf-8", errors="ignore").strip()
                        if len(content) > 100:
                            has_content = True
                            break
                    except Exception:
                        continue
                
                if not has_content:
                    logger.error("Validation failed: No HTML files with content for %s", company.domain)
                    return (company.company_id, company.domain, "failed_download")
                
                logger.info("Download validated: %d HTML files for %s", len(html_files), company.domain)
            except Exception as e:
                logger.exception("Download exception for %s: %s", company.domain, e)
                return (company.company_id, company.domain, "failed_download")
        else:
            logger.info("Skipping download for %s: already downloaded", company.domain)
        
        # Crawl if needed
        if not is_scraped:
            logger.info("Crawling %s (worker %d)", company.domain, company.company_id)
            try:
                crawl_status = crawl_company(company, data_dir, output_dir, settings)
                if crawl_status != "crawled":
                    logger.error("Crawl failed for %s: %s", company.domain, crawl_status)
                    return (company.company_id, company.domain, crawl_status)
                
                # Validate crawl output
                if not chunks_path.exists():
                    logger.error("Validation failed: chunks.json not created for %s", company.domain)
                    return (company.company_id, company.domain, "failed_crawl")
                
                try:
                    import json
                    with chunks_path.open("r", encoding="utf-8") as f:
                        chunks_data = json.load(f)
                    if not chunks_data or len(chunks_data) == 0:
                        logger.error("Validation failed: chunks.json is empty for %s", company.domain)
                        return (company.company_id, company.domain, "failed_crawl")
                    logger.info("Crawl validated: %d chunks for %s", len(chunks_data), company.domain)
                except Exception as e:
                    logger.error("Validation failed: Could not read chunks.json for %s: %s", company.domain, e)
                    return (company.company_id, company.domain, "failed_crawl")
            except Exception as e:
                logger.exception("Crawl exception for %s: %s", company.domain, e)
                return (company.company_id, company.domain, "failed_crawl")
        else:
            logger.info("Skipping crawl for %s: already scraped", company.domain)
            return (company.company_id, company.domain, "crawled")
        
        return (company.company_id, company.domain, "crawled")
        
    except Exception as e:
        logger.exception("Unexpected error processing %s: %s", company.domain, e)
        return (company.company_id, company.domain, "failed_unknown")


def main() -> None:
    # Set multiprocessing start method for Windows compatibility
    if sys.platform == "win32":
        multiprocessing.set_start_method("spawn", force=True)
    
    parser = argparse.ArgumentParser(description="Offline company intelligence pipeline")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to domains CSV (e.g. domains.csv)",
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Path to settings YAML (default: config/settings.yaml)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    config_path = (base_dir / args.config).resolve()
    settings = load_settings(config_path)

    data_dir = (base_dir / settings["paths"]["data_dir"]).resolve()
    output_dir = (base_dir / settings["paths"]["output_dir"]).resolve()
    logs_dir = (base_dir / settings["paths"]["logs_dir"]).resolve()

    setup_logging(logs_dir)
    logger = logging.getLogger("main")

    logger.info("Starting pipeline")
    logger.info("Loading domains from CSV: %s", args.input)

    input_csv = (base_dir / args.input).resolve()
    companies = load_companies_from_csv(input_csv, data_dir)

    manifest_csv = data_dir / "companies.csv"
    manifest_json = data_dir / "companies.json"
    write_manifest(companies, manifest_csv, manifest_json)

    # Determine number of workers
    parallel_cfg = settings.get("parallel", {})
    num_workers = parallel_cfg.get("workers", 0)
    if num_workers == 0:
        num_workers = multiprocessing.cpu_count()
    parallel_llm = parallel_cfg.get("parallel_llm", False)
    
    logger.info("Using %d parallel workers for download/crawl", num_workers)
    
    # Create company lookup by ID
    company_dict = {c.company_id: c for c in companies}
    
    # Prepare work items for parallel processing (download + crawl)
    work_items = []
    for company in companies:
        domain_dir = data_dir / company.domain
        chunks_path = output_dir / company.domain / "chunks.json"
        is_downloaded = check_downloaded(domain_dir)
        is_scraped = check_scraped(chunks_path)
        
        # Only add to work queue if needs download or crawl
        if not (is_downloaded and is_scraped):
            work_items.append((company, settings, data_dir, output_dir))
        else:
            logger.info("Skipping %s: already downloaded and scraped", company.domain)
            company.status = "crawled"
    
    # Process download and crawl in parallel
    if work_items:
        logger.info("Processing %d companies in parallel (download + crawl) with %d workers", len(work_items), num_workers)
        try:
            with multiprocessing.Pool(processes=num_workers) as pool:
                results = pool.map(process_company_download_crawl, work_items)
            
            # Update company statuses from parallel results
            success_count = 0
            failed_count = 0
            for company_id, domain, status in results:
                if company_id in company_dict:
                    company_dict[company_id].status = status
                    if status == "crawled":
                        success_count += 1
                    else:
                        failed_count += 1
                    logger.info("Completed %s: status = %s", domain, status)
            
            logger.info("Download/crawl phase complete: %d succeeded, %d failed", success_count, failed_count)
            
            # Write updated manifest
            write_manifest(companies, manifest_csv, manifest_json)
        except Exception as e:
            logger.exception("Error in parallel download/crawl processing: %s", e)
            logger.error("Falling back to sequential processing")
            # Fallback to sequential processing
            for company, settings, data_dir, output_dir in work_items:
                try:
                    result = process_company_download_crawl((company, settings, data_dir, output_dir))
                    company_id, domain, status = result
                    if company_id in company_dict:
                        company_dict[company_id].status = status
                    write_manifest(companies, manifest_csv, manifest_json)
                except Exception as e2:
                    logger.exception("Error processing %s sequentially: %s", company.domain, e2)
                    if company.company_id in company_dict:
                        company_dict[company.company_id].status = "failed_unknown"
                    write_manifest(companies, manifest_csv, manifest_json)
    
    # Process LLM extraction (sequential or parallel based on config)
    logger.info("Starting LLM extraction phase")
    
    if parallel_llm:
        llm_work_items = [
            (c, output_dir, settings, base_dir)
            for c in companies
            if c.status == "crawled"
        ]
        
        if llm_work_items:
            # Limit parallel LLM to avoid overwhelming Ollama (max 4 workers)
            max_llm_workers = min(4, num_workers, len(llm_work_items))
            logger.info("Using %d parallel LLM workers for %d companies (limited to avoid overwhelming Ollama)", max_llm_workers, len(llm_work_items))
            try:
                with multiprocessing.Pool(processes=max_llm_workers) as pool:
                    llm_results = pool.map(process_company_llm, llm_work_items)
                
                success_count = 0
                failed_count = 0
                for company_id, domain, status in llm_results:
                    if company_id in company_dict:
                        company_dict[company_id].status = status
                        if status == "profile_generated":
                            success_count += 1
                        else:
                            failed_count += 1
                        logger.info("LLM completed %s: status = %s", domain, status)
                
                logger.info("LLM extraction phase complete: %d succeeded, %d failed", success_count, failed_count)
                write_manifest(companies, manifest_csv, manifest_json)
            except Exception as e:
                logger.exception("Error in parallel LLM processing: %s", e)
                logger.error("Falling back to sequential LLM processing")
                # Fallback to sequential processing
                for company, output_dir, settings, base_dir in llm_work_items:
                    try:
                        result = process_company_llm((company, output_dir, settings, base_dir))
                        company_id, domain, status = result
                        if company_id in company_dict:
                            company_dict[company_id].status = status
                        write_manifest(companies, manifest_csv, manifest_json)
                    except Exception as e2:
                        logger.exception("Error processing LLM for %s sequentially: %s", company.domain, e2)
                        if company.company_id in company_dict:
                            company_dict[company.company_id].status = "failed_llm"
                        write_manifest(companies, manifest_csv, manifest_json)
    else:
        # Sequential LLM processing
        for company in companies:
            if company.status != "crawled":
                continue
            
            logger.info("Processing LLM extraction for %s", company.domain)
            chunks_path = output_dir / company.domain / "chunks.json"
            
            # Explicit validation: verify chunks.json exists and has content before LLM
            if not chunks_path.exists():
                logger.error("Validation failed: chunks.json not found for %s before LLM step", company.domain)
                company.status = "failed_crawl"
                write_manifest(companies, manifest_csv, manifest_json)
                continue
            
            try:
                with chunks_path.open("r", encoding="utf-8") as f:
                    chunks_data = json.load(f)
                if not chunks_data or not isinstance(chunks_data, list) or len(chunks_data) == 0:
                    logger.error("Validation failed: chunks.json is empty for %s before LLM step", company.domain)
                    company.status = "failed_crawl"
                    write_manifest(companies, manifest_csv, manifest_json)
                    continue
                logger.info("Validation passed: %d chunks found for %s", len(chunks_data), company.domain)
            except Exception as e:
                logger.error("Validation failed: Could not read/parse chunks.json for %s: %s", company.domain, e)
                company.status = "failed_crawl"
                write_manifest(companies, manifest_csv, manifest_json)
                continue

            # STEP 4: LLM extraction via Ollama
            try:
                llm_status = extract_profile_for_company(company, output_dir, settings, base_dir)
                company.status = llm_status
                write_manifest(companies, manifest_csv, manifest_json)
            except Exception as e:
                logger.exception("LLM extraction failed for %s: %s", company.domain, e)
                company.status = "failed_llm"
                write_manifest(companies, manifest_csv, manifest_json)

    # Final summary
    status_counts = {}
    for company in companies:
        status = company.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    logger.info("=" * 80)
    logger.info("PIPELINE COMPLETED - FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info("Total companies: %d", len(companies))
    for status, count in sorted(status_counts.items()):
        logger.info("  %s: %d", status, count)
    logger.info("=" * 80)
    
    # Write final manifest
    write_manifest(companies, manifest_csv, manifest_json)
    logger.info("Final manifest written to %s and %s", manifest_csv, manifest_json)


if __name__ == "__main__":
    main()


