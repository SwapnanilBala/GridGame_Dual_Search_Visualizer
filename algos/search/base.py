"""Shared base types and utilities for search algorithms.

References (APA)
Python Software Foundation. (2025). *dataclasses — Data Classes*. Python 3.12
    Documentation. https://docs.python.org/3/library/dataclasses.html

Python Software Foundation. (2025). *typing — Support for type hints*. Python 3.12
    Documentation. https://docs.python.org/3/library/typing.html
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Iterable, Optional, TypeVar

State = TypeVar("State")

NeighborsFn = Callable[[State], Iterable[tuple[State, float]]]
GoalTestFn = Callable[[State], bool]
HeuristicFn = Callable[[State], float]


@dataclass(slots=True)
class SearchResult(Generic[State]):
    found: bool
    path: list[State]
    cost: float
    expanded: int
    maximum_nodes_waiting_to_be_explored: int


def reconstruct_path(parent: dict[State, Optional[State]], end: State) -> list[State]:
    path: list[State] = []
    current: Optional[State] = end
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    return path
