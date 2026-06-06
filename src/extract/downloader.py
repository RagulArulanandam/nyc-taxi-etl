"""
src/extract/downloader.py
 
One job: stream-download a URL to a local path.
All decisions (which files, skip logic, validation) live in main.py.
"""


import requests
from pathlib import Path

from src.extract.config import *
from src.extract.logger import setup_logger

log = setup_logger(__name__)

def download_file(url: str, dest: Path) -> bool:
    """Stream-download url → dest. Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info("Downloading %s", url)

    try:
        with requests.get(url, stream=True, timeout=TIMEOUT_SEC) as r:
            if r.status_code == 404:
                log.warning("Not found (404): %s", url)
                return False
            r.raise_for_status()

            total = int(r.headers.get("content-length", 0))
            downloaded = 0

            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)
            
        if total and downloaded != total:
            log.error("Incomplete download: got %d of %d bytes", downloaded, total)
            dest.unlink(missing_ok=True)
            return False
        
        # Correct — values passed as separate arguments after the format string
        log.info("Saved %s (%.1f MB)", dest.name, downloaded / 1e6)
        return True
    
    except requests.RequestException as exc:
        log.error("Request failed (%s): %s", type(exc).__name__, exc)
        dest.unlink(missing_ok=True)
        return False
    
    except OSError as exc:
        log.error("File write error: %s", exc)
        return False

