"""
src/main.py   (NEW — project-root pipeline orchestrator)

Runs the full pipeline end to end: extract -> transform -> load.
Each stage owns its own loop and its own idempotency check, exactly
as already built. This file just calls them in sequence.

Run directly:
    python -m src.main
"""

from src.extract.logger import setup_logger
from src.extract.extract import run_extract
from src.transform.transform import run_transform
from src.load.load import run_load

log = setup_logger(__name__)


def run_pipeline():
    log.info("=== STAGE 1: EXTRACT ===")
    run_extract()

    log.info("=== STAGE 2: TRANSFORM ===")
    run_transform()

    log.info("=== STAGE 3: LOAD ===")
    run_load()

    log.info("=== PIPELINE COMPLETE ===")


if __name__ == "__main__":
    run_pipeline()