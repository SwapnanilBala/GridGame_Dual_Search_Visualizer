"""Uniform-Cost Search (Dijkstra) algorithm implementation.

References (APA)

Dijkstra, E. W. (1959). A Note on Two Problems in Connexion with Graphs.
    *Numerische Mathematik*, 1, 269-271.

Russell, S. J., & Norvig, P. (2021). *Artificial Intelligence: A Modern
    Approach* (4th ed.). Pearson.

Python Software Foundation. (2025). *heapq — Heap queue algorithm*. Python 3.12
    Documentation. https://docs.python.org/3/library/heapq.html

Python Software Foundation. (2025). *dataclasses — Data Classes*. Python 3.12
    Documentation. https://docs.python.org/3/library/dataclasses.html

Python Software Foundation. (2025). *typing — Support for type hints*. Python 3.12
    Documentation. https://docs.python.org/3/library/typing.html
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar

from .base import NeighborsFn, GoalTestFn, SearchResult, reconstruct_path

State = TypeVar("State")


@dataclass(order=True, slots=True)
class _PQItem:
    g: float
    tie: int
    state: Any = field(compare=False)


def ucs(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h=None,
    trace: list[State] | None = None,
) -> SearchResult[State]:
    
    
    """ Uniform Cost Search Algorithm — Optimal for non-negative step costs. """


    heap: list[_PQItem] = []
    tie = 0
    heapq.heappush(heap, _PQItem(0.0, tie, start))
    g_cost: dict[State, float] = {start: 0.0}
    parent: dict[State, Optional[State]] = {start: None}
    expanded_nodes = 0
    maximum_nodes_waiting_to_be_explored = 1

    while heap:
        maximum_nodes_waiting_to_be_explored = max(maximum_nodes_waiting_to_be_explored, len(heap))
        item = heapq.heappop(heap)
        current, current_g = item.state, item.g

        # Skip stale entries
        if current_g != g_cost.get(current, float("inf")):
            continue

        expanded_nodes += 1
        if trace is not None:
            trace.append(current)

        if is_goal(current):
            path = reconstruct_path(parent, current)
            return SearchResult(True, path, g_cost[current], expanded_nodes, maximum_nodes_waiting_to_be_explored)

        for next, step in neighbors(current):
            if step < 0:
                raise ValueError("UCS requires non-negative step costs.")
            new_g = current_g + step
            if next not in g_cost or new_g < g_cost[next]:
                g_cost[next] = new_g
                parent[next] = current
                tie += 1
                heapq.heappush(heap, _PQItem(new_g, tie, next))

    return SearchResult(False, [], float("inf"), expanded_nodes, maximum_nodes_waiting_to_be_explored)
