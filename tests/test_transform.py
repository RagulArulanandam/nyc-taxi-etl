from datetime import datetime

import polars as pl
import pytest

from src.transform import transform as transform_main
from src.transform.clean import OUTPUT_COLUMNS, clean_trips, period_from_filename, transform_layer


def clean(make_trips, rows):
    return clean_trips(make_trips(rows), 2024, 1)


def test_valid_row_kept_with_derived_columns(make_trips):
    df, stats = clean(make_trips, [{}])
    assert df.columns == OUTPUT_COLUMNS
    row = df.row(0, named=True)
    assert row["trip_duration_sec"] == 20 * 60
    assert row["pickup_hour"] == 8
    assert row["pickup_weekday"] == 1  # Monday
    assert row["tip_amount"] == 3.0
    assert stats["rows_in"] == 1 and stats["rows_out"] == 1


@pytest.mark.parametrize(
    ("override", "rule"),
    [
        ({"trip_distance": 0.0}, "bad_distance"),
        ({"trip_distance": 5000.0}, "bad_distance"),
        ({"fare_amount": -5.0}, "bad_fare"),
        ({"fare_amount": 99999.0}, "bad_fare"),
        ({"total_amount": -1.0}, "bad_total"),
        ({"passenger_count": 0}, "bad_passenger_count"),
        ({"passenger_count": 9}, "bad_passenger_count"),
        ({"tpep_pickup_datetime": datetime(2002, 12, 31, 8, 0)}, "pickup_outside_file_month"),
        ({"tpep_pickup_datetime": datetime(2024, 2, 1, 8, 0)}, "pickup_outside_file_month"),
        ({"tpep_dropoff_datetime": datetime(2024, 1, 15, 8, 0, 30)}, "bad_duration"),
        ({"tpep_dropoff_datetime": datetime(2024, 1, 16, 8, 0)}, "bad_duration"),
        ({"tpep_dropoff_datetime": datetime(2024, 1, 15, 7, 0)}, "bad_duration"),
        ({"tpep_dropoff_datetime": None}, "null_timestamps"),
    ],
)
def test_bad_rows_are_dropped_and_counted(make_trips, override, rule):
    df, stats = clean(make_trips, [override, {}])
    assert df.height == 1
    assert stats[f"dropped_{rule}"] == 1
    assert stats["rows_in"] == 2 and stats["rows_out"] == 1


def test_missing_passenger_count_is_dropped(make_trips):
    df, stats = clean(make_trips, [{"passenger_count": None}, {}])
    assert df.height == 1
    assert stats["dropped_bad_passenger_count"] == 1


def test_airport_fee_is_renamed_and_missing_optionals_are_null(make_trips):
    raw = make_trips([{}]).drop("tip_amount", "RatecodeID")
    df, _ = clean_trips(raw, 2024, 1)
    assert "airport_fee" in df.columns and "Airport_fee" not in df.columns
    assert df["tip_amount"][0] is None


def test_missing_required_column_raises(make_trips):
    with pytest.raises(ValueError, match="Missing required columns"):
        clean_trips(make_trips([{}]).drop("fare_amount"), 2024, 1)


def test_period_from_filename(tmp_path):
    assert period_from_filename(tmp_path / "yellow_tripdata_2023-07.parquet") == (2023, 7)
    with pytest.raises(ValueError):
        period_from_filename(tmp_path / "other.parquet")


def _setup_dirs(monkeypatch, tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "out"
    raw.mkdir()
    monkeypatch.setattr(transform_main, "RAW_DIR", raw)
    monkeypatch.setattr(transform_main, "PROCESSED_DIR", out)
    return raw, out


def test_transform_all_writes_skips_and_forces(make_trips, tmp_path, monkeypatch):
    raw, out = _setup_dirs(monkeypatch, tmp_path)
    make_trips([{}, {"fare_amount": -1.0}]).write_parquet(raw / "yellow_tripdata_2024-01.parquet")

    assert transform_main.run_transform([2024]) == {"success": 1, "skipped": 0, "failed": 0}
    assert pl.read_parquet(out / "yellow_tripdata_2024-01.parquet").height == 1
    assert not list(out.glob("*.tmp"))

    assert transform_main.run_transform([2024])["skipped"] == 1
    assert transform_main.run_transform([2024], force=True)["success"] == 1


def test_transform_all_filters_years_and_survives_bad_file(make_trips, tmp_path, monkeypatch):
    raw, out = _setup_dirs(monkeypatch, tmp_path)
    make_trips([{}]).write_parquet(raw / "yellow_tripdata_2024-01.parquet")
    make_trips([{}]).write_parquet(raw / "yellow_tripdata_2023-01.parquet")
    (raw / "yellow_tripdata_2024-02.parquet").write_bytes(b"garbage")

    summary = transform_main.run_transform([2024])
    assert summary == {"success": 1, "skipped": 0, "failed": 1}
    assert [p.name for p in out.glob("*.parquet")] == ["yellow_tripdata_2024-01.parquet"]
    assert not list(out.glob("*.tmp"))


def _fake_raw_file(tmp_path):
    """Small raw file mirroring the real TLC columns, with deliberately bad rows."""
    df = pl.DataFrame({
        "tpep_pickup_datetime": [
            datetime(2023, 1, 1, 8, 0, 0),  # good
            datetime(2023, 1, 1, 9, 0, 0),  # good
            datetime(2023, 1, 1, 10, 0, 0),  # bad: zero distance
            datetime(2023, 1, 1, 11, 0, 0),  # bad: trip too short
            None,  # bad: null pickup time
        ],
        "tpep_dropoff_datetime": [
            datetime(2023, 1, 1, 8, 15, 0),
            datetime(2023, 1, 1, 9, 20, 0),
            datetime(2023, 1, 1, 10, 10, 0),
            datetime(2023, 1, 1, 11, 0, 30),
            datetime(2023, 1, 1, 12, 0, 0),
        ],
        "passenger_count": [1, 2, 1, 1, 1],
        "trip_distance": [2.5, 5.0, 0.0, 1.0, 3.0],
        "fare_amount": [12.0, 20.0, 8.0, 5.0, 15.0],
        "total_amount": [15.0, 24.0, 10.0, 6.0, 18.0],
        "payment_type": [1, 1, 2, 1, 1],
        "PULocationID": [100, 150, 200, 75, 50],
        "DOLocationID": [101, 151, 201, 76, 51],
    })
    path = tmp_path / "yellow_tripdata_2023-01.parquet"
    df.write_parquet(path)
    return path


def test_transform_layer_on_file_keeps_only_valid_rows(tmp_path):
    result, stats = transform_layer(_fake_raw_file(tmp_path))
    assert result.height == 2
    assert stats["rows_in"] == 5 and stats["rows_out"] == 2
    assert (result["trip_distance"] > 0).all()
    assert (result["trip_duration_sec"] > 60).all()
    assert result["pickup_at"].null_count() == 0
    assert set(result.columns) == set(OUTPUT_COLUMNS)
