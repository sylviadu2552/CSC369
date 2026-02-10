import duckdb
import numpy as np
from PIL import Image
from tqdm import tqdm
import imageio

# =====================
# SETTINGS / CONFIG
# =====================
# file paths
parquet_file = "2022_place_cleaned.parquet"
spatial_gif_file = "spatial.gif"
freq_gif_file = "frequency.gif"
final_canvas_file = "final_canvas.png"

# canvas size and number of GIF frames
canvas_size = 2000
num_frames = 30

# how much to exaggerate changes so we can see movement
spatial_scale = 4.0
freq_scale = 10.0
final_phase_scale = 0.05

# whiteout start time (timestamp)
whiteout_start = 1648785600 + 82*3600 + 4*60  # 82 hours + 4 minutes

# =====================
# HELPER FUNCTIONS
# =====================
def hex_to_rgb(hex_color):
    """turn hex color string like '#FF00FF' into an (R,G,B) tuple"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# =====================
# LOAD DATA
# =====================
print("Loading pixels before the whiteout...")
conn = duckdb.connect()
pixels = conn.execute(f"""
    SELECT x, y, color
    FROM read_parquet('{parquet_file}')
    WHERE t < {whiteout_start}
""").fetchall()
conn.close()

if len(pixels) == 0:
    raise ValueError("No pixels loaded! Check your whiteout_start timestamp or units.")

# =====================
# INITIAL CANVAS
# =====================
print("Building initial canvas...")
# start fully white
canvas = np.ones((canvas_size, canvas_size, 3), dtype=np.float32)

# fill in all pixels from the data
for x, y, c in pixels:
    canvas[y, x] = np.array(hex_to_rgb(c)) / 255.0  # normalize RGB to 0-1

# crop to active area so we don't waste computation
ys, xs = np.where(np.any(canvas != 1.0, axis=2))
ymin, ymax = ys.min(), ys.max() + 1
xmin, xmax = xs.min(), xs.max() + 1
sub_canvas = canvas[ymin:ymax, xmin:xmax]

# =====================
# FFT SETUP
# =====================
print("Computing FFT for R, G, B channels...")
R = sub_canvas[..., 0]
G = sub_canvas[..., 1]
B = sub_canvas[..., 2]

F_R = np.fft.fft2(R)
F_G = np.fft.fft2(G)
F_B = np.fft.fft2(B)

# keep original FFT for computing differences later
F_R_orig, F_G_orig, F_B_orig = F_R.copy(), F_G.copy(), F_B.copy()

# make frequency grids for scaling phases
h, w = R.shape
fy = np.fft.fftfreq(h)
fx = np.fft.fftfreq(w)
FX, FY = np.meshgrid(fx, fy)
freq_radius = np.sqrt(FX**2 + FY**2)

# save phase info for later updates
phase_R = np.angle(F_R)
phase_G = np.angle(F_G)
phase_B = np.angle(F_B)

# also save original spatial canvas to compute deltas
R_base = np.fft.ifft2(F_R_orig).real
G_base = np.fft.ifft2(F_G_orig).real
B_base = np.fft.ifft2(F_B_orig).real

# =====================
# GENERATE GIF FRAMES
# =====================
print("Generating GIF frames...")
frames_spatial = []
frames_freq = []

for frame_num in tqdm(range(num_frames)):

    # --- randomly change FFT phases a little ---
    for F, phase in zip([F_R, F_G, F_B], [phase_R, phase_G, phase_B]):
        delta_phase = final_phase_scale * (np.random.rand(*phase.shape) - 0.5) * 2 * np.pi
        delta_phase *= freq_radius  # higher frequencies move more
        phase += delta_phase
        F[:] = np.abs(F) * np.exp(1j * phase)

    # --- spatial GIF ---
    R_spatial = np.fft.ifft2(F_R).real
    G_spatial = np.fft.ifft2(F_G).real
    B_spatial = np.fft.ifft2(F_B).real

    delta_spatial = np.stack([
        np.clip((R_spatial - R_base) * spatial_scale + R_base, 0, 1),
        np.clip((G_spatial - G_base) * spatial_scale + G_base, 0, 1),
        np.clip((B_spatial - B_base) * spatial_scale + B_base, 0, 1)
    ], axis=2)

    frame_canvas = canvas.copy()
    frame_canvas[ymin:ymax, xmin:xmax] = delta_spatial
    frames_spatial.append(Image.fromarray((frame_canvas * 255).astype(np.uint8)))

    # --- frequency GIF ---
    R_mag = np.log1p(freq_scale * np.abs(np.fft.fftshift(F_R - F_R_orig)))
    G_mag = np.log1p(freq_scale * np.abs(np.fft.fftshift(F_G - F_G_orig)))
    B_mag = np.log1p(freq_scale * np.abs(np.fft.fftshift(F_B - F_B_orig)))

    vmax = max(R_mag.max(), G_mag.max(), B_mag.max(), 1e-6)
    frame_freq = np.stack([
        (R_mag / vmax * 255).astype(np.uint8),
        (G_mag / vmax * 255).astype(np.uint8),
        (B_mag / vmax * 255).astype(np.uint8)
    ], axis=2)

    frame_freq_canvas = canvas.copy()
    frame_freq_canvas[ymin:ymax, xmin:xmax] = frame_freq / 255.0
    frames_freq.append(Image.fromarray((frame_freq_canvas * 255).astype(np.uint8)))

# =====================
# SAVE GIFS
# =====================
print("Saving GIFs...")
frames_spatial[0].save(spatial_gif_file, save_all=True, append_images=frames_spatial[1:], duration=100, loop=0)
frames_freq[0].save(freq_gif_file, save_all=True, append_images=frames_freq[1:], duration=100, loop=0)
print("✅ Saved spatial GIF:", spatial_gif_file)
print("✅ Saved frequency GIF:", freq_gif_file)

# =====================
# FINAL CANVAS
# =====================
print("Generating final predicted canvas...")
for F, phase in zip([F_R, F_G, F_B], [phase_R, phase_G, phase_B]):
    delta_phase = final_phase_scale * (np.random.rand(*phase.shape) - 0.5) * 2 * np.pi
    delta_phase *= freq_radius
    phase += delta_phase
    F[:] = np.abs(F) * np.exp(1j * phase)

R_final = np.clip(np.fft.ifft2(F_R).real, 0, 1)
G_final = np.clip(np.fft.ifft2(F_G).real, 0, 1)
B_final = np.clip(np.fft.ifft2(F_B).real, 0, 1)

final_sub = np.stack([R_final, G_final, B_final], axis=2)
final_canvas = canvas.copy()
final_canvas[ymin:ymax, xmin:xmax] = final_sub
Image.fromarray((final_canvas * 255).astype(np.uint8)).save(final_canvas_file)
print("✅ Saved final canvas:", final_canvas_file)
