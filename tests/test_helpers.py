from datetime import date

from src.extract import helpers
from src.extract.config import BASE_URL


def test_build_url():
    assert helpers.build_url(2024, 3) == f"{BASE_URL}/yellow_tripdata_2024-03.parquet"


def test_build_local_path_pads_month():
    assert helpers.build_local_path(2023, 1).name == "yellow_tripdata_2023-01.parquet"


def test_is_future_respects_publication_lag():
    today = date(2024, 6, 15)
    assert not helpers.is_future(2024, 4, today)  # two months back: published
    assert helpers.is_future(2024, 5, today)
    assert helpers.is_future(2025, 1, today)
    assert not helpers.is_future(2023, 12, today)


def test_is_future_across_year_boundary():
    today = date(2024, 1, 10)
    assert not helpers.is_future(2023, 11, today)
    assert helpers.is_future(2023, 12, today)


def test_validate_parquet_missing(tmp_path):
    ok, reason = helpers.validate_parquet(tmp_path / "nope.parquet")
    assert not ok and "does not exist" in reason


def test_validate_parquet_too_small(tmp_path):
    f = tmp_path / "a.parquet"
    f.write_bytes(b"PAR1")
    ok, reason = helpers.validate_parquet(f)
    assert not ok and "too small" in reason


def test_validate_parquet_bad_magic(tmp_path):
    f = tmp_path / "a.parquet"
    f.write_bytes(b"x" * 2048)
    ok, reason = helpers.validate_parquet(f)
    assert not ok and "magic" in reason


def test_validate_parquet_ok(tmp_path):
    f = tmp_path / "a.parquet"
    f.write_bytes(b"PAR1" + b"x" * 2048 + b"PAR1")
    assert helpers.validate_parquet(f) == (True, "")


def test_file_md5(tmp_path):
    f = tmp_path / "a.bin"
    f.write_bytes(b"hello")
    assert helpers.file_md5(f) == "5d41402abc4b2a76b9719d911017c592"
