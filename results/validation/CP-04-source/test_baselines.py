"""Run from the repository root: python -m unittest discover -v."""

import random
import unittest
from algorithms.astar import astar
from algorithms.bfs import bfs
from algorithms.dijkstra import dijkstra
from environments.grid_graph import GridGraph

METHODS = (bfs, dijkstra, astar)


def reference_cost(graph, start, goal):
    """Independent Bellman-Ford oracle; deliberately does not use a heap."""
    cells = [(r, c) for r in range(graph.rows) for c in range(graph.cols)
             if graph.is_free((r, c))]
    distances = {pos: float("inf") for pos in cells}
    distances[start] = 0.0
    for _ in range(len(cells) - 1):
        changed = False
        for cell in cells:
            for neighbor in graph.neighbors(cell):
                candidate = distances[cell] + graph.cost(neighbor)
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    changed = True
        if not changed:
            break
    return distances[goal]


class BaselineTests(unittest.TestCase):
    def assert_valid(self, graph, path, start, goal):
        self.assertIsNotNone(path)
        self.assertEqual(path[0], start)
        self.assertEqual(path[-1], goal)
        self.assertEqual(len(path), len(set(path)))
        for r, c in path:
            self.assertTrue(0 <= r < graph.rows and 0 <= c < graph.cols)
            self.assertNotIn((r, c), graph.obstacles)
        for a, b in zip(path, path[1:]):
            self.assertEqual(abs(a[0] - b[0]) + abs(a[1] - b[1]), 1)

    def test_open_grid_known_distance(self):
        graph = GridGraph(5, 5)
        for method in METHODS:
            with self.subTest(method=method.__name__):
                path = method(graph, (0, 0), (4, 4))
                self.assert_valid(graph, path, (0, 0), (4, 4))
                self.assertEqual(len(path) - 1, 8)

    def test_obstacle_detour_known_distance(self):
        graph = GridGraph(3, 5, {(0, 2), (1, 2)})
        for method in METHODS:
            with self.subTest(method=method.__name__):
                path = method(graph, (0, 0), (0, 4))
                self.assert_valid(graph, path, (0, 0), (0, 4))
                self.assertEqual(len(path) - 1, 8)

    def test_unreachable_goal(self):
        graph = GridGraph(3, 3, {(1, 0), (1, 1), (1, 2)})
        for method in METHODS:
            self.assertIsNone(method(graph, (0, 0), (2, 2)))

    def test_start_equals_goal(self):
        for method in METHODS:
            self.assertEqual(method(GridGraph(1, 1), (0, 0), (0, 0)), [(0, 0)])

    def test_invalid_endpoints(self):
        graph = GridGraph(3, 3, {(1, 1)})
        for method in METHODS:
            for start, goal in [((-1, 0), (2, 2)), ((0, 0), (3, 0)),
                                ((1, 1), (2, 2)), ((0, 0), (1, 1))]:
                with self.subTest(method=method.__name__, start=start, goal=goal):
                    with self.assertRaises(ValueError):
                        method(graph, start, goal)

    def test_weighted_detour(self):
        graph = GridGraph(3, 5, cell_costs={(1, c): 10 for c in (1, 2, 3)})
        for method in (dijkstra, astar):
            path = method(graph, (1, 0), (1, 4))
            self.assert_valid(graph, path, (1, 0), (1, 4))
            self.assertEqual(len(path) - 1, 6)
            self.assertEqual(graph.path_cost(path), 6)
        with self.assertRaises(ValueError):
            bfs(graph, (1, 0), (1, 4))

    def test_fractional_costs_preserve_astar_optimality(self):
        graph = GridGraph(2, 3, cell_costs={(1, 0): .1, (1, 1): .1,
                                                       (1, 2): .1, (0, 2): .1})
        for method in (dijkstra, astar):
            path = method(graph, (0, 0), (0, 2))
            self.assert_valid(graph, path, (0, 0), (0, 2))
            self.assertAlmostEqual(graph.path_cost(path), .4)

    def test_non_unit_uniform_costs(self):
        graph = GridGraph(2, 2, cell_costs={(r, c): 2 for r in range(2) for c in range(2)})
        for method in METHODS:
            self.assertEqual(graph.path_cost(method(graph, (0, 0), (1, 1))), 4)

    def test_seeded_uniform_maps_against_oracle(self):
        for seed in range(20):
            rng = random.Random(seed)
            obstacles = {(r, c) for r in range(5) for c in range(5)
                         if (r, c) not in ((0, 0), (4, 4)) and rng.random() < .3}
            graph = GridGraph(5, 5, obstacles)
            expected = reference_cost(graph, (0, 0), (4, 4))
            for method in METHODS:
                with self.subTest(seed=seed, method=method.__name__):
                    path = method(graph, (0, 0), (4, 4))
                    if expected == float("inf"):
                        self.assertIsNone(path)
                    else:
                        self.assert_valid(graph, path, (0, 0), (4, 4))
                        self.assertEqual(len(path) - 1, expected)

    def test_seeded_weighted_maps_against_oracle(self):
        for seed in range(20):
            rng = random.Random(seed)
            obstacles = {(r, c) for r in range(5) for c in range(5)
                         if (r, c) not in ((0, 0), (4, 4)) and rng.random() < .25}
            costs = {(r, c): rng.choice((.1, .5, 1, 3, 10))
                     for r in range(5) for c in range(5) if (r, c) not in obstacles}
            graph = GridGraph(5, 5, obstacles, costs)
            expected = reference_cost(graph, (0, 0), (4, 4))
            for method in (dijkstra, astar):
                with self.subTest(seed=seed, method=method.__name__):
                    path = method(graph, (0, 0), (4, 4))
                    if expected == float("inf"):
                        self.assertIsNone(path)
                    else:
                        self.assert_valid(graph, path, (0, 0), (4, 4))
                        self.assertAlmostEqual(graph.path_cost(path), expected)


class GridTests(unittest.TestCase):
    def test_invalid_dimensions(self):
        for rows, cols in [(0, 2), (2, -1), (2.5, 2), (True, 2)]:
            with self.assertRaises(ValueError):
                GridGraph(rows, cols)

    def test_invalid_obstacles_and_costs(self):
        with self.assertRaises(ValueError):
            GridGraph(2, 2, {(2, 0)})
        with self.assertRaises(ValueError):
            GridGraph(2, 2, {(1, 1)}, {(1, 1): 2})
        with self.assertRaises(ValueError):
            GridGraph(2, 2, cell_costs={(3, 3): 1})
        for value in (0, -1, float("nan"), float("inf"), "heavy", True):
            with self.assertRaises(ValueError):
                GridGraph(2, 2, cell_costs={(0, 0): value})

    def test_neighbors_are_deterministic_and_orthogonal(self):
        graph = GridGraph(3, 3, {(0, 1)})
        self.assertEqual(graph.neighbors((1, 1)), ((2, 1), (1, 0), (1, 2)))
        self.assertEqual(graph.neighbors((0, 0)), ((1, 0),))
        with self.assertRaises(ValueError):
            graph.neighbors((0, 1))

    def test_input_data_is_copied(self):
        obstacles, costs = {(1, 1)}, {(0, 1): 2}
        graph = GridGraph(2, 2, obstacles, costs)
        obstacles.clear()
        costs[(0, 1)] = 99
        self.assertFalse(graph.is_free((1, 1)))
        self.assertEqual(graph.cost((0, 1)), 2)
        with self.assertRaises(TypeError):
            graph.cell_costs[(0, 1)] = 5

    def test_path_cost_contract(self):
        graph = GridGraph(2, 2, cell_costs={(0, 0): 9, (0, 1): 2})
        self.assertEqual(graph.path_cost([(0, 0)]), 0)
        self.assertEqual(graph.path_cost([(0, 0), (0, 1)]), 2)
        for path in ([], [(0, 0), (1, 1)], [(3, 3)]):
            with self.assertRaises(ValueError):
                graph.path_cost(path)


if __name__ == "__main__":
    unittest.main()
