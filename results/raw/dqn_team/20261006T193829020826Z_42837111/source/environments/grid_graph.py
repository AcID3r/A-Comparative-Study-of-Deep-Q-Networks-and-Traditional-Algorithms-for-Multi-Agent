"""Immutable four-direction grid; coordinates are (row, column)."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real
from types import MappingProxyType
from typing import Mapping

Position = tuple[int, int]


@dataclass(frozen=True)
class GridGraph:
    rows: int
    cols: int
    obstacles: frozenset[Position] = frozenset()
    cell_costs: Mapping[Position, float] | None = None

    def __post_init__(self):
        if any(type(n) is not int or n <= 0 for n in (self.rows, self.cols)):
            raise ValueError("Grid dimensions must be positive integers")
        obstacles = frozenset(self.obstacles)
        costs = dict(self.cell_costs or {})
        for pos in obstacles | costs.keys():
            if not self.in_bounds(pos):
                raise ValueError(f"Cell outside grid: {pos}")
        for pos, cost in costs.items():
            if pos in obstacles:
                raise ValueError("Blocked cells cannot have movement costs")
            if isinstance(cost, bool) or not isinstance(cost, Real) or not isfinite(cost) or cost <= 0:
                raise ValueError("Movement costs must be finite and positive")
        object.__setattr__(self, "obstacles", obstacles)
        object.__setattr__(self, "cell_costs", MappingProxyType(costs))

    def in_bounds(self, pos: Position) -> bool:
        return (isinstance(pos, tuple) and len(pos) == 2
                and all(type(x) is int for x in pos)
                and 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols)

    def is_free(self, pos: Position) -> bool:
        return self.in_bounds(pos) and pos not in self.obstacles

    def validate_endpoints(self, start: Position, goal: Position) -> None:
        if not self.is_free(start) or not self.is_free(goal):
            raise ValueError("Start and goal must be free cells inside the grid")

    def neighbors(self, pos: Position) -> tuple[Position, ...]:
        if not self.is_free(pos):
            raise ValueError("Cannot find neighbors of an invalid cell")
        r, c = pos
        return tuple(p for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
                     if self.is_free(p))

    def cost(self, destination: Position) -> float:
        if not self.is_free(destination):
            raise ValueError("Cannot enter an invalid cell")
        return float(self.cell_costs.get(destination, 1.0))

    @property
    def minimum_cost(self) -> float:
        values = list(self.cell_costs.values())
        if len(values) < self.rows * self.cols - len(self.obstacles):
            values.append(1.0)
        return float(min(values, default=1.0))

    @property
    def uniform_costs(self) -> bool:
        values = set(self.cell_costs.values())
        if len(self.cell_costs) < self.rows * self.cols - len(self.obstacles):
            values.add(1.0)
        return len(values) <= 1

    def path_cost(self, path: list[Position]) -> float:
        if not path or not self.is_free(path[0]):
            raise ValueError("Path must contain at least one valid cell")
        for source, destination in zip(path, path[1:]):
            if destination not in self.neighbors(source):
                raise ValueError("Path contains a blocked or non-adjacent move")
        return sum(self.cost(pos) for pos in path[1:])
