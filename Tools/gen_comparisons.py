"""This does the pit search of the algorithms against each other and drops the scorecards into analysis/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_once, ASSETS_DIR, ANALYSIS_DIR
from visualization.gridworld_viz import save_comparison_jpg

ANALYSIS_DIR.mkdir(exist_ok=True)

# The Versus matchups we want to run, in the format (algo1, algo2, map_file)

COMPARISONS = [
    ("astar", "bfs",   "A-Star.txt"),
    ("dfs",   "bfs",   "BFS_Alternate.txt"),
    ("ucs",   "astar", "UCS_Weighted.txt"),
    ("dls",   "dfs",   "DLS.txt"),
    ("bds",   "bfs",   "BDS.txt"),
]

print("Letting the algorithms loose...\n")

for algo1, algo2, map_file in COMPARISONS:
    map_path = ASSETS_DIR / "maps" / map_file

    # Run both algorithms on the same map and collect their results
    _, algo1_res, _ = run_once(map_path, algo1)
    _, algo2_res, _ = run_once(map_path, algo2)

    # Build the output filename and save the comparison chart
    stem = map_file.replace(".txt", "")
    fname = f"{algo1}_vs_{algo2}__{stem}.jpg"
    out_path = ANALYSIS_DIR / fname
    save_comparison_jpg(algo1, algo1_res, algo2, algo2_res, map_file, out_path)

    # Print a quick recap of each matchup
    print(f"  {algo1} vs {algo2} on {map_file}")
    print(f"    {algo1}: found={algo1_res.found} cost={algo1_res.cost} expanded={algo1_res.expanded} frontier={algo1_res.maximum_nodes_waiting_to_be_explored} path_len={len(algo1_res.path)}")
    print(f"    {algo2}: found={algo2_res.found} cost={algo2_res.cost} expanded={algo2_res.expanded} frontier={algo2_res.maximum_nodes_waiting_to_be_explored} path_len={len(algo2_res.path)}")
    print(f"    Saved: {fname}")
    print()

print("All matchups done, charts are in analysis/!")
