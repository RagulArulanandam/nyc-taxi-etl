"""
src/transform/clean.py

Cleaning and feature engineering for one month of Yellow Taxi trips.
clean_trips() is a pure DataFrame -> DataFrame function so it is easy to test;
transform_layer() adds the file read around it.
"""

import re
from pathlib import Path

import polars as pl

from src.extract.config import (
    MAX_FARE_AMOUNT,
    MAX_PASSENGERS,
    MAX_TOTAL_AMOUNT,
    MAX_TRIP_DISTANCE_MILES,
    MAX_TRIP_SECONDS,
    MIN_TRIP_SECONDS,
)
from src.extract.logger import setup_logger

log = setup_logger(__name__)

FILENAME_RE = re.compile(r"yellow_tripdata_(\d{4})-(\d{2})\.parquet$")

REQUIRED_COLUMNS = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "trip_distance",
    "fare_amount",
    "total_amount",
    "payment_type",
    "PULocationID",
    "DOLocationID",
]

# Kept when present. The TLC has renamed some of these between years.
OPTIONAL_COLUMNS = [
    "VendorID",
    "passenger_count",
    "RatecodeID",
    "tip_amount",
    "tolls_amount",
    "congestion_surcharge",
    "airport_fee",
]

OUTPUT_COLUMNS = [
    "pickup_at",
    "dropoff_at",
    "pickup_hour",
    "pickup_weekday",
    "trip_duration_sec",
    "trip_distance",
    "passenger_count",
    "fare_amount",
    "tip_amount",
    "tolls_amount",
    "congestion_surcharge",
    "airport_fee",
    "total_amount",
    "payment_type",
    "VendorID",
    "RatecodeID",
    "pu_location_id",
    "do_location_id",
]


def period_from_filename(path: Path) -> tuple[int, int]:
    """Return (year, month) from a name like yellow_tripdata_2024-01.parquet."""
    match = FILENAME_RE.search(path.name)
    if not match:
        raise ValueError(f"Unexpected file name: {path.name}")
    return int(match.group(1)), int(match.group(2))


def _normalise(df: pl.DataFrame) -> pl.DataFrame:
    """Unify column names/types and add derived columns."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if "Airport_fee" in df.columns and "airport_fee" not in df.columns:
        df = df.rename({"Airport_fee": "airport_fee"})

    # Optional columns that are absent are added as nulls so the output schema is stable.
    df = df.with_columns(
        [pl.lit(None, dtype=pl.Float64).alias(c) for c in OPTIONAL_COLUMNS if c not in df.columns]
    )

    return (
        df.with_columns(
            pl.col("tpep_pickup_datetime").cast(pl.Datetime("us")).alias("pickup_at"),
            pl.col("tpep_dropoff_datetime").cast(pl.Datetime("us")).alias("dropoff_at"),
            pl.col("passenger_count").cast(pl.Int32),
            pl.col("trip_distance").cast(pl.Float32),
            pl.col("fare_amount").cast(pl.Float32),
            pl.col("tip_amount").cast(pl.Float32),
            pl.col("tolls_amount").cast(pl.Float32),
            pl.col("congestion_surcharge").cast(pl.Float32),
            pl.col("airport_fee").cast(pl.Float32),
            pl.col("total_amount").cast(pl.Float32),
            pl.col("payment_type").cast(pl.Int32),
            pl.col("PULocationID").alias("pu_location_id"),
            pl.col("DOLocationID").alias("do_location_id"),
            pl.col("VendorID").cast(pl.Int32),
            pl.col("RatecodeID").cast(pl.Int32),
        )
        .with_columns(
            (pl.col("dropoff_at") - pl.col("pickup_at"))
            .dt.total_seconds()
            .alias("trip_duration_sec"),
            pl.col("pickup_at").dt.hour().cast(pl.Int8).alias("pickup_hour"),
            pl.col("pickup_at").dt.weekday().cast(pl.Int8).alias("pickup_weekday"),
        )
    )


def clean_trips(df: pl.DataFrame, year: int, month: int) -> tuple[pl.DataFrame, dict[str, int]]:
    """
    Clean one month of trips.

    Returns the cleaned frame and a stats dict: rows_in, rows_out and, for every
    rule, how many rows it removed (rules apply in order, so a row is counted
    against the first rule it fails).
    """
    stats: dict[str, int] = {"rows_in": df.height}
    df = _normalise(df)

    rules: list[tuple[str, pl.Expr]] = [
        (
            "null_timestamps",
            pl.col("pickup_at").is_not_null() & pl.col("dropoff_at").is_not_null(),
        ),
        (
            "pickup_outside_file_month",
            (pl.col("pickup_at").dt.year() == year) & (pl.col("pickup_at").dt.month() == month),
        ),
        (
            "bad_duration",
            pl.col("trip_duration_sec").is_between(MIN_TRIP_SECONDS, MAX_TRIP_SECONDS),
        ),
        (
            "bad_distance",
            (pl.col("trip_distance") > 0) & (pl.col("trip_distance") <= MAX_TRIP_DISTANCE_MILES),
        ),
        (
            "bad_fare",
            (pl.col("fare_amount") > 0) & (pl.col("fare_amount") <= MAX_FARE_AMOUNT),
        ),
        (
            "bad_total",
            (pl.col("total_amount") > 0) & (pl.col("total_amount") <= MAX_TOTAL_AMOUNT),
        ),
        (
            # Null counts are dropped (the warehouse expects a value), as are 0 and > 6.
            "bad_passenger_count",
            pl.col("passenger_count").is_between(1, MAX_PASSENGERS),
        ),
    ]

    for name, keep in rules:
        before = df.height
        df = df.filter(keep.fill_null(False))
        stats[f"dropped_{name}"] = before - df.height

    df = df.select(OUTPUT_COLUMNS)
    stats["rows_out"] = df.height
    return df, stats


def transform_layer(path: Path) -> tuple[pl.DataFrame, dict[str, int]]:
    """Read one raw parquet file and return (cleaned frame, stats)."""
    year, month = period_from_filename(path)
    raw = pl.read_parquet(path)
    log.info("Read %s (%d rows)", path.name, raw.height)

    df, stats = clean_trips(raw, year, month)

    dropped = {k: v for k, v in stats.items() if k.startswith("dropped_") and v}
    log.info(
        "Cleaned %s: %d -> %d rows, dropped %s",
        path.name, stats["rows_in"], stats["rows_out"], dropped,
    )
    return df, stats
