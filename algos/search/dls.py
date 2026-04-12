"""Depth-Limited Search algorithm implementation.

References (APA)

Russell, S. J., & Norvig, P. (2021). *Artificial Intelligence: A Modern
    Approach* (4th ed.). Pearson.

Python Software Foundation. (2025). *Data structures: Using lists as stacks*.
    Python 3.12 Documentation.
    https://docs.python.org/3/tutorial/datastructures.html#using-lists-as-stacks

Python Software Foundation. (2025). *typing — Support for type hints*. Python 3.12
    Documentation. https://docs.python.org/3/library/typing.html
"""

from __future__ import annotations

from typing import TypeVar, Optional

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def dls(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    depth_limit: int = 175,
    h=None,
    trace: list[State] | None = None,
) -> SearchResult[State]:
    

    """ Depth-Limited Search — DFS that stops at a modifiable(can be changed before running the search) depth. """


    stack: list[tuple[State, int]] = [(start, 0)]
    parent: dict[State, Optional[State]] = {start: None}
    best_depth_seen: dict[State, int] = {start: 0}
    expanded_nodes = 0
    maximum_nodes_waiting_to_be_explored = 1

    while stack:
        maximum_nodes_waiting_to_be_explored = max(maximum_nodes_waiting_to_be_explored, len(stack))
        current, depth = stack.pop()
        expanded_nodes += 1
        if trace is not None:
            trace.append(current)

        if is_goal(current):
            path = reconstruct_path(parent, current)
            return SearchResult(True, path, float(len(path) - 1), expanded_nodes, maximum_nodes_waiting_to_be_explored)

        if depth >= depth_limit:
            continue

        for next, _ in neighbors(current):
            nd = depth + 1
            prev = best_depth_seen.get(next)
            if prev is None or nd < prev:
                best_depth_seen[next] = nd
                parent[next] = current
                stack.append((next, nd))

    return SearchResult(False, [], float("inf"), expanded_nodes, maximum_nodes_waiting_to_be_explored)
