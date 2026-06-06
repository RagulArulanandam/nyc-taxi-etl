"""
src/extract/helpers.py
 
Pure utility functions. No I/O, no logging, no side effects.
Each function does exactly one thing and is independently testable.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from src.extract.config import *

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

def is_future(year: int, month: int) -> bool:
    now = datetime.now()
    return (year, month) >= (now.year, now.month -1)

def validate_parquet(path: Path, min_bytes: int = 1024) -> bool:
    """
    Check that a file exists, is large enough, and has valid Parquet magic bytes.
    Returns (is_valid, reason_if_invalid).
    """
    if not path.exists():
        return False, "File does not exist"

    size = path.stat().st_size
    if size < MIN_FILESIZE:
        return False, f"too small ({size} bytes)"

    with open(path, "rb") as f:
        header = f.read(4)
        f.seek(-4,2)
        footer = f.read(4)

    if header != b"PAR1" or footer != b"PAR1":
        return False, "not a valid Parquet File (bad Magic Bytes)"

    return True, ""


