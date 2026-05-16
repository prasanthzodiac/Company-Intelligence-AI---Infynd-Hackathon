"""
Processing service for handling CSV uploads and running the pipeline
"""
import json
import logging
import os
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, List, Tuple
import sys

# Add parent directories to path
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from services.csv_loader import Company, load_companies_from_csv
from services.company_manifest import save_companies_manifest
from services.downloader import download_for_company
from services.crawler import crawl_company
from services.llm_extractor import extract_profile_for_company

logger = logging.getLogger(__name__)

# In-memory job status storage (in production, use Redis or database)
job_statuses: Dict[str, Dict] = {}


def check_downloaded(domain_dir: Path) -> bool:
    """Check if website is already downloaded"""
    if not domain_dir.exists():
        return False
    html_files = list(domain_dir.rglob("*.html")) + list(domain_dir.rglob("*.htm"))
    if not html_files:
        return False
    for html_file in html_files[:3]:
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore").strip()
            if len(content) > 100:
                return True
        except Exception:
            continue
    return False


def check_scraped(chunks_path: Path) -> bool:
    """Check if website is already scraped"""
    if not chunks_path.exists():
        return False
    try:
        with chunks_path.open("r", encoding="utf-8") as f:
            chunks_data = json.load(f)
        if chunks_data and isinstance(chunks_data, list) and len(chunks_data) > 0:
            valid_chunks = [c for c in chunks_data if c.get("text", "").strip() and len(c.get("text", "").strip()) > 20]
            return len(valid_chunks) > 0
    except Exception:
        pass
    return False


def check_llm_extracted(profile_path: Path) -> bool:
    """Check if LLM extraction is already done"""
    if not profile_path.exists():
        return False
    try:
        with profile_path.open("r", encoding="utf-8") as f:
            profile_data = json.load(f)
        # Check if profile has meaningful data
        if profile_data and isinstance(profile_data, dict):
            # Must have at least company name or domain
            if profile_data.get("company_name") or profile_data.get("domain"):
                # Check if it has some content (not just empty fields)
                has_content = (
                    profile_data.get("description_short") or 
                    profile_data.get("description_long") or
                    profile_data.get("industry") or
                    profile_data.get("contact", {}).get("email") or
                    profile_data.get("contact", {}).get("phone")
                )
                return bool(has_content)
    except Exception:
        pass
    return False


def process_company_download_crawl(args: Tuple) -> Tuple[int, str, str]:
    """Worker function for parallel download and crawl"""
    company, settings, data_dir, output_dir = args
    
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(f"worker-{company.company_id}")
    
    try:
        domain_dir = data_dir / company.domain
        chunks_path = output_dir / company.domain / "chunks.json"
        
        is_downloaded = check_downloaded(domain_dir)
        is_scraped = check_scraped(chunks_path)
        
        if is_downloaded and is_scraped:
            return (company.company_id, company.domain, "crawled")
        
        from services.pipeline_profiles import write_profile_from_chunks, write_status_profile

        if not is_downloaded:
            download_status = download_for_company(company, settings, data_dir)
            if download_status != "downloaded":
                write_status_profile(
                    output_dir,
                    company.domain,
                    download_status,
                    "Could not download the website. Check the domain is public and reachable.",
                )
                return (company.company_id, company.domain, download_status)

        if not is_scraped:
            crawl_status = crawl_company(company, data_dir, output_dir, settings)
            if crawl_status != "crawled":
                write_status_profile(
                    output_dir,
                    company.domain,
                    crawl_status,
                    "Download succeeded but scraping produced no content.",
                )
                return (company.company_id, company.domain, crawl_status)
            write_profile_from_chunks(output_dir, company.domain)

        return (company.company_id, company.domain, "crawled")
    except Exception as e:
        logger.exception("Error processing %s: %s", company.domain, e)
        return (company.company_id, company.domain, "failed")


def process_company_llm(args: Tuple) -> Tuple[int, str, str]:
    """Worker function for parallel LLM extraction"""
    company, output_dir, settings, base_dir = args
    
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(f"llm-worker-{company.company_id}")
    
    try:
        chunks_path = output_dir / company.domain / "chunks.json"
        profile_path = output_dir / company.domain / "profile.json"
        
        # Check if already extracted
        if check_llm_extracted(profile_path):
            logger.info("Skipping LLM extraction for %s: already extracted", company.domain)
            return (company.company_id, company.domain, "profile_generated")
        
        from services.pipeline_profiles import write_status_profile

        if not chunks_path.exists():
            write_status_profile(
                output_dir,
                company.domain,
                "failed_llm",
                "No scraped content available for extraction.",
            )
            return (company.company_id, company.domain, "failed_llm")
        
        status = extract_profile_for_company(company, output_dir, settings, base_dir)
        return (company.company_id, company.domain, status)
    except Exception as e:
        logger.exception("LLM error for %s: %s", company.domain, e)
        return (company.company_id, company.domain, "failed_llm")


def _use_thread_pool() -> bool:
    """Thread pool is safer on Render/Railway than multiprocessing."""
    return os.environ.get("PIPELINE_USE_THREADS", "true").lower() in (
        "1",
        "true",
        "yes",
    )


def _run_parallel(
    worker_fn: Callable,
    args_list: List[Tuple],
    max_workers: int,
    on_progress: Callable[[int, int, Tuple], None] | None = None,
) -> List[Tuple]:
    if not args_list:
        return []
    total = len(args_list)
    results: List[Tuple] = []
    workers = max(1, min(max_workers, total))

    if _use_thread_pool():
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_fn, args) for args in args_list]
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                results.append(result)
                if on_progress:
                    on_progress(i, total, result)
        return results

    import multiprocessing

    if sys.platform == "win32":
        multiprocessing.set_start_method("spawn", force=True)
    with multiprocessing.Pool(processes=workers) as pool:
        for i, result in enumerate(pool.imap_unordered(worker_fn, args_list), 1):
            results.append(result)
            if on_progress:
                on_progress(i, total, result)
    return results


def run_pipeline(
    csv_path: Path, job_id: str, session_id: str, repo_base: Path
) -> None:
    """Run the full pipeline in a background thread (session-scoped storage only)."""
    try:
        from services.session_store import get_session_paths, touch_session

        config_path = repo_base / "config" / "settings.yaml"
        if not config_path.exists():
            job_statuses[job_id] = {
                "stage": "error",
                "message": "Config file not found",
                "progress": 0,
            }
            return

        from services.settings_loader import load_settings, get_llm_config
        from services.llm_client import recommended_llm_workers

        settings = load_settings(repo_base)
        paths = get_session_paths(repo_base, session_id)
        touch_session(repo_base, session_id)
        data_dir = paths.data_dir.resolve()
        output_dir = paths.output_dir.resolve()
        
        # Load companies from CSV
        job_statuses[job_id] = {
            "stage": "downloading",
            "message": "Loading companies from CSV...",
            "progress": 5
        }
        
        companies = load_companies_from_csv(csv_path, data_dir)
        total = len(companies)

        # Write manifest immediately so the UI can list companies while processing
        save_companies_manifest(paths, companies)

        if total == 0:
            job_statuses[job_id] = {
                "stage": "error",
                "message": "No valid companies found in CSV file",
                "progress": 0
            }
            return
        
        # Check how many companies are already fully processed
        fully_processed = 0
        for company in companies:
            domain_dir = data_dir / company.domain
            chunks_path = output_dir / company.domain / "chunks.json"
            profile_path = output_dir / company.domain / "profile.json"
            
            is_downloaded = check_downloaded(domain_dir)
            is_scraped = check_scraped(chunks_path)
            is_extracted = check_llm_extracted(profile_path)
            
            if is_downloaded and is_scraped and is_extracted:
                fully_processed += 1
        
        # If all companies are already processed, skip to completion
        if fully_processed == total:
            job_statuses[job_id] = {
                "stage": "complete",
                "message": f"All {total} companies already processed! Skipping to main page...",
                "progress": 100,
                "total_companies": total,
                "processed_companies": total,
                "all_complete": True
            }
            # Still update manifest
            save_companies_manifest(paths, companies)
            return

        job_statuses[job_id] = {
            "stage": "downloading",
            "message": f"Processing {total} companies ({fully_processed} already complete)...",
            "progress": 10,
            "total_companies": total,
            "processed_companies": fully_processed
        }
        
        # Step 1: Download and Crawl (parallel)
        download_crawl_args = [(c, settings, data_dir, output_dir) for c in companies]
        # Increase workers for faster processing - use more cores
        parallel_config = settings.get("parallel", {})
        workers_setting = parallel_config.get("workers", 0)
        if workers_setting == 0:
            # Auto-detect: use CPU count but cap at 8
            default_workers = min(8, os.cpu_count() or 4)
        else:
            default_workers = workers_setting
        num_workers = max(1, min(default_workers, len(companies)))
        
        job_statuses[job_id] = {
            "stage": "downloading",
            "message": "Checking and downloading websites...",
            "progress": 15,
            "total_companies": total,
            "processed_companies": 0
        }
        
        def _download_progress(i, _total, result):
            job_statuses[job_id] = {
                "stage": "downloading",
                "message": f"Downloading and scraping websites... ({i}/{total})",
                "progress": 15 + int((i / total) * 35),
                "total_companies": total,
                "processed_companies": i,
                "current_company": result[1] if len(result) > 1 else "",
            }

        results = _run_parallel(
            process_company_download_crawl,
            download_crawl_args,
            num_workers,
            on_progress=_download_progress,
        )
        save_companies_manifest(paths, companies)

        downloaded_count = sum(1 for _, _, status in results if status == "downloaded" or status == "crawled")
        job_statuses[job_id] = {
            "stage": "scraping",
            "message": f"Completed scraping {downloaded_count} websites",
            "progress": 50,
            "total_companies": total,
            "processed_companies": downloaded_count
        }
        
        # Step 2: LLM extraction (parallel, rate-limited for remote/cloud LLMs)
        llm_args = [(c, output_dir, settings, repo_base) for c in companies]
        llm_config = get_llm_config(settings)
        llm_workers = recommended_llm_workers(llm_config, len(companies), num_workers)
        logger.info(
            "LLM provider=%s model=%s workers=%d",
            llm_config.provider,
            llm_config.model,
            llm_workers,
        )
        
        job_statuses[job_id] = {
            "stage": "llm",
            "message": "Extracting profiles with LLM...",
            "progress": 60,
            "total_companies": total,
            "processed_companies": downloaded_count
        }
        
        def _llm_progress(i, _total, result):
            job_statuses[job_id] = {
                "stage": "llm",
                "message": f"Extracting profiles with LLM... ({i}/{total})",
                "progress": 60 + int((i / total) * 35),
                "total_companies": total,
                "processed_companies": downloaded_count + i,
                "current_company": result[1] if len(result) > 1 else "",
            }

        llm_results = _run_parallel(
            process_company_llm,
            llm_args,
            llm_workers,
            on_progress=_llm_progress,
        )

        status_by_domain = {domain: status for _, domain, status in llm_results}
        for company in companies:
            if company.domain in status_by_domain:
                company.status = status_by_domain[company.domain]

        save_companies_manifest(paths, companies)

        success_count = sum(1 for _, _, status in llm_results if status == "profile_generated")
        
        job_statuses[job_id] = {
            "stage": "complete",
            "message": f"Completed! Processed {success_count} of {total} companies",
            "progress": 100,
            "total_companies": total,
            "processed_companies": success_count
        }
        
    except Exception as e:
        logger.exception("Pipeline error: %s", e)
        job_statuses[job_id] = {
            "stage": "error",
            "message": f"Error: {str(e)}",
            "progress": 0
        }


def start_processing(csv_path: Path, session_id: str, repo_base: Path) -> str:
    """Start processing pipeline and return job ID"""
    job_id = str(uuid.uuid4())

    job_statuses[job_id] = {
        "stage": "uploading",
        "message": "Starting pipeline...",
        "progress": 0,
        "session_id": session_id,
    }

    thread = threading.Thread(
        target=run_pipeline,
        args=(csv_path, job_id, session_id, repo_base),
    )
    thread.daemon = True
    thread.start()

    return job_id


def get_job_status(job_id: str, session_id: str | None = None) -> Dict:
    """Get current status of a job (optionally verify session ownership)."""
    status = job_statuses.get(job_id)
    if not status:
        return {"stage": "error", "message": "Job not found", "progress": 0}
    if session_id and status.get("session_id") and status["session_id"] != session_id:
        return {"stage": "error", "message": "Job not found", "progress": 0}
    return status

