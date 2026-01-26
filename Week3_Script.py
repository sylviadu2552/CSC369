import sys
import time
import duckdb
from datetime import datetime

# helper function
def parse_hour(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H")
    except ValueError:
        print("Error: Inputted time is not in proper format. Format must be YYYY-MM-DD HH")
        sys.exit(1)

def main():
     # check for if there's the correct number of inputs
    if len(sys.argv) != 5:
        print("Error: missing arguments.")
        print("Example: python Week3_Script.py data.parquet user_first_pixel.parquet 'YYYY-MM-DD HH' 'YYYY-MM-DD HH'")
        sys.exit(1)

    # read arguments
    data_file = sys.argv[1]
    first_pixel_file = sys.argv[2]
    start_hour = parse_hour(sys.argv[3])
    end_hour = parse_hour(sys.argv[4])

    # check if end hour comes after start hour
    if end_hour <= start_hour:
        print("Error: End hour must be after start hour.")
        sys.exit(1)

    # connects duckdb
    con = duckdb.connect()

    # 1.) Ranking of colors by distinct users
    start_time_colors = time.perf_counter_ns()

    colors_by_users = con.execute(f"""
        SELECT pixel_color, COUNT(DISTINCT user_id) AS distinct_users
        FROM read_parquet('{data_file}')
        WHERE timestamp >= '{start_hour}' AND timestamp < '{end_hour}'
        GROUP BY pixel_color
        ORDER BY distinct_users DESC
    """).fetchdf()

    end_time_colors = time.perf_counter_ns()

    # 2.) Average session length
    start_time_sessions = time.perf_counter_ns()

    avg_session = con.execute(f"""
        WITH ordered AS (
            SELECT user_id, timestamp,
                LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp) AS prev_time
            FROM read_parquet('{data_file}')
            WHERE timestamp >= '{start_hour}' AND timestamp < '{end_hour}'
        ),
        sessions AS (
            SELECT user_id, timestamp,
                SUM(CASE WHEN prev_time IS NULL OR EXTRACT(EPOCH FROM timestamp - prev_time) > 900
                         THEN 1 ELSE 0 END)
                    OVER (PARTITION BY user_id ORDER BY timestamp) AS session_id
            FROM ordered
        ),
        session_lengths AS (
            SELECT user_id, session_id,
                (MAX(timestamp) - MIN(timestamp)) AS length_interval
            FROM sessions
            GROUP BY user_id, session_id
            HAVING COUNT(*) > 1
        )
        SELECT AVG(EXTRACT(EPOCH FROM length_interval)) AS avg_session_seconds
        FROM session_lengths
    """).fetchone()[0]

    end_time_sessions = time.perf_counter_ns()

    # 3.) Percentiles of pixels placed by users
    start_time_percentiles = time.perf_counter_ns()

    percentiles = con.execute(f"""
        SELECT
            percentile_cont(0.50) WITHIN GROUP (ORDER BY count_pixels) AS p50,
            percentile_cont(0.75) WITHIN GROUP (ORDER BY count_pixels) AS p75,
            percentile_cont(0.90) WITHIN GROUP (ORDER BY count_pixels) AS p90,
            percentile_cont(0.99) WITHIN GROUP (ORDER BY count_pixels) AS p99
        FROM (
            SELECT user_id, COUNT(*) AS count_pixels
            FROM read_parquet('{data_file}')
            WHERE timestamp >= '{start_hour}' AND timestamp < '{end_hour}'
            GROUP BY user_id
        )
    """).fetchdf()

    end_time_percentiles = time.perf_counter_ns()

    # 4.) Count first-time users
    start_time_first_users = time.perf_counter_ns()

    first_users = con.execute(f"""
        SELECT COUNT(*) AS first_time_users
        FROM read_parquet('{first_pixel_file}')
        WHERE first_pixel_time >= '{start_hour}' AND first_pixel_time < '{end_hour}'
    """).fetchone()[0]

    end_time_first_users = time.perf_counter_ns()


    ### Ouputs Results
    print(f"Timeframe: {start_hour} to {end_hour}\n")

    print("1.) Colors ranked by distinct users:")
    print(colors_by_users.head(10))
    print()

    print("2.) Average session length:")
    print(avg_session, "seconds")
    print()

    print("3.) Pixel placement percentiles:")
    print(percentiles)
    print()

    print("4.) Number of first-time users:")
    print(first_users)
    print()

    print("Execution time:")
    print("- Colors:", (end_time_colors - start_time_colors) / 1_000_000, "ms")
    print("- Sessions:", (end_time_sessions - start_time_sessions) / 1_000_000, "ms")
    print("- Percentiles:", (end_time_percentiles - start_time_percentiles) / 1_000_000, "ms")
    print("- First Users:", (end_time_first_users - start_time_first_users) / 1_000_000, "ms")


if __name__ == "__main__":
    main()
