"""
src/extract/config.py

Single source of truth for all download and transform settings.
Change years, paths, URLs or cleaning limits here — nowhere else.
"""

from pathlib import Path

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"

YEARS = [2023, 2024]
MONTHS = list(range(1, 13))

RAW_DIR = Path("data/raw/yellow_taxi")
PROCESSED_DIR = Path("data/processed/yellow_taxi")
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "download.log"

CHUNK_SIZE = 8 * 1024 * 1024
TIMEOUT_SEC = 120  # per-request timeout
MIN_FILESIZE = 1_024  # bytes — anything smaller is treated as corrupt

# TLC publishes a month of data roughly two months after it ends.
# Months newer than (today - this many months) are not requested.
PUBLICATION_LAG_MONTHS = 2

# Cleaning limits used by src/transform/clean.py
MIN_TRIP_SECONDS = 60
MAX_TRIP_SECONDS = 6 * 60 * 60
MAX_TRIP_DISTANCE_MILES = 100
MAX_FARE_AMOUNT = 1_000
MAX_TOTAL_AMOUNT = 1_500
MAX_PASSENGERS = 6
