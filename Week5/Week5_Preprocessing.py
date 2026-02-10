import duckdb
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: python preprocess_parquet_safe.py input.parquet output.parquet")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    con = duckdb.connect()

    preprocess_sql = f"""
    SELECT
        CAST(epoch(timestamp) AS DOUBLE) AS t,
        pixel_color AS color,
        CAST(split_part(coordinate, ',', 1) AS INTEGER) AS x,
        CAST(split_part(coordinate, ',', 2) AS INTEGER) AS y
    FROM read_parquet('{input_file}')
    """

    con.execute(f"""
    COPY ({preprocess_sql})
    TO '{output_file}'
    (FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE)
    """)

    con.close()
    print("✅ Preprocessing complete")
    print("Output file:", output_file)

if __name__ == "__main__":
    main()
