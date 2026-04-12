"""GridWorld environment — 2D grid parsing, neighbor queries, and terrain costs.

References (APA)

Python Software Foundation. (2025). *dataclasses — Data Classes*. Python 3.12
    Documentation. https://docs.python.org/3/library/dataclasses.html

Python Software Foundation. (2025). *pathlib — Object-oriented filesystem paths*.
    Python 3.12 Documentation. https://docs.python.org/3/library/pathlib.html

Python Software Foundation. (2025). *typing — Support for type hints*. Python 3.12
    Documentation. https://docs.python.org/3/library/typing.html
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

State = tuple[int, int]  # (row, col)

# Tile characters
WALL  = "O"
FLOOR = "F"
START = "S"
GOAL  = "G"
ROAD  = "R"
MUD   = "M"
WATER = "W"


@dataclass(slots=True)
class GridWorld:
    
    """  2D grid environment that exposes start, goal, and neighbor queries to search algorithms.  """

    grid: list[list[str]]
    start: State
    goal: State

    @classmethod
    def from_file(cls, path: str | Path) -> "GridWorld":
        """  Load a .txt map file into a GridWorld.  """
        path = Path(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        lines = [ln for ln in lines if ln.strip() != ""]

        grid: list[list[str]] = [list(ln) for ln in lines]
        rows = len(grid)
        cols = len(grid[0]) if rows else 0
        if rows == 0 or cols == 0:
            raise ValueError("Map is empty.")

        # All rows must be the same width
        for r in range(rows):
            if len(grid[r]) != cols:
                bad_line = "".join(grid[r])
                raise ValueError(
                    f"Non-rectangular map at row {r} (line {r + 1}): expected {cols}, got {len(grid[r])}. "
                    f"Row repr: {bad_line!r}"
                )

        start: State | None = None
        goal: State | None = None

        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == START:
                    start = (r, c)
                elif grid[r][c] == GOAL:
                    goal = (r, c)

        if start is None:
            raise ValueError("Map missing 'S' (start).")
        if goal is None:
            raise ValueError("Map missing 'G' (goal).")

        return cls(grid=grid, start=start, goal=goal)

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    def in_bounds(self, s: State) -> bool:
        r, c = s
        return 0 <= r < self.rows and 0 <= c < self.cols

    def passable(self, s: State) -> bool:
        r, c = s
        return self.grid[r][c] != WALL

    def step_cost(self, s: State) -> float:
        """  Terrain-dependent movement cost: R=1, M=5, W=10, everything else=1.  """
        r, c = s
        ch = self.grid[r][c]
        if ch in (FLOOR, START, GOAL, " "):
            return 1.0
        if ch == ROAD:
            return 1.0
        if ch == MUD:
            return 5.0
        if ch == WATER:
            return 10.0
        return 1.0

    def neighbors4(self, s: State) -> Iterable[tuple[State, float]]:
        """  Yield (neighbor, step_cost) for 4-directional movement.  """
        r, c = s
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = (r + dr, c + dc)
            if self.in_bounds(nxt) and self.passable(nxt):
                yield nxt, self.step_cost(nxt)

    def is_goal(self, s: State) -> bool:
        return s == self.goal

    def manhattan(self, s: State) -> float:
        """  Admissible heuristic for A*: Manhattan distance to the goal.  """
        (r1, c1) = s
        (r2, c2) = self.goal
        return float(abs(r1 - r2) + abs(c1 - c2))

    def render_with_path(self, path: list[State]) -> str:
        """  Return ASCII grid with the path marked as dots.  """
        g = [row[:] for row in self.grid]
        for (r, c) in path:
            if g[r][c] in (START, GOAL, WALL):
                continue
            g[r][c] = "•"
        return "\n".join("".join(row) for row in g)
