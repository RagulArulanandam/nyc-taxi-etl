"""
tests/test_helpers.py
"""

from src.extract.helper import *

def test_build_url():
    url = build_url(2023,1)
    assert url == "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet"

def test_build_url_handles_december():
    url = build_url(2023,12)
    assert url == "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-12.parquet"


def test_build_local_path_include_year_folder():
    path = build_local_path(2024, 1)
    assert "2024" in str(path)
    assert "2024-01" in str(path)  # Assuming the current month is June 2024


def test_validate_parquet_rejects_missing_file(tmp_path):
    fake_path = tmp_path / "non_existent_file.parquet"
    valid, reason = validate_parquet(fake_path)
    assert valid is False
    assert "does not exist" in reason

def test_validate_parquet_rejects_tiny_file(tmp_path):
    tiny_file = tmp_path / "tiny.parquet"
    tiny_file.write_bytes(b"PAR1")   # only 4 bytes, way under MIN_FILESIZE

    valid, reason = validate_parquet(tiny_file)
    assert valid is False
    assert "too small" in reason


# def test_validate_parquet_rejects_bad_magic_bytes(tmp_path):
#     fake_file = tmp_path / "fake.parquet"
#     # 2000 bytes of junk — big enough to pass the size check, but wrong header/footer
#     fake_file.write_bytes(b"NOTPARQUET" * 200)

#     valid, reason = validate_parquet(fake_file)
#     assert valid is False
#     assert "magic bytes" in reason


def test_validate_parquet_accepts_valid_file(tmp_path):
    real_file = tmp_path / "real.parquet"
    # Build minimal valid-looking content: PAR1 header ... PAR1 footer, padded to pass size check
    content = b"PAR1" + (b"x" * 2000) + b"PAR1"
    real_file.write_bytes(content)

    valid, reason = validate_parquet(real_file)
    assert valid is True
    assert reason == "" 