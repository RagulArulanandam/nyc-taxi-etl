import polars as pl

df = pl.read_parquet("data/raw/2024/yellow_tripdata_2024-01.parquet")

print(df.head())
print(df.schema)
print(df.columns)