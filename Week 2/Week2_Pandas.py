import sys
import time
import pandas as pd
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
    if len(sys.argv) != 4:
        print("Error: missing arguments.")
        print("Example: python lab2.py 2022_place.csv '2022-04-01 12' '2022-04-01 13'")    
        sys.exit(1)

     # read arguments
    csv_file = sys.argv[1]
    start_hour = parse_hour(sys.argv[2])
    end_hour = parse_hour(sys.argv[3])

    # check if end hour comes after start hour
    if end_hour <= start_hour:
        print("Error: End hour must be after start hour.")
        sys.exit(1)

    # set up counters, chunksize, and total_rows counter
    color_counts = {}
    pixel_counts = {}
    chunk_size = 500_000
    total_rows = 0

    # starting time
    start_time = time.perf_counter_ns()

    # reads CSV file in chunks
    try:
        reader = pd.read_csv(
            csv_file,
            chunksize=chunk_size,
            usecols=["timestamp", "pixel_color", "coordinate"]
        )

        # process each chunk
        for chunk in reader:
            total_rows += len(chunk)

            if total_rows % 500_000 == 0:
                print(f"Processed {total_rows} rows...")

            # parse timestamps
            chunk["timestamp"] = pd.to_datetime(
                chunk["timestamp"].str.replace(" UTC", ""),
                errors="coerce"
            )

            # filter timeframe
            chunk = chunk[
                (chunk["timestamp"] >= start_hour) &
                (chunk["timestamp"] < end_hour)
            ]

            # update color counts
            for color, count in chunk["pixel_color"].value_counts().items():
                color_counts[color] = color_counts.get(color, 0) + count

            # update pixel counts
            for coord, count in chunk["coordinate"].value_counts().items():
                pixel_counts[coord] = pixel_counts.get(coord, 0) + count

    # handles missing fille error
    except FileNotFoundError:
        print(f"Error: file '{csv_file}' not found.")
        sys.exit(1)

    # exit if no pixels found in timeframe
    if not color_counts or not pixel_counts:
        print("No pixels found in this timeframe.")
        sys.exit(1)

    # finds the most placed colors and pixel
    most_color = max(color_counts, key=color_counts.get)
    most_pixel = max(pixel_counts, key=pixel_counts.get)

    # stop timing
    end_time = time.perf_counter_ns()
    time_ms = (end_time - start_time) / 1_000_000

    print(f"Timeframe: {sys.argv[2]} to {sys.argv[3]}")
    print(f"Execution Time: {time_ms:.2f} ms")
    print(f"Most Placed Color: {most_color}")
    print(f"Most Placed Pixel Location: {most_pixel}")

if __name__ == "__main__":
    main()