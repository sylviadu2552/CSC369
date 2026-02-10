import duckdb
import numpy as np
from PIL import Image
from tqdm import tqdm
import imageio
import math
from collections import Counter

# =====================
# CONFIG
# =====================
PARQUET_FILE = "2022_place_cleaned.parquet"
GIF_OUT = "structured_prediction.gif"

CANVAS_SIZE = 2000
FRAME_INTERVAL = 300
MAX_FRAMES = 90
WHITEOUT_OFFSET_SEC = 82*3600 + 4*60
WHITEOUT_FRAMES = 15

# INFLUENCE PARAMETERS
INERTIA = 0.7          # pixel resists changing from current
NEIGHBOR_WEIGHT = 0.35 # neighbors push pixel toward their color
BLOCK_WEIGHT = 0.25    # block-level majority color influence
MAX_NEIGHBORS = 4
BLOCK_SIZE = 10        # region blocks for structured influence

# =====================
# COLOR UTILS
# =====================
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))

def rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

# =====================
# LOAD DATA FROM DUCKDB
# =====================
con = duckdb.connect()
print("Reading cleaned parquet efficiently...")

# Step 1: compute min/max time
t_min, t_max = con.execute(f"""
SELECT MIN(t), MAX(t)
FROM read_parquet('{PARQUET_FILE}')
""").fetchone()

whiteout_start = t_min + WHITEOUT_OFFSET_SEC

# Step 2: pixel counts per color
con.execute(f"""
CREATE TEMP TABLE pixel_counts AS
SELECT x, y, color, COUNT(*) AS cnt
FROM read_parquet('{PARQUET_FILE}')
WHERE t < {whiteout_start}
GROUP BY x, y, color
""")

# Step 3: MAP color using ROW_NUMBER
con.execute("""
CREATE TEMP TABLE pixel_map AS
SELECT x, y, color
FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY x, y ORDER BY cnt DESC) AS rn
    FROM pixel_counts
)
WHERE rn = 1
""")

# Step 4: get pixel probabilities for entropy
prob_rows = con.execute("""
SELECT x, y, color, cnt
FROM pixel_counts
""").fetchall()

# Step 5: compute pixel Poisson rates (for simulated events)
rate_rows = con.execute(f"""
SELECT x, y,
       COUNT(*) / ({whiteout_start} - MIN(t)) AS rate
FROM read_parquet('{PARQUET_FILE}')
WHERE t < {whiteout_start}
GROUP BY x, y
""").fetchall()

# Step 6: pull MAP colors
map_rows = con.execute("SELECT x, y, color FROM pixel_map").fetchall()
con.close()

print("Data loaded successfully.")

# =====================
# BUILD MAPS AND ENTROPY
# =====================
pixel_probs = {}
pixel_rate = {}
pixel_entropy = {}

# build pixel_probs
for x, y, color, cnt in prob_rows:
    pixel_probs.setdefault((x,y), []).append((color, cnt))

# normalize probs and compute entropy
for k, colors in pixel_probs.items():
    counts = np.array([c for _, c in colors], dtype=float)
    counts /= counts.sum()
    pixel_probs[k] = [(c[0], p) for c, p in zip(colors, counts)]
    pixel_entropy[k] = -np.sum(counts * np.log(counts + 1e-9))

# build pixel_rate dict
for x, y, rate in rate_rows:
    pixel_rate[(x, y)] = rate

# =====================
# INITIAL CANVAS (MAP)
# =====================
canvas = np.full((CANVAS_SIZE, CANVAS_SIZE, 3), 255, dtype=np.uint8)

for x, y, color in map_rows:
    canvas[y, x] = hex_to_rgb(color)

# =====================
# PREP BLOCKS
# =====================
block_map = {}
for by in range(0, CANVAS_SIZE, BLOCK_SIZE):
    for bx in range(0, CANVAS_SIZE, BLOCK_SIZE):
        block_map[(bx, by)] = []

# assign pixels to blocks
for y in range(CANVAS_SIZE):
    for x in range(CANVAS_SIZE):
        bx, by = (x // BLOCK_SIZE)*BLOCK_SIZE, (y // BLOCK_SIZE)*BLOCK_SIZE
        block_map[(bx,by)].append((x,y))

# =====================
# SIMULATION
# =====================
rng = np.random.default_rng()
frames = []

print("Simulating structured evolution...")

for frame in tqdm(range(MAX_FRAMES)):
    is_whiteout = frame >= (MAX_FRAMES - WHITEOUT_FRAMES)

    for (x,y), colors in pixel_probs.items():
        lam = pixel_rate.get((x,y),0)
        p_event = 1 - math.exp(-lam*FRAME_INTERVAL)
        if is_whiteout:
            p_event *= 4
        if rng.random() > p_event:
            continue

        # ----- base probabilities -----
        base = {c:p for c,p in colors}

        # ----- neighbor influence -----
        neighbor_colors = []
        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if 0<=nx<CANVAS_SIZE and 0<=ny<CANVAS_SIZE:
                neighbor_colors.append(rgb_to_hex(canvas[ny,nx]))

        if neighbor_colors:
            counts = Counter(neighbor_colors)
            for c in counts:
                base[c] = base.get(c,0) + NEIGHBOR_WEIGHT*counts[c]/MAX_NEIGHBORS

        # ----- block influence -----
        bx, by = (x//BLOCK_SIZE)*BLOCK_SIZE, (y//BLOCK_SIZE)*BLOCK_SIZE
        block_colors = [rgb_to_hex(canvas[py,px]) for px,py in block_map[(bx,by)]]
        counts = Counter(block_colors)
        for c in counts:
            base[c] = base.get(c,0) + BLOCK_WEIGHT*counts[c]/len(block_colors)

        # ----- inertia/entropy locking -----
        current = rgb_to_hex(canvas[y,x])
        inertia_bonus = INERTIA + (1 - pixel_entropy.get((x,y),0)/np.log(len(colors)+1))
        base[current] = base.get(current,0) + inertia_bonus

        # ----- normalize -----
        cols = list(base.keys())
        probs = np.array(list(base.values()))
        probs /= probs.sum()

        chosen = rng.choice(cols, p=probs)
        canvas[y,x] = hex_to_rgb(chosen)

    frames.append(canvas.copy())

# =====================
# SAVE GIF
# =====================
print("Saving GIF...")
imageio.mimsave(GIF_OUT, frames, duration=0.12)
print("✅ Saved:", GIF_OUT)
