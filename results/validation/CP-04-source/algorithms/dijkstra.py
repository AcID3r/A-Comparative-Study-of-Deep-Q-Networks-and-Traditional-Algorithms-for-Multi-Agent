"""Minimum-cost search with positive destination-cell costs."""

from heapq import heappop, heappush
from time import perf_counter
from algorithms.search_result import SearchResult, finish_result
from algorithms.bfs import reconstruct_path
from environments.grid_graph import GridGraph, Position


def dijkstra(graph: GridGraph, start: Position, goal: Position) -> list[Position] | None:
    return dijkstra_result(graph, start, goal).path


def dijkstra_result(graph: GridGraph, start: Position, goal: Position) -> SearchResult:
    started = perf_counter()
    graph.validate_endpoints(start, goal)
    frontier = [(0.0, start)]
    distances = {start: 0.0}
    parents = {start: None}
    expanded = 0
    while frontier:
        distance, current = heappop(frontier)
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
                heappush(frontier, (candidate, neighbor))
    return finish_result(graph, None, expanded, started)
