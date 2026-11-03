"""
src/extract/helpers.py

Small utility functions. Each does exactly one thing and is independently testable.
"""

import hashlib
from datetime import date
from pathlib import Path

from src.extract.config import (
    BASE_URL,
    MIN_FILESIZE,
    PUBLICATION_LAG_MONTHS,
    RAW_DIR,
)


def build_url(year: int, month: int) -> str:
    return f"{BASE_URL}/yellow_tripdata_{year}-{month:02d}.parquet"


def build_local_path(year: int, month: int) -> Path:
    return RAW_DIR / f"yellow_tripdata_{year}-{month:02d}.parquet"


def file_md5(path: Path, chunk: int = 1 << 20) -> str:
    """Return the MD5 hex digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def is_future(year: int, month: int, today: date | None = None) -> bool:
    """True if (year, month) is too recent to be published yet."""
    today = today or date.today()
    latest = today.year * 12 + (today.month - 1) - PUBLICATION_LAG_MONTHS
    return year * 12 + (month - 1) > latest


def validate_parquet(path: Path, min_bytes: int = MIN_FILESIZE) -> tuple[bool, str]:
    """
    Check that a file exists, is large enough, and has valid Parquet magic bytes.
    Returns (is_valid, reason_if_invalid).
    """
    if not path.exists():
        return False, "file does not exist"

    size = path.stat().st_size
    if size < min_bytes:
        return False, f"too small ({size} bytes)"

    with open(path, "rb") as f:
        header = f.read(4)
        f.seek(-4, 2)
        footer = f.read(4)

    if header != b"PAR1" or footer != b"PAR1":
        return False, "not a valid Parquet file (bad magic bytes)"

    return True, ""
