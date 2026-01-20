import sys
import time
import duckdb
from datetime import datetime

def parse_hour(time_str):
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H")
    except ValueError:
        print("Error: Inputted time is not in proper format. Format must be YYYY-MM-DD HH")
        sys.exit(1)

def main():
    if len(sys.argv) != 4:
        print("Error: missing arguments.")
        print("Example: python Week2_DuckDB.py 2022_place.parquet '2022-04-01 12' '2022-04-01 13'")
        sys.exit(1)

    parquet_file = sys.argv[1]
    start_hour = parse_hour(sys.argv[2])
    end_hour = parse_hour(sys.argv[3])

    if end_hour <= start_hour:
        print("Error: End hour must be after start hour.")
        sys.exit(1)

    start_time = time.perf_counter_ns()

    con = duckdb.connect()

    # rows processed (entire file)
    rows_processed = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{parquet_file}')"
    ).fetchone()[0]

    # most placed color
    most_color = con.execute(
        f"""
        SELECT pixel_color
        FROM read_parquet('{parquet_file}')
        WHERE timestamp >= '{start_hour}' AND timestamp < '{end_hour}'
        GROUP BY pixel_color
        ORDER BY COUNT(*) DESC
        LIMIT 1
        """
    ).fetchone()[0]

    # most placed pixel location
    most_pixel = con.execute(
        f"""
        SELECT coordinate
        FROM read_parquet('{parquet_file}')
        WHERE timestamp >= '{start_hour}' AND timestamp < '{end_hour}'
        GROUP BY coordinate
        ORDER BY COUNT(*) DESC
        LIMIT 1
        """
    ).fetchone()[0]

    end_time = time.perf_counter_ns()
    time_ms = (end_time - start_time) / 1_000_000

    print(f"Timeframe: {sys.argv[2]} to {sys.argv[3]}")
    print(f"Execution Time: {time_ms:.2f} ms")
    print(f"Most Placed Color: {most_color}")
    print(f"Most Placed Pixel Location: {most_pixel}")

if __name__ == "__main__":
    main()
