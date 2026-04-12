"""Entry point for the GridWorld Dual Search Visualizer.

References (APA)
Python Software Foundation. (2025). *argparse — Parser for command-line options,
    arguments and sub-commands*. Python 3.12 Documentation.
    https://docs.python.org/3/library/argparse.html

Python Software Foundation. (2025). *pathlib — Object-oriented filesystem paths*.
    Python 3.12 Documentation. https://docs.python.org/3/library/pathlib.html
"""

from __future__ import annotations

import argparse
from pathlib import Path

from env.gridworld import GridWorld
from utils.registry import ALGOS, discover_maps
from visualization.pygame_viz import run_launcher, run_trace_viewer

# Project paths (relative to this file)
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
CONFIGS_DIR = PROJECT_ROOT / "configs"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"


def run_once(map_path: Path, algo_name: str):
    """Run one algorithm on one map → (env, result, trace)."""
    env = GridWorld.from_file(map_path)
    trace: list[tuple[int, int]] = []  # populated during search for replay

    kwargs = dict(
        start=env.start,
        is_goal=env.is_goal,
        neighbors=env.neighbors4,
        h=env.manhattan,
        trace=trace,
    )

    # BDS needs the explicit goal state
    if algo_name == "bds":
        kwargs["goal"] = env.goal

    result = ALGOS[algo_name](**kwargs)
    return env, result, trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Run search algorithms on GridWorld.")
    parser.add_argument(
        "--mode",
        choices=["launcher", "single"],
        default="launcher",
        help="launcher = swipe UI, single = run one map/algo from args",
    )
    parser.add_argument("--map", default="map01.txt", help="Map filename inside assets/maps/")
    parser.add_argument(
        "--algo",
        choices=list(ALGOS.keys()),
        default="astar",
        help="Search algorithm to run (single mode).",
    )
    parser.add_argument("--cell", type=int, default=38, help="Cell size for Pygame viewer.")
    parser.add_argument("--fps", type=int, default=15, help="Start FPS for Pygame viewer.")
    args = parser.parse_args()

    ANALYSIS_DIR.mkdir(exist_ok=True)

    # --- LAUNCHER MODE ---
    if args.mode == "launcher":
        maps = discover_maps(ASSETS_DIR / "maps")
        algos = list(ALGOS.keys())

        if not maps:
            raise FileNotFoundError(f"No map files found in: {ASSETS_DIR / 'maps'}")

        run_launcher(
            maps=maps,
            algos=algos,
            run_once=run_once,
            cell_size=args.cell,
            start_fps=args.fps,
            analysis_dir=ANALYSIS_DIR,
        )
        return

    # --- SINGLE MODE ---
    map_path = ASSETS_DIR / "maps" / args.map
    if not map_path.exists():
        raise FileNotFoundError(f"Map file not found: {map_path}")

    env, result, trace = run_once(map_path, args.algo)

    print(
        f"\n{args.algo.upper()} => found={result.found} cost={result.cost} "
        f"expanded={result.expanded} "
        f"maximum_nodes_waiting_to_be_explored={result.maximum_nodes_waiting_to_be_explored}"
    )

    if result.found:
        print(f"path_len={len(result.path)}")
        print(env.render_with_path(result.path))
    else:
        print("No path found.")

    # Live Pygame replay
    run_trace_viewer(
        grid=env.grid,
        trace=trace,
        path=result.path if result.found else None,
        cell_size=args.cell,
        start_fps=args.fps,
    )


if __name__ == "__main__":
    main()
