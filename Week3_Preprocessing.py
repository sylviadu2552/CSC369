import duckdb
import sys

# check for if there's correct number of input
if len(sys.argv) != 3:
    print("Usage: python Week3_Preprocessing.py input.parquet output_prefix")
    sys.exit(1)

# read arguments
PARQUET_PATH = sys.argv[1]
OUT_PREFIX = sys.argv[2]

# set outfile names
PREPROCESSED_PATH = f"{OUT_PREFIX}.parquet"
USER_FIRST_PATH = "user_first.parquet"

# map hex codes to english names
HEX_TO_GROUP = {
    "#6D001A": "dark red",
    "#BE0039": "bright red",
    "#FF4500": "red orange",
    "#FF3881": "pink",
    "#FF99AA": "light pink",
    "#DE107F": "magenta",
    "#FFA800": "orange",
    "#FFB470": "light orange",
    "#FFD635": "yellow",
    "#FFF8B8": "pale yellow",
    "#00A368": "dark green",
    "#00CC78": "green",
    "#7EED56": "light green",
    "#00756F": "dark teal",
    "#009EAA": "teal",
    "#00CCC0": "light teal",
    "#2450A4": "blue",
    "#3690EA": "bright blue",
    "#51E9F4": "cyan",
    "#493AC1": "indigo",
    "#6A5CFF": "violet blue",
    "#94B3FF": "light blue",
    "#811E9F": "purple",
    "#B44AC0": "lavender",
    "#E4ABFF": "light purple",
    "#6D482F": "brown",
    "#9C6926": "golden brown",
    "#515252": "dark gray",
    "#898D90": "gray",
    "#D4D7D9": "light gray",
    "#000000": "black",
    "#FFFFFF": "white",
}

# create SQL for color mapping table
group_values_sql = "SELECT * FROM (VALUES\n" + ",\n".join(
    [f"('{h}', '{g}')" for h, g in HEX_TO_GROUP.items()]
) + "\n) AS t(hex, color_group)"

# connect/set up duckdb
con = duckdb.connect(database=":memory:")
con.execute("PRAGMA threads=8;")
con.execute("PRAGMA timezone='UTC';")  # IMPORTANT

# preprocessing the data
preprocess_sql = f"""
WITH raw AS (
  SELECT
    CAST(timestamp AS TIMESTAMP) AS ts,
    user_id,
    UPPER(pixel_color) AS hex,
    REPLACE(REPLACE(coordinate, '"', ''), ' ', '') AS coord
  FROM read_parquet('{PARQUET_PATH}')
),
mapped AS (
  SELECT
    CAST(epoch(ts) AS INTEGER) AS ts_s,
    CAST(hash(user_id) AS UBIGINT) AS user_key,
    g.color_group,
    str_split(coord, ',') AS parts
  FROM raw
  JOIN ({group_values_sql}) g ON raw.hex = g.hex
  WHERE ts IS NOT NULL AND user_id IS NOT NULL
)
SELECT
  ts_s,
  user_key,
  color_group,
  CASE
    WHEN list_count(parts) = 2 THEN 1
    WHEN list_count(parts) = 4 THEN
      (abs(CAST(parts[3] AS INTEGER) - CAST(parts[1] AS INTEGER)) + 1) *
      (abs(CAST(parts[4] AS INTEGER) - CAST(parts[2] AS INTEGER)) + 1)
    ELSE 1
  END AS weight
FROM mapped
"""

# export to preprocessed parquet
con.execute(f"""
COPY ({preprocess_sql})
TO '{PREPROCESSED_PATH}'
(FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE);
""")

# export to user first pixel parquet
con.execute(f"""
COPY (
  SELECT user_key, MIN(ts_s) AS first_ts_s
  FROM read_parquet('{PREPROCESSED_PATH}')
  GROUP BY user_key
)
TO '{USER_FIRST_PATH}'
(FORMAT PARQUET, COMPRESSION ZSTD, OVERWRITE);
""")

con.close()

print("Pre-processing complete")
print("Preprocessed file:", PREPROCESSED_PATH)
print("User-first file:", USER_FIRST_PATH)
