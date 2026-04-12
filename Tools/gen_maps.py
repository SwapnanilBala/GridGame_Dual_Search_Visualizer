"""Generate deterministic 18x18 maze maps with loop openings, rooms, and weighted terrain.

References (APA)
Python Software Foundation. (2025). *random — Generate pseudo-random numbers*.
    Python 3.12 Documentation. https://docs.python.org/3/library/random.html

Python Software Foundation. (2025). *dataclasses — Data Classes*. Python 3.12
    Documentation. https://docs.python.org/3/library/dataclasses.html

Python Software Foundation. (2025). *pathlib — Object-oriented filesystem paths*.
    Python 3.12 Documentation. https://docs.python.org/3/library/pathlib.html
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

MAPS_DIR = Path(__file__).resolve().parents[1] / "assets" / "maps"
ROWS = COLS = 18
LAST_R = ROWS - 2
LAST_C = COLS - 2
INTERIOR_CELLS = (ROWS - 2) * (COLS - 2)
DIRS4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIRS2 = [(-2, 0), (2, 0), (0, -2), (0, 2)]


@dataclass(frozen=True, slots=True)
class MapConfig:
    name: str
    seed: int
    start: tuple[int, int]
    goal: tuple[int, int]
    loop_density: float
    room_attempts: int = 0
    weighted_tiles: dict[str, float] | None = None


def in_bounds(r: int, c: int) -> bool:
    return 1 <= r < ROWS - 1 and 1 <= c < COLS - 1


def carve_base_maze() -> list[list[str]]:
    grid = [["O"] * COLS for _ in range(ROWS)]
    start = (1, 1)
    grid[start[0]][start[1]] = "F"
    stack = [start]
    visited = {start}

    while stack:
        r, c = stack[-1]
        candidates = []
        for dr, dc in DIRS2:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and (nr, nc) not in visited:
                candidates.append((nr, nc, r + dr // 2, c + dc // 2))

        if not candidates:
            stack.pop()
            continue

        nr, nc, wr, wc = random.choice(candidates)
        grid[wr][wc] = "F"
        grid[nr][nc] = "F"
        visited.add((nr, nc))
        stack.append((nr, nc))

    return grid


def carve_rooms(grid: list[list[str]], attempts: int) -> None:
    for _ in range(attempts):
        height = random.choice((3, 5))
        width = random.choice((3, 5))
        top = random.randrange(1, ROWS - height, 2)
        left = random.randrange(1, COLS - width, 2)
        for r in range(top, top + height):
            for c in range(left, left + width):
                grid[r][c] = "F"


def open_loops(grid: list[list[str]], density: float) -> None:
    openings = max(1, round(INTERIOR_CELLS * density))
    for _ in range(openings):
        r = random.randint(1, ROWS - 2)
        c = random.randint(1, COLS - 2)
        if grid[r][c] != "O":
            continue
        neighbors = sum(
            1
            for dr, dc in DIRS4
            if 0 <= r + dr < ROWS and 0 <= c + dc < COLS and grid[r + dr][c + dc] != "O"
        )
        if neighbors >= 2:
            grid[r][c] = "F"


def protected_cells(*points: tuple[int, int]) -> set[tuple[int, int]]:
    blocked: set[tuple[int, int]] = set()
    for r, c in points:
        for dr, dc in [(0, 0), *DIRS4]:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc):
                blocked.add((nr, nc))
    return blocked


def clear_endpoint(grid: list[list[str]], pos: tuple[int, int]) -> None:
    r, c = pos
    grid[r][c] = "F"
    for dr, dc in DIRS4:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and grid[nr][nc] == "O":
            grid[nr][nc] = "F"


def place_weighted_tiles(
    grid: list[list[str]],
    weighted_tiles: dict[str, float],
    blocked: set[tuple[int, int]],
) -> None:
    base_floors = [
        (r, c)
        for r in range(1, ROWS - 1)
        for c in range(1, COLS - 1)
        if grid[r][c] == "F" and (r, c) not in blocked
    ]
    if not base_floors:
        return

    total = len(base_floors)
    for tile, ratio in weighted_tiles.items():
        target = min(len(base_floors), max(1, round(total * ratio)))
        frontier: list[tuple[int, int]] = []
        placed = 0

        while placed < target:
            available = {
                (r, c)
                for r, c in base_floors
                if grid[r][c] == "F" and (r, c) not in blocked
            }
            if not available:
                break

            if not frontier:
                frontier.append(random.choice(tuple(available)))

            r, c = frontier.pop(random.randrange(len(frontier)))
            if (r, c) not in available:
                continue

            grid[r][c] = tile
            placed += 1

            neighbors = [(r + dr, c + dc) for dr, dc in DIRS4 if (r + dr, c + dc) in available]
            random.shuffle(neighbors)
            frontier.extend(neighbors[:3])


def build_map(config: MapConfig) -> list[str]:
    random.seed(config.seed)
    grid = carve_base_maze()
    carve_rooms(grid, config.room_attempts)
    open_loops(grid, config.loop_density)
    clear_endpoint(grid, config.start)
    clear_endpoint(grid, config.goal)

    if config.weighted_tiles:
        place_weighted_tiles(grid, config.weighted_tiles, protected_cells(config.start, config.goal))
        clear_endpoint(grid, config.start)
        clear_endpoint(grid, config.goal)

    grid[config.start[0]][config.start[1]] = "S"
    grid[config.goal[0]][config.goal[1]] = "G"
    return ["".join(row) for row in grid]


CONFIGS = [
    MapConfig("A-Star.txt", 100, (1, 1), (LAST_R, LAST_C), loop_density=0.16, room_attempts=3),
    MapConfig("BDS.txt", 200, (1, 1), (1, LAST_C), loop_density=0.18, room_attempts=3),
    MapConfig("BFS.txt", 300, (1, 1), (LAST_R, LAST_C), loop_density=0.12, room_attempts=2),
    MapConfig("BFS_Alternate.txt", 400, (1, LAST_C), (LAST_R, 1), loop_density=0.2, room_attempts=4),
    MapConfig("DFS.txt", 450, (1, 1), (LAST_R, LAST_C), loop_density=0.05),
    MapConfig("DLS.txt", 500, (1, 1), (LAST_R, LAST_C), loop_density=0.08, room_attempts=1),
    MapConfig("UCS.txt", 600, (1, 1), (LAST_R, LAST_C), loop_density=0.14, room_attempts=2),
    MapConfig(
        "UCS_Weighted.txt",
        700,
        (1, 1),
        (LAST_R, LAST_C),
        loop_density=0.14,
        room_attempts=2,
        weighted_tiles={"W": 0.1, "M": 0.08},
    ),
    MapConfig(
        "UCS_Weighted_02.txt",
        800,
        (1, 1),
        (LAST_R, LAST_C),
        loop_density=0.16,
        room_attempts=3,
        weighted_tiles={"W": 0.05, "M": 0.1, "R": 0.08},
    ),
    MapConfig(
        "Maze_Challenge.txt",
        900,
        (1, 1),
        (LAST_R, LAST_C),
        loop_density=0.07,
        room_attempts=1,
        weighted_tiles={"W": 0.07, "M": 0.12},
    ),
]


def validate(lines: list[str], config: MapConfig) -> None:
    widths = {len(line) for line in lines}
    assert widths == {COLS}, f"{config.name} not rectangular: {sorted(widths)}"
    assert len(lines) == ROWS, f"{config.name} wrong row count: {len(lines)}"
    assert lines[config.start[0]][config.start[1]] == "S", f"{config.name} missing S"
    assert lines[config.goal[0]][config.goal[1]] == "G", f"{config.name} missing G"


def main() -> None:
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    for config in CONFIGS:
        lines = build_map(config)
        validate(lines, config)
        path = MAPS_DIR / config.name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"  {config.name}: {len(lines)}x{len(lines[0])} OK")

    print(f"\nAll {len(CONFIGS)} maps generated as {ROWS}x{COLS}.")


if __name__ == "__main__":
    main()
