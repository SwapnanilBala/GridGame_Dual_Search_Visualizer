"""Breadth-First Search algorithm implementation.

References (APA)

Russell, S. J., & Norvig, P. (2021). *Artificial Intelligence: A Modern
    Approach* (4th ed.). Pearson.

Python Software Foundation. (2025). *collections — Container datatypes:
    collections.deque*. Python 3.12 Documentation.
    https://docs.python.org/3/library/collections.html#collections.deque

Python Software Foundation. (2025). *typing — Support for type hints*. Python 3.12
    Documentation. https://docs.python.org/3/library/typing.html
"""

from __future__ import annotations

from collections import deque
from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bfs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,
    trace: list[State] | None = None,
) -> SearchResult[State]:
    
    
    """  Breadth-First Search — optimal when all step costs are equal."""


    q = deque([start])
    parent: dict[State, Optional[State]] = {start: None}
    expanded_nodes = 0
    maximum_nodes_waiting_to_be_explored = 1

    while q:
        maximum_nodes_waiting_to_be_explored = max(maximum_nodes_waiting_to_be_explored, len(q))
        current = q.popleft()
        expanded_nodes += 1
        if trace is not None:
            trace.append(current)

        if is_goal(current):
            path = reconstruct_path(parent, current)
            return SearchResult(True, path, float(len(path) - 1), expanded_nodes, maximum_nodes_waiting_to_be_explored)

        for nxt, _ in neighbors(current):
            if nxt not in parent:
                parent[nxt] = current
                q.append(nxt)

    return SearchResult(False, [], float("inf"), expanded_nodes, maximum_nodes_waiting_to_be_explored)
