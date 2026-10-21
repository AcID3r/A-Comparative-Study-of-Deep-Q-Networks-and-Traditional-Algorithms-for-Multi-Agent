"""Geometry-disjoint deterministic map banks, with unreachable maps retained."""

import hashlib
import json
import math
import random
from algorithms.bfs import bfs
from environments.grid_graph import GridGraph
from environments.dynamic_env import ObstacleChange, DynamicSingleAgentEnv
from environments.single_agent_env import SingleAgentEnv


def map_id(rows, cols, obstacles):
    data = json.dumps([rows, cols, sorted(obstacles)], separators=(',', ':')).encode()
    return hashlib.sha256(data).hexdigest()


def build_bank(rows, cols, density, partitions, *, excluded_ids=()):
    GridGraph(rows, cols)
    if isinstance(density, bool) or not isinstance(density, (int, float)) or not math.isfinite(density) or not 0 <= density <= 1:
        raise ValueError('Density must be finite in [0,1]')
    used = set(excluded_ids)
    seeds_used = set()
    result = {'rows': rows, 'cols': cols, 'density_requested': density, 'partitions': {},
              'rejected_candidates': [], 'reachability_filter': 'none; unreachable maps retained'}
    for name, (first_seed, count) in partitions.items():
        if type(first_seed) is not int or first_seed < 0 or type(count) is not int or count <= 0:
            raise ValueError('Partition counts/seeds must be positive/nonnegative integers')
        maps = []
        for candidate in range(first_seed, first_seed + 1000):
            if candidate in seeds_used:
                raise ValueError('Partition seed ranges overlap')
            seeds_used.add(candidate)
            rng = random.Random(candidate)
            start, goal = (0, 0), (rows - 1, cols - 1)
            walls = {(r, c) for r in range(rows) for c in range(cols)
                     if (r, c) not in (start, goal) and rng.random() < density}
            identity = map_id(rows, cols, walls)
            if identity in used:
                result['rejected_candidates'].append({'partition': name, 'seed': candidate, 'reason': 'duplicate_geometry'})
                continue
            used.add(identity)
            path = bfs(GridGraph(rows, cols, walls), start, goal)
            maps.append({'map_id': identity, 'map_seed': candidate, 'rows': rows, 'cols': cols,
                         'obstacles': sorted(walls), 'start': start, 'goal': goal,
                         'initial_reachable': path is not None, 'initial_optimal_moves': None if path is None else len(path) - 1})
            if len(maps) == count:
                break
        if len(maps) != count:
            raise ValueError('Not enough unique maps in the declared candidate range')
        result['partitions'][name] = maps
    return result


def blocked_route_schedule(scenario, *, add_tick=3, remove_tick=8):
    graph = GridGraph(scenario['rows'], scenario['cols'], {tuple(p) for p in scenario['obstacles']})
    start, goal = tuple(scenario['start']), tuple(scenario['goal'])
    path = bfs(graph, start, goal)
    cells = path[1:-1] if path else [(r, c) for r in range(graph.rows) for c in range(graph.cols) if graph.is_free((r, c))]
    candidates = [p for p in cells if p not in (start, goal) and abs(p[0] - start[0]) + abs(p[1] - start[1]) >= add_tick]
    if not candidates:
        return ()
    # At tick t, any agent has taken at most t-1 moves. This prevents occupancy
    # rejection and gives every evaluated method the same realized schedule.
    cell = candidates[0]
    return (ObstacleChange(add_tick, cell, 'add'), ObstacleChange(remove_tick, cell, 'remove'))


def make_scenario_env(scenario, *, max_steps=50, dynamic=False):
    graph = GridGraph(scenario['rows'], scenario['cols'], {tuple(p) for p in scenario['obstacles']})
    start, goal = tuple(scenario['start']), tuple(scenario['goal'])
    if dynamic:
        return DynamicSingleAgentEnv(graph, start, goal, max_steps=max_steps, schedule=blocked_route_schedule(scenario))
    return SingleAgentEnv(graph, start, goal, max_steps=max_steps)
