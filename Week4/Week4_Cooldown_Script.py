import duckdb
import pandas as pd
from datetime import datetime, timezone

parquet_file = "2022_place.parquet"
output_csv_file = "superhuman_pixels.csv"
chunk_hours = 2   # process data in 2-hour chunks to reduce memory usage

def allowed_cooldown_seconds(ts_epoch):
    """
    Returns the minimum allowed delay between pixels (in seconds) for a given timestamp.
    r/place 2022 rules:
        - Before 5:40 EST Apr 1 -> 10 minutes (600s)
        - After 5:40 EST Apr 1 -> 5 minutes (300s)
    """
    # 5:40 EST Apr 1, 2022 -> 2022-04-01 09:40 UTC
    cooldown_switch_epoch = datetime(2022, 4, 1, 9, 40, 0, tzinfo=timezone.utc).timestamp()
    if ts_epoch < cooldown_switch_epoch:
        return 600
    else:
        return 300

db_conn = duckdb.connect()
db_conn.execute("PRAGMA timezone='UTC';")
db_conn.execute("SET preserve_insertion_order=false;")
db_conn.execute("SET threads=2;")

min_timestamp, max_timestamp = db_conn.execute(f"""
    SELECT MIN(EXTRACT('epoch' FROM timestamp)) AS min_ts,
           MAX(EXTRACT('epoch' FROM timestamp)) AS max_ts
    FROM read_parquet('{parquet_file}')
""").fetchone()

print(f"Data time range: {datetime.fromtimestamp(min_timestamp, tz=timezone.utc)} to "
      f"{datetime.fromtimestamp(max_timestamp, tz=timezone.utc)}")

# chunks data
current_start_time = min_timestamp
superhuman_results = []

while current_start_time < max_timestamp:
    current_end_time = min(current_start_time + chunk_hours * 3600, max_timestamp)
    print(f"Processing chunk: {datetime.fromtimestamp(current_start_time, tz=timezone.utc)} to "
          f"{datetime.fromtimestamp(current_end_time, tz=timezone.utc)}")

    query = f"""
    WITH ordered AS (
        SELECT
            user_id,
            timestamp,
            CAST(str_split(coordinate, ',')[1] AS INTEGER) AS x_coord,
            CAST(str_split(coordinate, ',')[2] AS INTEGER) AS y_coord,
            LAG(EXTRACT('epoch' FROM timestamp)) OVER (PARTITION BY user_id ORDER BY timestamp) AS prev_ts_epoch
        FROM read_parquet('{parquet_file}')
        WHERE EXTRACT('epoch' FROM timestamp) >= {current_start_time}
          AND EXTRACT('epoch' FROM timestamp) < {current_end_time}
    ),
    diffs AS (
        SELECT
            user_id,
            timestamp,
            x_coord,
            y_coord,
            prev_ts_epoch,
            EXTRACT('epoch' FROM timestamp) - prev_ts_epoch AS delta_seconds
        FROM ordered
        WHERE prev_ts_epoch IS NOT NULL
    )
    SELECT *
    FROM diffs
    """

    chunk_df = db_conn.execute(query).fetchdf()

    if not chunk_df.empty:
        chunk_df['allowed_cooldown'] = chunk_df['prev_ts_epoch'].apply(allowed_cooldown_seconds)
        # keep only rows where the interval is shorter than allowed
        chunk_df = chunk_df[chunk_df['delta_seconds'] < chunk_df['allowed_cooldown']]
        if not chunk_df.empty:
            superhuman_results.append(chunk_df[['user_id', 'timestamp', 'x_coord', 'y_coord']])

    current_start_time = current_end_time

# combine chunks
if superhuman_results:
    all_superhuman = pd.concat(superhuman_results, ignore_index=True)
    all_superhuman.to_csv(output_csv_file, index=False)
    print(f"Saved {len(all_superhuman)} superhuman pixels to {output_csv_file}")
else:
    print("No superhuman pixels detected after applying cooldown rules.")

db_conn.close()
