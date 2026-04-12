"""A* Search algorithm implementation.

References (APA)

Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A Formal Basis for the
    Heuristic Determination of Minimum Cost Paths. *IEEE Transactions on
    Systems Science and Cybernetics*, 4(2), 100-107.

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

from .base import GoalTestFn, HeuristicFn, NeighborsFn, SearchResult, reconstruct_path

State = TypeVar("State")


@dataclass(order=True, slots=True)
class _PQItem:
    f: float          # f = g + h
    g: float
    tie: int
    state: Any = field(compare=False)


def astar(
    start: State,
    is_goal: GoalTestFn[State],
    neighbors: NeighborsFn[State],
    h: HeuristicFn[State],
    trace: list[State] | None = None,
) -> SearchResult[State]:
    """  A* Search — optimal with an admissible heuristic and non-negative costs.  """
    heap: list[_PQItem] = []
    tie = 0
    g_cost: dict[State, float] = {start: 0.0}
    parent: dict[State, Optional[State]] = {start: None}
    heapq.heappush(heap, _PQItem(f=h(start), g=0.0, tie=tie, state=start))
    expanded_nodes = 0
    maximum_nodes_waiting_to_be_explored = 1

    while heap:
        maximum_nodes_waiting_to_be_explored = max(maximum_nodes_waiting_to_be_explored, len(heap))
        item = heapq.heappop(heap)
        current, current_g = item.state, item.g

        # Skips redundant heap entries
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
                raise ValueError("A* requires non-negative step costs.")
            new_g = current_g + step
            if next not in g_cost or new_g < g_cost[next]:
                g_cost[next] = new_g
                parent[next] = current
                tie += 1
                heapq.heappush(heap, _PQItem(f=new_g + h(next), g=new_g, tie=tie, state=next))

    return SearchResult(False, [], float("inf"), expanded_nodes, maximum_nodes_waiting_to_be_explored)
