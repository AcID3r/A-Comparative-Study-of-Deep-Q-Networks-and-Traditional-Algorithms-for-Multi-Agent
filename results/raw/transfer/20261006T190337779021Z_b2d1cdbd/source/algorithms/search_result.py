"""Common reporting contract; original path-returning APIs remain available."""

from dataclasses import dataclass
from time import perf_counter
from environments.grid_graph import GridGraph, Position


@dataclass(frozen=True)
class SearchResult:
    path: list[Position] | None
    moves: int | None
    path_cost: float | None
    expanded_nodes: int
    planning_time_seconds: float
    failure_reason: str | None

    @property
    def success(self) -> bool:
        return self.path is not None


def finish_result(graph, path, expanded_nodes, started):
    # Stop before reporting-only cost validation, rendering, or file I/O.
    elapsed = perf_counter() - started
    return SearchResult(
        path=path,
        moves=None if path is None else len(path) - 1,
        path_cost=None if path is None else graph.path_cost(path),
        expanded_nodes=expanded_nodes,
        planning_time_seconds=elapsed,
        failure_reason="unreachable" if path is None else None,
    )
