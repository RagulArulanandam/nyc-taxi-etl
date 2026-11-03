from datetime import datetime

import polars as pl
import pytest


@pytest.fixture
def make_trips():
    """Build a raw-format trips frame; each dict overrides the defaults of a valid row."""

    def _make(rows: list[dict]) -> pl.DataFrame:
        base = {
            "VendorID": 1,
            "tpep_pickup_datetime": datetime(2024, 1, 15, 8, 0, 0),
            "tpep_dropoff_datetime": datetime(2024, 1, 15, 8, 20, 0),
            "passenger_count": 1,
            "trip_distance": 3.5,
            "RatecodeID": 1,
            "payment_type": 1,
            "PULocationID": 100,
            "DOLocationID": 200,
            "fare_amount": 15.0,
            "tip_amount": 3.0,
            "tolls_amount": 0.0,
            "congestion_surcharge": 2.5,
            "Airport_fee": 0.0,
            "total_amount": 21.0,
        }
        full = [{**base, **r} for r in rows]
        return pl.DataFrame(
            full,
            schema_overrides={
                "tpep_pickup_datetime": pl.Datetime("ns"),
                "tpep_dropoff_datetime": pl.Datetime("ns"),
                "passenger_count": pl.Int64,
            },
        )

    return _make
