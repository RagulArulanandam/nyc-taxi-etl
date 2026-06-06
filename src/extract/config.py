"""
src/extract/config.py
 
Single source of truth for all download settings.
Change years, paths, or URLs here — nowhere else.
"""

from pathlib import Path

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


YEARS = [2023, 2024]
MONTHS = list(range(1, 13))

RAW_DIR  = Path("data/raw/yellow_taxi")
LOG_DIR  = Path("logs")
LOG_FILE = LOG_DIR / "download.log"



CHUNK_SIZE = 8 * 1024 * 1024
TIMEOUT_SEC  = 120       # per-request timeout
MIN_FILESIZE = 1_024     # bytes — anything smaller is treated as corrupt