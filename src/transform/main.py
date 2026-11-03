"""
src/transform/main.py

Entry point for the transform step: data/raw -> data/processed.

Run directly:
    python -m src.transform.main            # only files not yet processed
    python -m src.transform.main --force    # reprocess everything (after rule changes)
"""

import argparse

from src.extract.config import PROCESSED_DIR, RAW_DIR, YEARS
from src.extract.logger import setup_logger
from src.transform.clean import period_from_filename, transform_layer

log = setup_logger(__name__)


def transform_all(years: list[int] | None = None, force: bool = False) -> dict:
    """
    Run transform_layer() on every raw parquet file for the given years.

    Skips files whose output already exists unless force=True. Output is written
    to a temp file and renamed, so a crash never leaves a half-written file that
    would be skipped as "done" on the next run.
    """
    years = YEARS if years is None else years
    raw_files = []
    for path in sorted(RAW_DIR.glob("yellow_tripdata_*.parquet")):
        try:
            year, _ = period_from_filename(path)
        except ValueError:
            log.warning("Ignoring unexpected file: %s", path.name)
            continue
        if not years or year in years:
            raw_files.append(path)

    log.info("Found %d raw files to consider", len(raw_files))
    summary = {"success": 0, "skipped": 0, "failed": 0}
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for raw_path in raw_files:
        output = PROCESSED_DIR / raw_path.name
        tmp = output.with_name(output.name + ".tmp")

        if output.exists() and not force:
            log.info("Already processed, skipping: %s", raw_path.name)
            summary["skipped"] += 1
            continue

        try:
            df, _ = transform_layer(raw_path)
            df.write_parquet(tmp, compression="snappy")
            tmp.replace(output)
            log.info("Written: %s (%d rows)", output.name, df.height)
            summary["success"] += 1
        except Exception as exc:  # one bad month must not stop the others
            log.error("Failed on %s: %s", raw_path.name, exc)
            tmp.unlink(missing_ok=True)
            summary["failed"] += 1

    log.info(
        "Transform done. success=%d skipped=%d failed=%d",
        summary["success"], summary["skipped"], summary["failed"],
    )
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean raw Yellow Taxi parquet files.")
    parser.add_argument("--force", action="store_true", help="reprocess files that already exist")
    parser.add_argument("--years", type=int, nargs="+", help="limit to these years")
    args = parser.parse_args()
    result = transform_all(years=args.years, force=args.force)
    raise SystemExit(1 if result["failed"] else 0)
