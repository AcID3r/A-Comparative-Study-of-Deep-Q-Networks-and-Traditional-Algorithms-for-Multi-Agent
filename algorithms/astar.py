"""A* using Manhattan distance scaled by minimum traversable-cell cost."""

from heapq import heappop, heappush
from time import perf_counter
from algorithms.search_result import SearchResult, finish_result
from algorithms.bfs import reconstruct_path
from environments.grid_graph import GridGraph, Position


def astar(graph: GridGraph, start: Position, goal: Position) -> list[Position] | None:
    return astar_result(graph, start, goal).path


def astar_result(graph: GridGraph, start: Position, goal: Position) -> SearchResult:
    started = perf_counter()
    graph.validate_endpoints(start, goal)
    scale = graph.minimum_cost

    def heuristic(pos):
        return scale * (abs(pos[0] - goal[0]) + abs(pos[1] - goal[1]))

    frontier = [(heuristic(start), 0.0, start)]
    distances = {start: 0.0}
    parents = {start: None}
    expanded = 0
    while frontier:
        _, distance, current = heappop(frontier)
        if distance != distances[current]:
            continue
        expanded += 1
        if current == goal:
            return finish_result(graph, reconstruct_path(parents, goal), expanded, started)
        for neighbor in graph.neighbors(current):
            candidate = distance + graph.cost(neighbor)
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                parents[neighbor] = current
                heappush(frontier, (candidate + heuristic(neighbor), candidate, neighbor))
    return finish_result(graph, None, expanded, started)
