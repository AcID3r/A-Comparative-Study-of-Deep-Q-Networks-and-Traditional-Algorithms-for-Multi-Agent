"""Behavior checks for CP-02 search measurements and displays."""

import unittest
from algorithms.bfs import bfs, bfs_result
from algorithms.dijkstra import dijkstra, dijkstra_result
from algorithms.astar import astar, astar_result
from environments.grid_graph import GridGraph


class SearchReportingTests(unittest.TestCase):
    def test_corridor_has_three_processed_nodes_including_goal(self):
        graph = GridGraph(1, 3)
        for search in (bfs_result, dijkstra_result, astar_result):
            with self.subTest(search=search.__name__):
                result = search(graph, (0, 0), (0, 2))
                self.assertEqual(result.expanded_nodes, 3)
                self.assertEqual(result.moves, 2)
                self.assertEqual(result.path_cost, 2)
                self.assertTrue(result.success)
                self.assertIsNone(result.failure_reason)
                self.assertGreaterEqual(result.planning_time_seconds, 0)

    def test_already_at_goal_processes_one_node(self):
        for search in (bfs_result, dijkstra_result, astar_result):
            result = search(GridGraph(1, 1), (0, 0), (0, 0))
            self.assertEqual(result.expanded_nodes, 1)
            self.assertEqual(result.moves, 0)
            self.assertEqual(result.path_cost, 0)

    def test_unreachable_preserves_failure_without_fake_length(self):
        graph = GridGraph(1, 3, {(0, 1)})
        for search in (bfs_result, dijkstra_result, astar_result):
            result = search(graph, (0, 0), (0, 2))
            self.assertFalse(result.success)
            self.assertEqual(result.failure_reason, "unreachable")
            self.assertIsNone(result.path)
            self.assertIsNone(result.moves)
            self.assertIsNone(result.path_cost)
            self.assertEqual(result.expanded_nodes, 1)

    def test_path_apis_still_return_the_same_paths(self):
        graph = GridGraph(3, 5, {(0, 2), (1, 2)})
        for old, measured in ((bfs, bfs_result), (dijkstra, dijkstra_result), (astar, astar_result)):
            self.assertEqual(old(graph, (0, 0), (0, 4)),
                             measured(graph, (0, 0), (0, 4)).path)

    def test_weighted_result_counts_cost_and_moves_separately(self):
        graph = GridGraph(1, 3, cell_costs={(0, 1): 2, (0, 2): 3})
        for search in (dijkstra_result, astar_result):
            result = search(graph, (0, 0), (0, 2))
            self.assertEqual(result.moves, 2)
            self.assertEqual(result.path_cost, 5)
        with self.assertRaises(ValueError):
            bfs_result(graph, (0, 0), (0, 2))

    def test_invalid_endpoints_still_raise(self):
        for search in (bfs_result, dijkstra_result, astar_result):
            with self.assertRaises(ValueError):
                search(GridGraph(2, 2), (-1, 0), (1, 1))


if __name__ == "__main__":
    unittest.main()
