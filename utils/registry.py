"""Algorithm registry and map discovery utilities.

References (APA)
Python Software Foundation. (2025). *dataclasses — Data Classes*. Python 3.12
    Documentation. https://docs.python.org/3/library/dataclasses.html

Python Software Foundation. (2025). *pathlib — Object-oriented filesystem paths*.
    Python 3.12 Documentation. https://docs.python.org/3/library/pathlib.html

Python Software Foundation. (2025). *typing — Support for type hints*. Python 3.12
    Documentation. https://docs.python.org/3/library/typing.html
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

from algos.search.astar import astar
from algos.search.dfs import dfs
from algos.search.bfs import bfs
from algos.search.ucs import ucs
from algos.search.dls import dls
from algos.search.bds import bds

AlgoFn = Callable[..., Any]

# Name → function registry. Add new algorithms here to auto-register them in the UI.
ALGOS: dict[str, AlgoFn] = {
    "astar": astar,
    "dfs": dfs,
    "bfs": bfs,
    "ucs": ucs,
    "dls": dls,
    "bds": bds,
}


def discover_maps(maps_dir: Path) -> list[Path]:
    """Return sorted list of .txt map files in the given directory."""
    return sorted(maps_dir.glob("*.txt"))


@dataclass
class RunConfig:
    map_path: Path
    algo_name: str