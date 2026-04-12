"""Verify all maps load and all algorithms find a path."""

import sys
from pathlib import Path

# Allow running from the Tools/ directory or project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_once, ASSETS_DIR

maps = [
    "A-Star.txt", "BDS.txt", "BFS.txt", "BFS_Alternate.txt",
    "DFS.txt", "DLS.txt", "UCS_Weighted.txt",
    "Maze_Challenge.txt",
]
algos = ["astar", "bds", "bfs", "dfs", "dls", "ucs"]

for m in maps:
    for a in algos:
        _, r, _ = run_once(ASSETS_DIR / "maps" / m, a)
        tag = "OK" if r.found else "FAIL"
        print(f"  {m:25s} {a:6s} {tag}  cost={r.cost}")

print("\nDone.")
