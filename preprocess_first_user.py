import duckdb

con = duckdb.connect()

con.execute("""
    COPY (
        SELECT
            user_id,
            MIN(timestamp) AS first_pixel_time
        FROM read_parquet('2022_place.parquet')
        GROUP BY user_id
    )
    TO 'user_first_pixel.parquet' (FORMAT PARQUET)
""")

print("Saved user_first_pixel.parquet")
