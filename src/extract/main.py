"""
src/extract/main.py

Entry point for the extraction step.
Orchestrates the loop — all logic lives in the imported modules.

Run directly:
    python -m src.extract.main

Or import and call run() from an Airflow DAG or src/pipeline.py.
"""

from src.extract.config import MONTHS, YEARS
from src.extract.downloader import download_file
from src.extract.helpers import (
    build_local_path,
    build_url,
    file_md5,
    is_future,
    validate_parquet,
)
from src.extract.logger import setup_logger

log = setup_logger(__name__)


def run(years: list[int] = YEARS, months: list[int] = MONTHS) -> dict:
    """
    Download Yellow Taxi Parquet files for all (year, month) combinations.

    Skips files that are already downloaded and valid.
    Re-downloads files that exist but fail validation.

    Returns a summary dict: attempted, downloaded, skipped, failed.
    """
    summary = {"attempted": 0, "downloaded": 0, "skipped": 0, "failed": 0}

    for year in years:
        for month in months:

            if is_future(year, month):
                log.debug("Skipping future period %d-%02d", year, month)
                continue

            summary["attempted"] += 1
            url  = build_url(year, month)
            dest = build_local_path(year, month)

            # Skip if already downloaded and valid
            if dest.exists():
                valid, reason = validate_parquet(dest)
                if valid:
                    log.info("Already valid, skipping: %s", dest.name)
                    summary["skipped"] += 1
                    continue
                log.warning("Existing file invalid (%s), re-downloading: %s", reason, dest.name)
                dest.unlink()

            # Download
            log.info("Processing %d-%02d", year, month)
            ok = download_file(url, dest)
            if not ok:
                summary["failed"] += 1
                continue

            # Validate after download
            valid, reason = validate_parquet(dest)
            if valid:
                log.info("Validated %s  md5=%s", dest.name, file_md5(dest))
                summary["downloaded"] += 1
            else:
                log.error("Post-download validation failed (%s): %s", reason, dest.name)
                dest.unlink(missing_ok=True)
                summary["failed"] += 1

    log.info(
        "Done. attempted=%d downloaded=%d skipped=%d failed=%d",
        summary["attempted"], summary["downloaded"],
        summary["skipped"], summary["failed"],
    )
    return summary



if __name__ == "__main__":
    run()
