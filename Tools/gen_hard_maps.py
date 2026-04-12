"""Generate harder maze maps for all algorithms."""

import random
import sys
from pathlib import Path

MAPS_DIR = Path(__file__).resolve().parents[1] / "assets" / "maps"


def generate_maze(rows=18, cols=18, seed=42):
    """Generate a perfect maze using iterative backtracking on odd-indexed cells."""
    random.seed(seed)
    grid = [['O'] * cols for _ in range(rows)]

    stack = [(1, 1)]
    visited = {(1, 1)}
    grid[1][1] = 'F'

    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and (nr, nc) not in visited:
                neighbors.append((nr, nc, r + dr // 2, c + dc // 2))
        if neighbors:
            nr, nc, wr, wc = random.choice(neighbors)
            visited.add((nr, nc))
            grid[wr][wc] = 'F'
            grid[nr][nc] = 'F'
            stack.append((nr, nc))
        else:
            stack.pop()

    return grid


def add_extra_paths(grid, count=8, seed=100):
    """Break some walls to create loops (multiple paths)."""
    random.seed(seed)
    rows, cols = len(grid), len(grid[0])
    cells = [(r, c) for r in range(2, rows - 2) for c in range(2, cols - 2) if grid[r][c] == 'O']
    random.shuffle(cells)
    added = 0
    for r, c in cells:
        if added >= count:
            break
        adj = sum(1 for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
                  if 0 <= r + dr < rows and 0 <= c + dc < cols and grid[r + dr][c + dc] != 'O')
        if adj >= 2:
            grid[r][c] = 'F'
            added += 1


def add_weighted_terrain(grid, mud_pct=0.20, water_pct=0.12, seed=300):
    """Replace some floor tiles with M (mud, cost=5) and W (water, cost=10)."""
    random.seed(seed)
    rows, cols = len(grid), len(grid[0])
    floors = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 'F']
    random.shuffle(floors)
    n_mud = int(len(floors) * mud_pct)
    n_water = int(len(floors) * water_pct)
    for r, c in floors[:n_mud]:
        grid[r][c] = 'M'
    for r, c in floors[n_mud:n_mud + n_water]:
        grid[r][c] = 'W'


def clear_endpoint(grid, pos):
    """Ensure the endpoint and at least one neighbor are passable."""
    r, c = pos
    rows, cols = len(grid), len(grid[0])
    grid[r][c] = 'F'
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and grid[nr][nc] == 'O':
            grid[nr][nc] = 'F'


def save_map(grid, name):
    path = MAPS_DIR / name
    text = '\n'.join(''.join(row) for row in grid) + '\n'
    path.write_text(text, encoding='utf-8')
    print(f"  Saved {name}: {len(grid)} rows x {len(grid[0])} cols")


def validate_path(grid, start, goal):
    """BFS to verify a path exists from start to goal."""
    from collections import deque
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    visited = {start}
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            return True
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited and grid[nr][nc] != 'O':
                visited.add((nr, nc))
                q.append((nr, nc))
    return False


def main():
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating harder maps...\n")

    # ── 1. A-Star.txt ─────────────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=1001)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=6, seed=1001)
    assert validate_path(grid, (1, 1), (16, 16)), "A-Star.txt: no path!"
    save_map(grid, 'A-Star.txt')

    # ── 2. BFS.txt ────────────────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=2002)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=18, seed=2002)
    assert validate_path(grid, (1, 1), (16, 16)), "BFS.txt: no path!"
    save_map(grid, 'BFS.txt')

    # ── 3. BFS_Alternate.txt ──────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=3003)
    clear_endpoint(grid, (16, 16))
    clear_endpoint(grid, (1, 1))
    grid[16][16] = 'S'
    grid[1][1] = 'G'
    add_extra_paths(grid, count=12, seed=3003)
    assert validate_path(grid, (16, 16), (1, 1)), "BFS_Alternate.txt: no path!"
    save_map(grid, 'BFS_Alternate.txt')

    # ── 4. DFS.txt ────────────────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=4004)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=3, seed=4004)
    assert validate_path(grid, (1, 1), (16, 16)), "DFS.txt: no path!"
    save_map(grid, 'DFS.txt')

    # ── 5. DLS.txt ────────────────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=5005)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=4, seed=5005)
    assert validate_path(grid, (1, 1), (16, 16)), "DLS.txt: no path!"
    save_map(grid, 'DLS.txt')

    # ── 6. BDS.txt ────────────────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=6006)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=10, seed=6006)
    assert validate_path(grid, (1, 1), (16, 16)), "BDS.txt: no path!"
    save_map(grid, 'BDS.txt')

    # ── 7. UCS_Weighted.txt ────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=7007)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=14, seed=7007)
    add_weighted_terrain(grid, mud_pct=0.22, water_pct=0.14, seed=7007)
    assert validate_path(grid, (1, 1), (16, 16)), "UCS_Weighted.txt: no path!"
    save_map(grid, 'UCS_Weighted.txt')

    # ── 8. Maze_Challenge.txt ─────────────────────────────────────────────────
    grid = generate_maze(18, 18, seed=8008)
    clear_endpoint(grid, (1, 1))
    clear_endpoint(grid, (16, 16))
    grid[1][1] = 'S'
    grid[16][16] = 'G'
    add_extra_paths(grid, count=2, seed=8008)
    add_weighted_terrain(grid, mud_pct=0.15, water_pct=0.10, seed=8008)
    assert validate_path(grid, (1, 1), (16, 16)), "Maze_Challenge.txt: no path!"
    save_map(grid, 'Maze_Challenge.txt')

    print("\nAll maps generated and validated!")


if __name__ == "__main__":
    main()
