"""Run: python -m experiments.run_static [--demo]. This is a smoke study only."""

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from algorithms.astar import astar_result
from algorithms.bfs import bfs_result
from algorithms.dijkstra import dijkstra_result
from environments.grid_graph import GridGraph
from evaluation.visualize import render_svg, render_text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEARCHES = {"bfs": bfs_result, "dijkstra": dijkstra_result, "astar": astar_result}
FIELDS = ["schema_version", "run_id", "scenario_id", "seed", "rows", "cols",
          "agents", "condition", "obstacle_density_requested", "obstacle_density_actual",
          "algorithm", "success", "failure_reason", "moves", "path_cost", "expanded_nodes",
          "planning_time_seconds", "path_json"]


def validate_config(config):
    expected = {"schema_version", "purpose", "grid_sizes", "obstacle_densities", "seeds", "algorithms"}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("Config must contain exactly the documented smoke fields")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("Unsupported schema version")
    if config["purpose"] != "static_single_agent_smoke":
        raise ValueError("This runner only supports static_single_agent_smoke")
    for key in ("grid_sizes", "obstacle_densities", "seeds", "algorithms"):
        if not isinstance(config[key], list) or not config[key]:
            raise ValueError(f"{key} must be a nonempty list")
    for size in config["grid_sizes"]:
        if not isinstance(size, list) or len(size) != 2 or any(type(x) is not int or x <= 0 for x in size):
            raise ValueError("Grid sizes must be pairs of positive integers")
    for density in config["obstacle_densities"]:
        if isinstance(density, bool) or not isinstance(density, (int, float)) or not math.isfinite(density) or not 0 <= density <= 1:
            raise ValueError("Densities must be finite numbers between zero and one")
    if any(type(seed) is not int or seed < 0 for seed in config["seeds"]):
        raise ValueError("Seeds must be nonnegative integers")
    if any(not isinstance(name, str) or name not in SEARCHES for name in config["algorithms"]):
        raise ValueError("Unknown algorithm")
    for key in ("grid_sizes", "obstacle_densities", "seeds", "algorithms"):
        values = [tuple(x) if isinstance(x, list) else x for x in config[key]]
        if len(set(values)) != len(values):
            raise ValueError(f"Duplicate {key} would repeat measurements")


def make_scenario(rows, cols, density, seed):
    start, goal = (0, 0), (rows - 1, cols - 1)
    rng = random.Random(seed)
    obstacles = {(r, c) for r in range(rows) for c in range(cols)
                 if (r, c) not in (start, goal) and rng.random() < density}
    return GridGraph(rows, cols, obstacles), start, goal


def source_hashes():
    files = [*sorted((PROJECT_ROOT / "algorithms").glob("*.py")),
             PROJECT_ROOT / "environments/grid_graph.py",
             PROJECT_ROOT / "evaluation/visualize.py", Path(__file__).resolve()]
    return {p.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in files}


def run_smoke(config, output_root):
    validate_config(config)
    stamp = datetime.now(timezone.utc)
    run_id = stamp.strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid4().hex[:8]
    directory = Path(output_root) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    figures = directory / "paths"
    figures.mkdir()
    # Exact snapshots and hashes allow reconstruction even after defaults change.
    (directory / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    metadata = {"run_id": run_id, "purpose": config["purpose"], "created_at_utc": stamp.isoformat(),
                "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
                "processor": platform.processor(), "logical_cpus": os.cpu_count(),
                "dependencies": "Python standard library only", "source_sha256": source_hashes(),
                "timing": "perf_counter seconds: validation, setup, search and path reconstruction; excludes reporting and I/O",
                "expansions": "non-stale nodes processed, including goal; not discovered nodes",
                "density_denominator": "all grid cells; endpoints protected; requested density is Bernoulli probability",
                "map_filtering": "none; unreachable scenarios retained",
                "comparison_limit": "single run per algorithm per scenario, fixed order; no performance conclusions"}
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    scenarios = []
    with (directory / "raw_results.csv").open("x", newline="", encoding="utf-8") as csv_file, \
            (directory / "paths.txt").open("x", encoding="utf-8") as display:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
        writer.writeheader()
        for rows, cols in config["grid_sizes"]:
            for density in config["obstacle_densities"]:
                for seed in config["seeds"]:
                    graph, start, goal = make_scenario(rows, cols, density, seed)
                    scenario_id = f"grid{rows}x{cols}_density{density}_seed{seed}"
                    scenarios.append({"scenario_id": scenario_id, "seed": seed, "rows": rows, "cols": cols,
                                      "density_requested": density, "start": start, "goal": goal,
                                      "obstacles": sorted(graph.obstacles), "cell_costs": []})
                    for name in config["algorithms"]:
                        result = SEARCHES[name](graph, start, goal)
                        writer.writerow({"schema_version": 1, "run_id": run_id, "scenario_id": scenario_id,
                                         "seed": seed, "rows": rows, "cols": cols, "agents": 1, "condition": "static",
                                         "obstacle_density_requested": density,
                                         "obstacle_density_actual": len(graph.obstacles) / (rows * cols),
                                         "algorithm": name, "success": int(result.success),
                                         "failure_reason": result.failure_reason, "moves": result.moves,
                                         "path_cost": result.path_cost, "expanded_nodes": result.expanded_nodes,
                                         "planning_time_seconds": result.planning_time_seconds,
                                         "path_json": json.dumps(result.path)})
                        title = f"{scenario_id} / {name}"
                        display.write(f"{title}\nMoves={result.moves}; cost={result.path_cost}; "
                                      f"expanded={result.expanded_nodes}; seconds={result.planning_time_seconds:.9f}\n")
                        display.write(render_text(graph, start, goal, result.path) + "\n\n")
                        (figures / f"{scenario_id}_{name}.svg").write_text(
                            render_svg(graph, start, goal, result.path, title), encoding="utf-8")
    (directory / "scenarios.json").write_text(json.dumps(scenarios, indent=2) + "\n", encoding="utf-8")
    # Created last: its presence distinguishes a completed run from partial output.
    (directory / "COMPLETE.json").write_text(json.dumps({"scenario_count": len(scenarios),
        "row_count": len(scenarios) * len(config["algorithms"]), "purpose": config["purpose"]}, indent=2) + "\n", encoding="utf-8")
    return directory


def show_demo():
    graph = GridGraph(3, 5, {(0, 2), (1, 2)})
    for name, search in SEARCHES.items():
        result = search(graph, (0, 0), (0, 4))
        print(f"\n{name.upper()}: moves={result.moves}, cost={result.path_cost}, "
              f"expanded={result.expanded_nodes}, seconds={result.planning_time_seconds:.9f}")
        print(render_text(graph, (0, 0), (0, 4), result.path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs/static_smoke.json")
    parser.add_argument("--output-root", type=Path, default=PROJECT_ROOT / "results/raw/static_smoke")
    parser.add_argument("--demo", action="store_true", help="Display the fixed detour example without writing a run")
    args = parser.parse_args()
    if args.demo:
        show_demo()
        return
    config = json.loads(args.config.read_text(encoding="utf-8"))
    directory = run_smoke(config, args.output_root)
    print(f"Static single-agent smoke run saved to: {directory}")
    print("CSV, exact maps/config, metadata, text displays and SVG paths saved. This is not a final paper benchmark.")


if __name__ == "__main__":
    main()
