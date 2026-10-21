"""Breadth-first search for uniform movement costs."""

from collections import deque
from time import perf_counter
from algorithms.search_result import SearchResult, finish_result
from environments.grid_graph import GridGraph, Position


def reconstruct_path(parents, goal):
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parents[current]
    return path[::-1]


def bfs(graph: GridGraph, start: Position, goal: Position) -> list[Position] | None:
    return bfs_result(graph, start, goal).path


def bfs_result(graph: GridGraph, start: Position, goal: Position) -> SearchResult:
    started = perf_counter()
    graph.validate_endpoints(start, goal)
    if not graph.uniform_costs:
        raise ValueError("BFS requires uniform movement costs")
    queue = deque([start])
    parents = {start: None}
    expanded = 0
    while queue:
        current = queue.popleft()
        expanded += 1
        if current == goal:
            return finish_result(graph, reconstruct_path(parents, goal), expanded, started)
        for neighbor in graph.neighbors(current):
            if neighbor not in parents:
                parents[neighbor] = current
                queue.append(neighbor)
    return finish_result(graph, None, expanded, started)
