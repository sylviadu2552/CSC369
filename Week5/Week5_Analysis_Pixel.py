import duckdb
import numpy as np
from PIL import Image
from tqdm import tqdm
import imageio
import math
from collections import Counter

# =====================
# SETTINGS
# =====================
parquet_file = "2022_place_cleaned.parquet"
output_gif = "prediction.gif"

canvas_size = 2000
frame_interval = 300
number_of_frames = 90

whiteout_offset_seconds = 82*3600 + 4*60
whiteout_frame_count = 15

inertia_strength = 0.85
neighbor_influence = 0.35
max_neighbors_considered = 4

# =====================
# HELPER FUNCTIONS
# =====================
def hex_to_rgb(hex_color):
    """convert hex string like '#FF00FF' to (255,0,255)"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2],16) for i in (0,2,4))

def rgb_to_hex(rgb_color):
    """convert (255,0,255) back to hex string"""
    return "#{:02X}{:02X}{:02X}".format(*rgb_color)

# =====================
# LOAD DATA
# =====================
conn = duckdb.connect()
print("Reading parquet file...")

time_min, time_max = conn.execute(f"""
SELECT MIN(t), MAX(t) FROM read_parquet('{parquet_file}')
""").fetchone()

whiteout_start_time = time_min + whiteout_offset_seconds

# =====================
# CALCULATE PIXEL STATISTICS
# =====================
print("Calculating pixel histories...")

conn.execute(f"""
CREATE TEMP TABLE pixel_counts AS
SELECT x, y, color, COUNT(*) as count
FROM read_parquet('{parquet_file}')
WHERE t < {whiteout_start_time}
GROUP BY x, y, color
""")

conn.execute("""
CREATE TEMP TABLE pixel_probabilities AS
SELECT x, y, color,
       count / SUM(count) OVER (PARTITION BY x,y) as probability
FROM pixel_counts
""")

conn.execute(f"""
CREATE TEMP TABLE pixel_change_rates AS
SELECT x, y, COUNT(*) / ({whiteout_start_time}-MIN(t)) as change_rate
FROM read_parquet('{parquet_file}')
WHERE t < {whiteout_start_time}
GROUP BY x, y
""")

pixel_prob_rows = conn.execute("SELECT x, y, color, probability FROM pixel_probabilities").fetchall()
pixel_rate_rows = conn.execute("SELECT x, y, change_rate FROM pixel_change_rates").fetchall()

conn.close()

# =====================
# BUILD DICTIONARIES
# =====================
pixel_probabilities = {}
for x, y, color, probability in pixel_prob_rows:
    pixel_probabilities.setdefault((x, y), []).append((color, probability))

pixel_change_rate = {(x, y): rate for x, y, rate in pixel_rate_rows}

# =====================
# INITIAL CANVAS
# =====================
canvas = np.full((canvas_size, canvas_size, 3), 255, dtype=np.uint8)

for (x, y), color_probs in pixel_probabilities.items():
    most_probable_color = max(color_probs, key=lambda c: c[1])[0]
    canvas[y, x] = hex_to_rgb(most_probable_color)

# =====================
# SIMULATION
# =====================
rng = np.random.default_rng()
all_frames = []

print("Running simulation...")

for frame_index in tqdm(range(number_of_frames)):
    is_whiteout = frame_index >= (number_of_frames - whiteout_frame_count)

    for (x, y), color_probs in pixel_probabilities.items():
        change_rate = pixel_change_rate.get((x, y), 0.0)
        probability_of_event = 1 - math.exp(-change_rate * frame_interval)
        if is_whiteout: 
            probability_of_event *= 4
        if rng.random() > probability_of_event: 
            continue

        # start with base probabilities from history
        base_probabilities = {color: prob for color, prob in color_probs}

        # -------- neighbor influence --------
        neighbor_colors = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            neighbor_x, neighbor_y = x + dx, y + dy
            if 0 <= neighbor_x < canvas_size and 0 <= neighbor_y < canvas_size:
                neighbor_colors.append(rgb_to_hex(canvas[neighbor_y, neighbor_x]))
        if neighbor_colors:
            counts = Counter(neighbor_colors)
            for color, count in counts.items():
                base_probabilities[color] = base_probabilities.get(color, 0) + neighbor_influence * count / max_neighbors_considered

        # -------- inertia (keep current color) --------
        current_color = rgb_to_hex(canvas[y, x])
        base_probabilities[current_color] = base_probabilities.get(current_color, 0) + inertia_strength

        # -------- normalize probabilities --------
        colors_list = list(base_probabilities.keys())
        probs_array = np.array(list(base_probabilities.values()))
        probs_array /= probs_array.sum()

        # pick new color
        chosen_color = rng.choice(colors_list, p=probs_array)
        canvas[y, x] = hex_to_rgb(chosen_color)

    all_frames.append(canvas.copy())

# =====================
# SAVE GIF
# =====================
print("Saving GIF...")
imageio.mimsave(output_gif, all_frames, duration=0.12)
print("Done! Saved as:", output_gif)
