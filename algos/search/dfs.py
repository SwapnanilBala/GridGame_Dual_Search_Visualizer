"""Depth-First Search algorithm implementation.

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

from typing import Optional, TypeVar

from .base import GoalTestFn, NeighborsFn, SearchResult, reconstruct_path

State = TypeVar("State")


def dfs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,
    trace: list[State] | None = None,
) -> SearchResult[State]:
    

    """  Depth-First Search — Take one path as deep as possible before backtracking  """


    stack: list[State] = [start]
    parent: dict[State, Optional[State]] = {start: None}
    visited: set[State] = {start}
    expanded_nodes = 0
    maximum_nodes_waiting_to_be_explored = 1

    while stack:
        maximum_nodes_waiting_to_be_explored = max(maximum_nodes_waiting_to_be_explored, len(stack))
        current = stack.pop()
        expanded_nodes += 1
        if trace is not None:
            trace.append(current)

        if is_goal(current):
            path = reconstruct_path(parent, current)
            return SearchResult(True, path, float(len(path) - 1), expanded_nodes, maximum_nodes_waiting_to_be_explored)

        for next, _ in neighbors(current):
            if next not in visited:
                visited.add(next)
                parent[next] = current
                stack.append(next)

    return SearchResult(False, [], float("inf"), expanded_nodes, maximum_nodes_waiting_to_be_explored)
