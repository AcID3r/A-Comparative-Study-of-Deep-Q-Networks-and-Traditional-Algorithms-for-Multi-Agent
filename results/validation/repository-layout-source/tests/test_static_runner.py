"""Integration checks use temporary directories, never real experiment outputs."""

import copy
import csv
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from environments.grid_graph import GridGraph
from evaluation.visualize import render_svg, render_text
from experiments.run_static import FIELDS, make_scenario, run_smoke, validate_config
from tests.test_baselines import reference_cost


def tiny_config():
    return {"schema_version": 1, "purpose": "static_single_agent_smoke",
            "grid_sizes": [[3, 3]], "obstacle_densities": [0.0, 1.0],
            "seeds": [7], "algorithms": ["bfs", "dijkstra", "astar"]}


class DisplayTests(unittest.TestCase):
    def test_text_preserves_walls_endpoints_and_route(self):
        graph = GridGraph(2, 3, {(0, 1)})
        path = [(0, 0), (1, 0), (1, 1), (1, 2), (0, 2)]
        self.assertEqual(render_text(graph, (0, 0), (0, 2), path).splitlines()[:2],
                         ["S # G", "* * *"])

    def test_missing_route_and_same_endpoint_are_clear(self):
        self.assertIn("No route exists", render_text(GridGraph(1, 3, {(0, 1)}), (0, 0), (0, 2), None))
        self.assertEqual(render_text(GridGraph(1, 1), (0, 0), (0, 0), [(0, 0)]).splitlines()[0], "B")

    def test_svg_is_valid_and_escapes_title(self):
        graph = GridGraph(1, 2)
        document = render_svg(graph, (0, 0), (0, 1), [(0, 0), (0, 1)], "A* <route> & costs")
        root = ET.fromstring(document)
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(root.find("s:title", ns).text, "A* <route> & costs")
        self.assertEqual(len(root.findall("s:rect", ns)), 3)  # background and two cells
        self.assertIn("Moves: 1; cost: 1", document)

    def test_visualization_rejects_invalid_or_wrong_endpoint_path(self):
        graph = GridGraph(2, 2)
        for renderer in (render_text, render_svg):
            for path in ([(0, 0), (1, 1)], [(0, 1), (1, 1)], []):
                with self.assertRaises(ValueError):
                    renderer(graph, (0, 0), (1, 1), path)

    def test_weighted_display_explains_costs(self):
        graph = GridGraph(1, 2, cell_costs={(0, 1): 2})
        path = [(0, 0), (0, 1)]
        self.assertIn("(0, 1)=2", render_text(graph, (0, 0), (0, 1), path))
        self.assertIn("cost: 2", render_svg(graph, (0, 0), (0, 1), path))


class StaticRunnerTests(unittest.TestCase):
    def test_seeded_scenarios_repeat_and_protect_endpoints(self):
        for size in (5, 10, 15):
            a, start, goal = make_scenario(size, size, .2, 42)
            b, _, _ = make_scenario(size, size, .2, 42)
            self.assertEqual(a.obstacles, b.obstacles)
            self.assertTrue(a.is_free(start))
            self.assertTrue(a.is_free(goal))

    def test_invalid_configs_are_rejected_before_creating_output(self):
        changes = [{"schema_version": True}, {"purpose": "final_benchmark"},
                   {"grid_sizes": [[0, 3]]}, {"grid_sizes": [[True, 3]]},
                   {"seeds": []}, {"seeds": [1, 1]}, {"seeds": [-1]},
                   {"obstacle_densities": [float("nan")]}, {"obstacle_densities": [1.1]},
                   {"obstacle_densities": [True]}, {"algorithms": ["unknown"]},
                   {"algorithms": ["bfs", "bfs"]}, {"extra": "typo"}]
        with tempfile.TemporaryDirectory() as folder:
            for change in changes:
                config = tiny_config() | change
                with self.subTest(change=change), self.assertRaises(ValueError):
                    run_smoke(config, folder)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_exports_matched_scenarios_and_retains_unreachable_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = run_smoke(tiny_config(), folder)
            with (directory / "raw_results.csv").open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames, FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 6)
            scenarios = json.loads((directory / "scenarios.json").read_text())
            self.assertEqual(len(scenarios), 2)
            for scenario in scenarios:
                matching = [row for row in rows if row["scenario_id"] == scenario["scenario_id"]]
                self.assertEqual({row["algorithm"] for row in matching}, {"bfs", "dijkstra", "astar"})
                graph = GridGraph(scenario["rows"], scenario["cols"],
                                  {tuple(pos) for pos in scenario["obstacles"]})
                start, goal = tuple(scenario["start"]), tuple(scenario["goal"])
                expected = reference_cost(graph, start, goal)
                for row in matching:
                    self.assertGreaterEqual(float(row["planning_time_seconds"]), 0)
                    self.assertGreaterEqual(int(row["expanded_nodes"]), 1)
                    if expected == float("inf"):
                        self.assertEqual(row["success"], "0")
                        self.assertEqual(row["failure_reason"], "unreachable")
                        self.assertEqual(row["moves"], "")
                        self.assertEqual(row["path_cost"], "")
                        self.assertIsNone(json.loads(row["path_json"]))
                    else:
                        path = [tuple(pos) for pos in json.loads(row["path_json"])]
                        self.assertEqual(path[0], start)
                        self.assertEqual(path[-1], goal)
                        self.assertEqual(graph.path_cost(path), expected)
                        self.assertEqual(int(row["moves"]), len(path) - 1)
                        self.assertEqual(row["success"], "1")
            self.assertEqual(len(list((directory / "paths").glob("*.svg"))), 6)
            for svg in (directory / "paths").glob("*.svg"):
                ET.parse(svg)
            self.assertIn("No route exists", (directory / "paths.txt").read_text())
            self.assertEqual(json.loads((directory / "config.json").read_text()), tiny_config())
            metadata = json.loads((directory / "metadata.json").read_text())
            self.assertIn("algorithms/astar.py", metadata["source_sha256"])
            self.assertEqual(len(metadata["source_sha256"]["algorithms/astar.py"]), 64)
            self.assertEqual(json.loads((directory / "COMPLETE.json").read_text())["row_count"], 6)

    def test_repeated_runs_keep_previous_output_and_repeat_non_time_data(self):
        with tempfile.TemporaryDirectory() as folder:
            config = tiny_config()
            first = run_smoke(config, folder)
            original = (first / "raw_results.csv").read_bytes()
            second = run_smoke(config, folder)
            self.assertNotEqual(first, second)
            self.assertEqual((first / "raw_results.csv").read_bytes(), original)
            self.assertEqual((first / "scenarios.json").read_bytes(), (second / "scenarios.json").read_bytes())
            def deterministic_rows(directory):
                with (directory / "raw_results.csv").open(newline="", encoding="utf-8") as f:
                    return [{k: v for k, v in row.items() if k not in ("run_id", "planning_time_seconds")}
                            for row in csv.DictReader(f)]
            self.assertEqual(deterministic_rows(first), deterministic_rows(second))

    def test_single_cell_scenario_has_zero_moves(self):
        with tempfile.TemporaryDirectory() as folder:
            config = tiny_config() | {"grid_sizes": [[1, 1]], "obstacle_densities": [1]}
            directory = run_smoke(config, folder)
            with (directory / "raw_results.csv").open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.assertEqual(row["moves"], "0")
                    self.assertEqual(row["expanded_nodes"], "1")


if __name__ == "__main__":
    unittest.main()
