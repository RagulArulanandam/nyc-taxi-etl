"""
tests/test_transform.py
"""

import polars as pl
from datetime import datetime
from src.transform.clean import transform_layer


def make_fake_raw_file(tmp_path) -> "Path":
    """
    Build a small, realistic-looking raw parquet file with the same
    columns the real TLC data has, including some deliberately bad rows.
    """
    df = pl.DataFrame({
        "tpep_pickup_datetime":  [
            datetime(2023, 1, 1, 8, 0, 0),   # good row
            datetime(2023, 1, 1, 9, 0, 0),   # good row
            datetime(2023, 1, 1, 10, 0, 0),  # bad: zero distance
            datetime(2023, 1, 1, 11, 0, 0),  # bad: trip too short
            None,                              # bad: null pickup time
        ],
        "tpep_dropoff_datetime": [
            datetime(2023, 1, 1, 8, 15, 0),
            datetime(2023, 1, 1, 9, 20, 0),
            datetime(2023, 1, 1, 10, 10, 0),
            datetime(2023, 1, 1, 11, 0, 30),   # only 30 sec trip
            datetime(2023, 1, 1, 12, 0, 0),
        ],
        "passenger_count": [1, 2, 1, 1, 1],
        "trip_distance":   [2.5, 5.0, 0.0, 1.0, 3.0],   # row 3 = zero distance
        "fare_amount":     [12.0, 20.0, 8.0, 5.0, 15.0],
        "total_amount":    [15.0, 24.0, 10.0, 6.0, 18.0],
        "payment_type":    [1, 1, 2, 1, 1],
        "PULocationID":    [100, 150, 200, 75, 50],
        "DOLocationID":    [101, 151, 201, 76, 51],
    })

    path = tmp_path / "fake_yellow_tripdata_2023-01.parquet"
    df.write_parquet(path)
    return path


def test_transform_layer_drops_zero_distance_rows(tmp_path):
    raw_path = make_fake_raw_file(tmp_path)
    result = transform_layer(raw_path)

    # Row 3 had trip_distance = 0.0 — should be filtered out
    assert (result["trip_distance"] == 0.0).sum() == 0


def test_transform_layer_drops_short_trips(tmp_path):
    raw_path = make_fake_raw_file(tmp_path)
    result = transform_layer(raw_path)

    # Row 4 was a 30-second trip — trip_duration_sec must all be > 60
    assert (result["trip_duration_sec"] > 60).all()


def test_transform_layer_drops_null_pickup_rows(tmp_path):
    raw_path = make_fake_raw_file(tmp_path)
    result = transform_layer(raw_path)

    # Row 5 had a null pickup time — must not survive
    assert result["pickup_at"].null_count() == 0


def test_transform_layer_renames_columns_correctly(tmp_path):
    raw_path = make_fake_raw_file(tmp_path)
    result = transform_layer(raw_path)

    expected_columns = {
        "pickup_at", "dropoff_at", "pickup_hour", "pickup_weekday",
        "trip_duration_sec", "trip_distance", "passenger_count",
        "fare_amount", "total_amount", "payment_type",
        "pu_location_id", "do_location_id",
    }
    assert set(result.columns) == expected_columns


def test_transform_layer_keeps_only_valid_rows(tmp_path):
    raw_path = make_fake_raw_file(tmp_path)
    result = transform_layer(raw_path)

    # Of 5 input rows, only rows 1 and 2 should survive all filters
    assert result.shape[0] == 2