"""Render completed search visualizations as images for the README."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np

from main import run_once, ASSETS_DIR, ANALYSIS_DIR

ANALYSIS_DIR.mkdir(exist_ok=True)

# Colour mapping for tiles (converted to RGB floats for numpy)
TILE_COLORS = {
    'O': mcolors.to_rgb('darkslategray'),
    'F': mcolors.to_rgb('lavender'),
    'S': mcolors.to_rgb('tomato'),
    'G': mcolors.to_rgb('mediumspringgreen'),
    'R': mcolors.to_rgb('wheat'),
    'M': mcolors.to_rgb('sienna'),
    'W': mcolors.to_rgb('dodgerblue'),
}

EXPLORED_COLOR = 'cornflowerblue'
PATH_COLOR     = 'limegreen'
BG_COLOR       = 'black'


def render_search(ax, grid, trace, path, title, explored_color=EXPLORED_COLOR):
    rows, cols = len(grid), len(grid[0])
    img = np.zeros((rows, cols, 3))

    for r in range(rows):
        for c in range(cols):
            img[r, c] = TILE_COLORS.get(grid[r][c], TILE_COLORS['F'])

    ax.imshow(img, interpolation='nearest')

    # Explored overlay
    explored_set = set(trace)
    for r, c in explored_set:
        if grid[r][c] not in ('O', 'S', 'G'):
            rect = mpatches.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                       color=explored_color, zorder=2)
            ax.add_patch(rect)

    # Path overlay
    if path:
        path_set = set(path)
        for r, c in path_set:
            if grid[r][c] not in ('O', 'S', 'G'):
                rect = mpatches.Rectangle((c - 0.5, r - 0.5), 1, 1,
                                           color=PATH_COLOR, zorder=3)
                ax.add_patch(rect)

        # Draw path line
        py = [r for r, c in path]
        px = [c for r, c in path]
        ax.plot(px, py, color='springgreen', linewidth=2.0, zorder=4, alpha=0.8)

    ax.set_title(title, color='whitesmoke', fontsize=11, fontweight='bold', pad=8)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def render_dual_search(map_file, algo1, algo2, out_name):
    map_path = ASSETS_DIR / "maps" / map_file
    env1, algo1_res, trace1 = run_once(map_path, algo1)
    env2, algo2_res, trace2 = run_once(map_path, algo2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), facecolor=BG_COLOR)
    fig.subplots_adjust(wspace=0.05, top=0.88, bottom=0.05, left=0.02, right=0.98)

    fig.suptitle(f"Completed Search — {map_file}",
                 color='cyan', fontsize=14, fontweight='bold', y=0.95)

    title1 = f"{algo1.upper()}  |  cost={algo1_res.cost:.0f}  expanded={algo1_res.expanded}  path={len(algo1_res.path)}"
    title2 = f"{algo2.upper()}  |  cost={algo2_res.cost:.0f}  expanded={algo2_res.expanded}  path={len(algo2_res.path)}"

    render_search(ax1, env1.grid, trace1, algo1_res.path if algo1_res.found else [], title1,
                  explored_color='cornflowerblue')
    render_search(ax2, env2.grid, trace2, algo2_res.path if algo2_res.found else [], title2,
                  explored_color='sandybrown')

    out_path = ANALYSIS_DIR / out_name
    fig.savefig(out_path, format='jpeg', dpi=150, bbox_inches='tight', facecolor=BG_COLOR)
    plt.close(fig)
    print(f"  Saved: {out_name}")


print("Rendering finished search images...\n")

# Render a couple finished searches to show what it looks like
render_dual_search("A-Star.txt", "astar", "bfs", "finished_astar_vs_bfs__A-Star.jpg")
render_dual_search("BFS_Alternate.txt", "dfs", "bfs", "finished_dfs_vs_bfs__BFS_Alternate.jpg")
render_dual_search("UCS_Weighted.txt", "ucs", "astar", "finished_ucs_vs_astar__UCS_Weighted.jpg")

print("\nDone!")
