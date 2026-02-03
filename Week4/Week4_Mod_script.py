import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


summary_csv = "whiteout_summary.csv"
output_gif = "moderator_whiteout.gif"
frame_skip = 5   # use every 5th row to reduce memory and speed up animation
fps = 20         # frames per second for GIF

whiteout_df = pd.read_csv(summary_csv)

# Convert epoch seconds to datetime for plotting
whiteout_df['time_dt'] = pd.to_datetime(whiteout_df['time_bin'], unit='s')
whiteout_df = whiteout_df.iloc[::frame_skip, :].reset_index(drop=True)


fig, ax = plt.subplots(figsize=(6, 3))
ax.set_xlim(whiteout_df['time_dt'].min(), whiteout_df['time_dt'].max())
ax.set_ylim(0, whiteout_df['total_pixels'].max() * 1.1)
ax.set_xlabel("Time")
ax.set_ylabel("Pixels on Canvas")
ax.set_title("Moderator Whiteout on r/place 2022")

line, = ax.plot([], [], color='black', linewidth=2)

def update(frame):
    line.set_data(whiteout_df['time_dt'][:frame+1],
                  whiteout_df['total_pixels'][:frame+1])
    return (line,)

animation = FuncAnimation(fig, update, frames=len(whiteout_df), blit=True)

animation.save(output_gif, writer='pillow', fps=fps)

plt.close(fig)
print(f"Moderator whiteout GIF saved as {output_gif}!")
