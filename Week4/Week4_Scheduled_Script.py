import duckdb
import pandas as pd
from datetime import datetime, timezone

#config
input_file = "2022_place.parquet"
output_intervals_file = "pixel_intervals.csv.gz"
output_user_stats_file = "user_stats.csv"
output_suspects_file = "suspected_bots.csv"

std_dev_threshold = 5.0    # low std indicates bot-like consistency
min_pixel_count = 10       # minimum pixels to consider for suspicion
chunk_size_hours = 2       # process data in 2-hour chunks

db_conn = duckdb.connect(database=':memory:')


min_timestamp, max_timestamp = db_conn.execute(f"""
    SELECT MIN(EXTRACT('epoch' FROM timestamp)), MAX(EXTRACT('epoch' FROM timestamp))
    FROM read_parquet('{input_file}')
""").fetchone()

print(f"Time range: {datetime.fromtimestamp(min_timestamp, tz=timezone.utc)} to "
      f"{datetime.fromtimestamp(max_timestamp, tz=timezone.utc)}")


current_start_time = min_timestamp
first_chunk_flag = True  # only write header for the first chunk

while current_start_time < max_timestamp:
    current_end_time = min(current_start_time + chunk_size_hours * 3600, max_timestamp)
    print(f"Processing chunk: {datetime.fromtimestamp(current_start_time, tz=timezone.utc)} to "
          f"{datetime.fromtimestamp(current_end_time, tz=timezone.utc)}")

    query = f"""
    WITH parsed AS (
        SELECT
            user_id,
            timestamp::TIMESTAMP AS ts,
            CAST(split_part(coordinate, ',', 1) AS INTEGER) AS x_coord,
            CAST(split_part(coordinate, ',', 2) AS INTEGER) AS y_coord
        FROM read_parquet('{input_file}')
        WHERE EXTRACT('epoch' FROM timestamp) >= {current_start_time}
          AND EXTRACT('epoch' FROM timestamp) < {current_end_time}
    ),
    ordered AS (
        SELECT
            user_id,
            ts,
            x_coord, y_coord,
            LAG(EXTRACT('epoch' FROM ts)) OVER (PARTITION BY user_id ORDER BY ts) AS prev_ts
        FROM parsed
    ),
    intervals AS (
        SELECT
            user_id,
            ts,
            x_coord, y_coord,
            EXTRACT('epoch' FROM ts) - prev_ts AS interval_seconds
        FROM ordered
        WHERE prev_ts IS NOT NULL
    )
    SELECT * FROM intervals
    """

    chunk_df = db_conn.execute(query).fetchdf()
    if not chunk_df.empty:
        chunk_df.to_csv(output_intervals_file, mode='a', header=first_chunk_flag, index=False, compression='gzip')
        first_chunk_flag = False

    current_start_time = current_end_time

# user stats
intervals_df = pd.read_csv(output_intervals_file, compression='gzip')

user_summary = intervals_df.groupby('user_id')['interval_seconds'].agg(
    mean_interval='mean',
    std_interval='std',
    total_pixels='count'
).reset_index()

user_summary.to_csv(output_user_stats_file, index=False)

# flag sus users
suspected_bots = user_summary[
    (user_summary['std_interval'] <= std_dev_threshold) &
    (user_summary['total_pixels'] >= min_pixel_count)
]

suspected_bots.to_csv(output_suspects_file, index=False)

print("Processing complete. Compressed CSVs are ready for visualization and analysis.")
