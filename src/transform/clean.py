import polars as pl
from pathlib import Path
from src.extract.logger import setup_logger

log = setup_logger(__name__)



def transform_layer(path: Path):
    """
    Load the data and Transform by removing null values, renaming the columns etc
    """

    df = pl.read_parquet(path)
    log.info("File Path Read Successfully and Traforming Layer.")

    df = (
        df
        .drop_nulls(subset=["tpep_pickup_datetime", 
                            "tpep_dropoff_datetime",
                            "passenger_count"])
        .with_columns([
            pl.col("tpep_pickup_datetime").alias("pickup_at"),
            pl.col("tpep_dropoff_datetime").alias("dropoff_at"),
            pl.col("PULocationID").alias("pu_location_id"),      
            pl.col("DOLocationID").alias("do_location_id"), 
            pl.col("passenger_count").cast(pl.Int32),
            pl.col("trip_distance").cast(pl.Float32),
            pl.col("fare_amount").cast(pl.Float32),
            pl.col("total_amount").cast(pl.Float32),
            ])
        .with_columns([
            (pl.col("dropoff_at") - pl.col("pickup_at"))
                .dt.total_seconds().alias("trip_duration_sec"),
             pl.col("pickup_at").dt.hour().alias("pickup_hour"),
             pl.col("pickup_at").dt.weekday().alias("pickup_weekday"),
        ])

        #Filter out bad data 
        .filter(
            (pl.col("trip_distance") > 0) &
            (pl.col("fare_amount") > 0) &
            (pl.col("trip_duration_sec") > 60)
        )

        .select([
            "pickup_at", "dropoff_at", "pickup_hour", "pickup_weekday", "trip_duration_sec", "trip_distance", "passenger_count", "fare_amount", "total_amount", "payment_type", "pu_location_id", "do_location_id"])

    )

    log.info("Transofrming Layer Succesfully completed")

    return df