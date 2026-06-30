"""
    src.transform.transformLayer.py

    Logic of Transforming or cleaning the data using functions in the clean.py 

"""

from src.transform.clean import transform_layer
from src.extract.config import *
from src.extract.logger import setup_logger


log = setup_logger(__name__)



def run_transform(years: list[int] = YEARS):
    """
    Run transform_layer() on every raw parquet file that hasn't been processed yet.
    Reads from data/raw/yellow_taxi/  →  writes to data/processed/yellow_taxi/
    """
    raw_files = sorted(RAW_DIR.glob("yellow_tripdata_*.parquet"))
    if years:
        filtered_files = []

        for f in raw_files:
            for y in years:
                log.info(y)
                if str(y) in f.name:
                    filtered_files.append(f)
                    break

        raw_files = filtered_files
    
    log.info("Found %d raw files to transform", len(raw_files))
    success, skipped, failed = 0, 0, 0

    for raw_path in raw_files:
        relative = raw_path.relative_to(RAW_DIR)
        output = PROCESSED_DIR / relative

        if output.exists():
            log.info("Already processed skipping: %s", raw_path.name)
            skipped += 1
            continue

        try:
            df = transform_layer(raw_path)

            output.parent.mkdir(parents=True, exist_ok=True)
            df.write_parquet(output, compression="snappy")
            log.info("Written: %s (%d rows)", output.name, df.shape[0])

            success +=1

        except Exception as exc:
            log.error("Failed on %s: %s", raw_path.name, exc)
            failed +=1
    
    log.info("Transform done. Success= %d skipped=%d failed=%d", success, skipped, failed)