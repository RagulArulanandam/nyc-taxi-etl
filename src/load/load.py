"""
src/load/main.py
 
Entry point for the load step.
Orchestrates the loop over all processed parquet files —
all loading logic lives in load.py.
 
Run directly:
    python -m src.load.main
"""

import os
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

from src.extract.config import *
from src.extract.logger import setup_logger
from src.load.load_postgres import load_file, get_loaded_files, record_loaded_file

load_dotenv()  # Load environment variables from .env file

log = setup_logger(__name__)

POSTGRES_URL = os.getenv("POSTGRES_URL")

def run_load(years: list[int] = YEARS) -> dict:
    """
    Load all processed parquet files into PostgreSQL.
    Skips files already recorded in load_log.
    """

    summary = {
        "attempted": 0,
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "total_rows_loaded": 0
    }

    if not POSTGRES_URL:
        log.error("PostgreSQL URL not found in environment variables.")
        return summary
    
    parquet_files = sorted(PROCESSED_DIR.rglob("yellow_tripdata_*.parquet"))

    if years:
        parquet_files = [f for f in parquet_files if any(f"_{year}-" in f.name for year in years)]
    
    if not parquet_files:
        log.warning("No parquet files found to load %s", PROCESSED_DIR)
        return summary
    
    log.info("Found %d parquet files to load.", len(parquet_files))

    try:
        conn = psycopg2.connect(POSTGRES_URL)
        log.info("Connection to PostgreSQL database established successfully.")
    except psycopg2.OperationalError as e:
        log.error("Error connecting to PostgreSQL database: %s", e)
        return summary
    except Exception as e:
        log.error("Unexpected error connecting to PostgreSQL database: %s", e)
        return summary
    
    try:
        with conn:
            loaded_files = get_loaded_files(conn)

            for path in parquet_files:
                summary["attempted"] += 1
                if path.name in loaded_files:
                    log.info("Skipping already loaded file: %s", path.name)
                    summary["skipped"] += 1
                    continue

                try:
                    rows_loaded = load_file(path, conn)
                    record_loaded_file(conn, path.name, rows_loaded)
                    summary["total_rows_loaded"] += rows_loaded
                    summary["success"] += 1
                except Exception as e:
                    log.error("Error loading file %s: %s", path.name, e)
                    conn.rollback()  # Rollback in case of error
                    summary["failed"] += 1

            # in src/load/main.py, inside run(), after the for-loop over parquet_files
            refresh_views(conn)
            log.info("Materialized views refreshed")    
            
    except Exception as e:
        log.error("Unexpected error during load process: %s", e)
    finally:
        conn.close()
        log.info("Connection to PostgreSQL database closed.")

    
    log.info("Done. attempted=%d success=%d skipped=%d failed=%d total_rows_loaded=%d",
             summary["attempted"], summary["success"], summary["skipped"], summary["failed"], summary["total_rows_loaded"])

    return summary


def refresh_views(conn):
    with conn.cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW mv_hourly_demand;")
        cur.execute("REFRESH MATERIALIZED VIEW mv_top_zones;")
        cur.execute("REFRESH MATERIALIZED VIEW mv_monthly_trend;")
    conn.commit()



if __name__ == "__main__":
    
    run_load(years=[2023, 2024])


    

    