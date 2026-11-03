"""
src/pipeline.py

Runs the whole ETL in order. Later steps (load, analytics) are added here.

    python -m src.pipeline
"""

from src.extract.main import run as extract
from src.transform.main import transform_all


def run() -> dict:
    extract_summary = extract()
    transform_summary = transform_all()
    return {"extract": extract_summary, "transform": transform_summary}


if __name__ == "__main__":
    result = run()
    failed = result["extract"]["failed"] + result["transform"]["failed"]
    raise SystemExit(1 if failed else 0)
