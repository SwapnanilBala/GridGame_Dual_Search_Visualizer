"""Bidirectional BFS algorithm implementation.

References (APA)

Pohl, I. (1971). Bi-directional Search. *Machine Intelligence*, 6, 127-140.

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
from typing import Optional, TypeVar

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


def bds(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    goal: State | None = None,
    h=None,
    trace: list[State] | None = None,
) -> SearchResult[State]:
    

    """  Bidirectional BFS — searches from start and goal simultaneously.  """


    if goal is None:
        raise ValueError("bds requires goal=... (explicit goal state).")
    if start == goal:
        return SearchResult(True, [start], 0.0, 1, 1)

    q_f = deque([start])
    q_b = deque([goal])
    parent_f: dict[State, Optional[State]] = {start: None}
    parent_b: dict[State, Optional[State]] = {goal: None}
    expanded_nodes = 0
    maximum_nodes_waiting_to_be_explored = 2

    def expand(q, parent_this, parent_other) -> Optional[State]:
        nonlocal expanded_nodes
        current = q.popleft()
        expanded_nodes += 1
        if trace is not None:
            trace.append(current)
        for next, _ in neighbors(current):
            if next in parent_this:
                continue
            parent_this[next] = current
            if next in parent_other:  # searches met!
                return next
            q.append(next)
        return None

    def _stitch(meet):


        """  Combining the forward + backward paths through the meeting point.  """


        path_f = reconstruct_path(parent_f, meet)
        path_b = reconstruct_path(parent_b, meet)
        path_b.reverse()
        return path_f + path_b[1:]

    while q_f and q_b:
        maximum_nodes_waiting_to_be_explored = max(maximum_nodes_waiting_to_be_explored, len(q_f) + len(q_b))

        meet = expand(q_f, parent_f, parent_b)
        if meet is not None:
            full = _stitch(meet)
            return SearchResult(True, full, float(len(full) - 1), expanded_nodes, maximum_nodes_waiting_to_be_explored)

        meet = expand(q_b, parent_b, parent_f)
        if meet is not None:
            full = _stitch(meet)
            return SearchResult(True, full, float(len(full) - 1), expanded_nodes, maximum_nodes_waiting_to_be_explored)

    return SearchResult(False, [], float("inf"), expanded_nodes, maximum_nodes_waiting_to_be_explored)
