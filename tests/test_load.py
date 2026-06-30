"""
tests/test_load.py

pytest tests/test_load.py -v
"""

from src.load.load_postgres import DB_COLUMNS
from src.transform.clean import transform_layer


def test_db_columns_has_no_duplicates():
    assert len(DB_COLUMNS) == len(set(DB_COLUMNS))


def test_db_columns_uses_snake_case_only():
    # Catches the exact bug you hit earlier — PULocationID vs pu_location_id
    for col in DB_COLUMNS:
        assert col == col.lower(), f"{col} is not snake_case"
        assert " " not in col


def test_db_columns_matches_transform_output(tmp_path):
    # Reuse the same fake-file builder pattern from test_transform.py
    import polars as pl
    from datetime import datetime

    df = pl.DataFrame({
        "tpep_pickup_datetime":  [datetime(2023, 1, 1, 8, 0, 0)],
        "tpep_dropoff_datetime": [datetime(2023, 1, 1, 8, 15, 0)],
        "passenger_count": [1],
        "trip_distance":   [2.5],
        "fare_amount":     [12.0],
        "total_amount":    [15.0],
        "payment_type":    [1],
        "PULocationID":    [100],
        "DOLocationID":    [101],
    })

    raw_path = tmp_path / "fake.parquet"
    df.write_parquet(raw_path)

    transformed = transform_layer(raw_path)

    # Every column the loader expects must actually exist in transform output
    missing = set(DB_COLUMNS) - set(transformed.columns)
    assert missing == set(), f"DB_COLUMNS expects columns not produced by transform_layer: {missing}"