import duckdb
import numpy as np
from PIL import Image
from tqdm import tqdm
import imageio
from collections import Counter

# =====================
# SETTINGS / CONFIG
# =====================
parquet_file_path = "2022_place_cleaned.parquet"
output_gif_file = "territorial_prediction.gif"

canvas_width = 2000
canvas_height = 2000
total_frames = 80

inertia_amount = 0.6
neighbor_influence_strength = 0.45
stability_increase_rate = 0.02
stability_decrease_rate = 0.01

# =====================
# COLOR HELPERS
# =====================
def hex_to_rgb(hex_string):
    """convert color hex like '#FF00FF' to (255,0,255)"""
    hex_string = hex_string.lstrip("#")
    return tuple(int(hex_string[i:i+2],16) for i in (0,2,4))

def rgb_to_hex(rgb_tuple):
    """convert (255,0,255) to hex string"""
    return "#{:02X}{:02X}{:02X}".format(*rgb_tuple)

# =====================
# BORDER CHECK FUNCTION
# =====================
def check_if_pixel_is_border(x, y, canvas_array):
    """returns True if any neighbor pixel is different color"""
    pixel_color = canvas_array[y, x]
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        neighbor_x, neighbor_y = x + dx, y + dy
        if 0 <= neighbor_x < canvas_width and 0 <= neighbor_y < canvas_height:
            if not np.array_equal(canvas_array[neighbor_y, neighbor_x], pixel_color):
                return True
    return False

# =====================
# LOAD DATA
# =====================
conn = duckdb.connect()
print("Reading cleaned parquet file...")

# Step 1: count how many times each color appears at each pixel
conn.execute(f"""
CREATE TEMP TABLE pixel_color_counts AS
SELECT x, y, color, COUNT(*) AS color_count
FROM read_parquet('{parquet_file_path}')
GROUP BY x, y, color
""")

# Step 2: choose the most common color per pixel as the initial map
conn.execute("""
CREATE TEMP TABLE pixel_initial_map AS
SELECT x, y, color
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY x, y ORDER BY color_count DESC) AS row_num
    FROM pixel_color_counts
)
WHERE row_num = 1
""")

map_rows = conn.execute("SELECT x, y, color FROM pixel_initial_map").fetchall()
conn.close()
print("Loaded initial canvas state from parquet.")

# =====================
# INITIALIZE CANVAS AND STABILITY
# =====================
canvas_array = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)
stability_array = np.zeros((canvas_height, canvas_width), dtype=np.float32)

for x, y, color in map_rows:
    canvas_array[y, x] = hex_to_rgb(color)

# =====================
# SIMULATION LOOP
# =====================
frames_list = []
print("Starting territorial dynamics simulation...")

for frame_idx in tqdm(range(total_frames)):
    new_canvas_array = canvas_array.copy()

    for x, y, _ in map_rows:

        # interior pixels gain stability and resist changes
        if not check_if_pixel_is_border(x, y, canvas_array):
            stability_array[y, x] = min(1.0, stability_array[y, x] + stability_increase_rate)
            continue

        # check neighbor colors
        neighbor_colors_list = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < canvas_width and 0 <= ny < canvas_height:
                neighbor_colors_list.append(rgb_to_hex(canvas_array[ny, nx]))

        color_counts = Counter(neighbor_colors_list)
        invading_color, invading_strength = color_counts.most_common(1)[0]

        current_color = rgb_to_hex(canvas_array[y, x])
        invasion_pressure = invading_strength * neighbor_influence_strength
        resistance_power = inertia_amount + stability_array[y, x]

        if invading_color != current_color and invasion_pressure > resistance_power:
            new_canvas_array[y, x] = hex_to_rgb(invading_color)
            stability_array[y, x] = 0.0
        else:
            stability_array[y, x] = min(1.0, stability_array[y, x] + stability_decrease_rate)

    canvas_array = new_canvas_array
    frames_list.append(canvas_array.copy())

# =====================
# SAVE GIF
# =====================
print("Saving GIF file...")
imageio.mimsave(output_gif_file, [Image.fromarray(f) for f in frames_list], duration=0.12)
print("✅ GIF saved as:", output_gif_file)
