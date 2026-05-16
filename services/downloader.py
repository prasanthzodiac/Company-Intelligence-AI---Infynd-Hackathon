import logging
import shutil
import subprocess
import time
from collections import deque
from pathlib import Path
from typing import Dict
from urllib.parse import urljoin, urlparse

import requests

from .csv_loader import Company
from .domain_utils import crawl_hosts


logger = logging.getLogger(__name__)


def _find_executable(name: str, configured_path: str | None) -> str | None:
    if configured_path:
        path = Path(configured_path)
        if path.exists():
            return str(path)
    return shutil.which(name)


def _run_with_retry(cmd: list[str], timeout: int, cwd: Path) -> bool:
    for attempt in range(2):  # initial + 1 retry
        try:
            logger.info("Running command (attempt %d): %s", attempt + 1, " ".join(cmd))
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
                text=True,
            )
            if result.returncode == 0:
                logger.info("Command succeeded")
                return True
            logger.warning(
                "Command failed with code %s. stdout: %s stderr: %s",
                result.returncode,
                result.stdout[-1000:],
                result.stderr[-1000:],
            )
        except subprocess.TimeoutExpired:
            logger.warning("Command timed out on attempt %d", attempt + 1)
        except Exception as e:
            logger.exception("Unexpected error running command: %s", e)
    return False


def _python_crawl(domain: str, base_url: str, target_dir: Path, depth: int, timeout: int) -> bool:
    """
    Improved Python-only crawler used when httrack/wget are unavailable.
    - Only follows same-domain HTTP/HTTPS links.
    - Respects a simple max-depth BFS.
    - Tries HTTPS first, then HTTP fallback.
    - Better error handling and link extraction.
    """
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    visited: set[str] = set()
    queue: deque[tuple[str, int]] = deque()
    
    # Try HTTPS first, then HTTP
    https_url = f"https://{domain}/"
    http_url = f"http://{domain}/"
    
    # Add both to queue with priority on HTTPS
    queue.append((https_url, 0))
    if https_url != http_url:
        queue.append((http_url, 0))

    parsed_domain = urlparse(base_url).netloc
    max_pages = 100  # Limit total pages to avoid infinite loops
    pages_fetched = 0

    def _save_html(url: str, content: str) -> None:
        parsed = urlparse(url)
        path = parsed.path or "/"
        if path.endswith("/"):
            path = path + "index.html"
        if not path.endswith(".html") and not path.endswith(".htm"):
            # Force .html extension for non-HTML-looking paths
            path = path.rstrip("/") + ".html"
        # Clean path to avoid invalid characters
        path = path.replace("?", "_").replace("&", "_").replace("=", "_")
        dest = target_dir / path.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            dest.write_text(content, encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning("Failed to save %s: %s", dest, e)

    try:
        from bs4 import BeautifulSoup  # type: ignore
    except Exception:
        logger.error("BeautifulSoup (bs4) is required for Python fallback crawler")
        return False

    while queue and pages_fetched < max_pages:
        url, d = queue.popleft()
        if url in visited or d > depth:
            continue
        visited.add(url)
        pages_fetched += 1

        try:
            logger.info("Python crawler fetching %s (depth %d, page %d)", url, d, pages_fetched)
            # Small delay to be polite to servers
            if pages_fetched > 1:
                time.sleep(0.5)
            resp = session.get(url, timeout=min(timeout, 30), allow_redirects=True)
            if resp.status_code >= 400:
                logger.warning("Skipping %s due to status %s", url, resp.status_code)
                continue
        except requests.exceptions.SSLError:
            # Try HTTP if HTTPS fails
            if url.startswith("https://"):
                http_url = url.replace("https://", "http://")
                if http_url not in visited:
                    queue.append((http_url, d))
            logger.warning("SSL error for %s, will try HTTP", url)
            continue
        except Exception as e:
            logger.warning("Request error for %s: %s", url, e)
            continue

        content_type = resp.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            continue

        html = resp.text
        if len(html.strip()) < 100:  # Skip very small pages
            continue
            
        _save_html(url, html)

        # Extract internal links
        try:
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:") or href.startswith("javascript:"):
                    continue
                try:
                    next_url = urljoin(url, href)
                    parsed_next = urlparse(next_url)
                    # Normalize domain comparison (handle www. prefix)
                    next_domain = parsed_next.netloc.lower().replace("www.", "")
                    current_domain = parsed_domain.lower().replace("www.", "")
                    if next_domain != current_domain:
                        continue
                    if parsed_next.scheme not in ("http", "https"):
                        continue
                    # Remove fragments
                    next_url = next_url.split("#")[0]
                    if next_url not in visited and d < depth:
                        queue.append((next_url, d + 1))
                except Exception as e:
                    logger.debug("Error processing link %s: %s", href, e)
                    continue
        except Exception as e:
            logger.warning("Error parsing HTML for %s: %s", url, e)
            continue

    html_files = list(target_dir.rglob("*.html")) + list(target_dir.rglob("*.htm"))
    logger.info("Python crawler completed: %d HTML files saved for %s", len(html_files), domain)
    return len(html_files) > 0


def download_for_company(company: Company, settings: Dict, data_dir: Path) -> str:
    """
    Download the website snapshot for a single company using:
    - httrack (preferred) or wget, when available, otherwise
    - a Python-only fallback crawler.

    Returns a status string: 'downloaded' or 'failed_download'.
    """
    downloader_cfg = settings.get("downloader", {})
    depth = int(downloader_cfg.get("depth", 3))
    timeout = int(downloader_cfg.get("timeout_seconds", 600))

    httrack_path = _find_executable("httrack", downloader_cfg.get("httrack_path"))
    wget_path = _find_executable("wget", downloader_cfg.get("wget_path"))

    target_dir = data_dir / company.domain
    target_dir.mkdir(parents=True, exist_ok=True)

    used_tool = None
    success = False

    for host in crawl_hosts(company.domain):
        url = f"https://{host}/"
        if httrack_path:
            cmd = [
                httrack_path,
                url,
                "-O",
                str(target_dir),
                f"+*{host}/*",
                f"-r{depth}",
                "-n",
            ]
            used_tool = "httrack"
            logger.info("Using %s to download %s into %s", used_tool, host, target_dir)
            success = _run_with_retry(cmd, timeout=timeout, cwd=target_dir)
        elif wget_path:
            cmd = [
                wget_path,
                "--mirror",
                "--convert-links",
                "--page-requisites",
                "--no-parent",
                f"--directory-prefix={target_dir}",
                "--no-robots",
                f"--level={depth}",
                url,
            ]
            used_tool = "wget"
            logger.info("Using %s to download %s into %s", used_tool, host, target_dir)
            success = _run_with_retry(cmd, timeout=timeout, cwd=target_dir)
        else:
            used_tool = "python_crawler"
            logger.info("Python crawler for %s (host %s)", company.domain, host)
            success = _python_crawl(host, url, target_dir, depth=depth, timeout=timeout)

        if success:
            html_files = list(target_dir.rglob("*.html")) + list(target_dir.rglob("*.htm"))
            if html_files:
                break
            success = False

    if not success:
        logger.error("Download failed for %s using %s", company.domain, used_tool)
        return "failed_download"

    # Explicit validation: at least one HTML file with actual content
    html_files = list(target_dir.rglob("*.html")) + list(target_dir.rglob("*.htm"))
    if not html_files:
        logger.error("No HTML files found after download for %s", company.domain)
        return "failed_download"
    
    # Verify at least one HTML file has meaningful content (not empty, not just whitespace)
    has_valid_content = False
    for html_file in html_files[:5]:  # Check first 5 files
        try:
            content = html_file.read_text(encoding="utf-8", errors="ignore").strip()
            if len(content) > 100:  # At least 100 chars of actual content
                has_valid_content = True
                break
        except Exception as e:
            logger.debug("Could not read %s: %s", html_file, e)
            continue
    
    if not has_valid_content:
        logger.error("No HTML files with valid content found for %s", company.domain)
        return "failed_download"

    logger.info("Download validated: %d HTML files found for %s", len(html_files), company.domain)
    return "downloaded"


