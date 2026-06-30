"""
src/load/load_postgres.py
"""

import time
import io
from pathlib import Path
 
import polars as pl
from src.extract.logger import setup_logger



log = setup_logger(__name__)



DB_COLUMNS = [
    "pickup_at",
    "dropoff_at",
    "pickup_hour",
    "pickup_weekday",
    "trip_duration_sec",
    "trip_distance",
    "passenger_count",
    "fare_amount",
    "total_amount",
    "payment_type",
    "pu_location_id",
    "do_location_id",
]

def get_loaded_files(conn) -> set[str]:
    """
    Get the set of already loaded files from the PostgreSQL database.

    Args:
        conn: psycopg2 connection object.
    """

    with conn.cursor() as cur:
        cur.execute("""
            CREATE  TABLE IF NOT EXISTS load_log (
                filename TEXT PRIMARY KEY,
                rows_loaded integer,
                loaded_at TIMESTAMP DEFAULT NOW())
        """)

        conn.commit()
        cur.execute("SELECT filename from load_log")
        return {row[0] for row in cur.fetchall()}



def record_loaded_file(conn, filename: str, rows: int):
    """
    Record the loaded file in the PostgreSQL database.

    Args:
        conn: psycopg2 connection object.
        filename (str): Name of the loaded file.
        rows (int): Number of rows loaded from the file.
    """
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO load_log (filename, rows_loaded) VALUES (%s, %s) ON CONFLICT (filename) DO NOTHING",
            (filename, rows),
        )
    conn.commit()


# CORE LOAD FUNCTION
def load_file(parquet_path: Path, conn) -> int:
    """
     Load one processed parquet file into yellow_trips via COPY.
    Returns the number of rows inserted.
    """
    tO = time.time()

    # Read the Parquet file into a Polars DataFrame
    df = pl.read_parquet(parquet_path).select(DB_COLUMNS)
    row_count = df.shape[0]

    buf = io.BytesIO()
    df.write_csv(buf)
    buf.seek(0) 

    with conn.cursor() as cur:
        columns = ", ".join(DB_COLUMNS)
        cur.copy_expert(
            f"COPY yellow_trips ({columns}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE)",
            buf,
        )
    conn.commit()

    elapsed = time.time() - tO
    rate = row_count / elapsed if elapsed > 0 else 0
    log.info(
        "Loaded %s: %d rows in %.1fs (%.0f rows/sec)",
        parquet_path.name, row_count, elapsed, rate
    )

    return row_count

