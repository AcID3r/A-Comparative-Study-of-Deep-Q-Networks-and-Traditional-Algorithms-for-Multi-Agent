"""Scripted environment checks, not learned-policy evaluation or paper results."""

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

from algorithms.bfs import bfs
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action, ACTION_DELTAS, OBSERVATION_FEATURES, OBSERVATION_VERSION, SingleAgentEnv


def trace_episode(env, actions, name):
    observation, reset_info = env.reset(seed=42)
    initial_observation = observation
    transitions = []
    final = reset_info
    for action in actions:
        observation, reward, terminated, truncated, final = env.step(action)
        transitions.append({'action': Action(action).name, 'observation': observation,
                            'reward': reward, 'terminated': terminated, 'truncated': truncated, 'info': final})
        if terminated or truncated:
            break
    return {'name': name, 'map': {'rows': env.graph.rows, 'cols': env.graph.cols,
            'obstacles': sorted(env.graph.obstacles), 'start': env.start, 'goal': env.goal,
            'max_steps': env.max_steps}, 'initial_observation': initial_observation,
            'reset_info': reset_info, 'transitions': transitions, 'final_info': final}


def run_demo():
    graph = GridGraph(3, 5, {(0, 2), (1, 2)})
    path = bfs(graph, (0, 0), (0, 4))
    by_delta = {delta: Action(i) for i, delta in enumerate(ACTION_DELTAS[:4])}
    actions = [by_delta[(b[0] - a[0], b[1] - a[1])] for a, b in zip(path, path[1:])]
    cases = [trace_episode(SingleAgentEnv(graph, (0, 0), (0, 4), max_steps=8), actions, 'baseline_route'),
             trace_episode(SingleAgentEnv(GridGraph(3, 3, {(0, 1)}), (0, 0), (2, 2), max_steps=3),
                           [Action.UP, Action.RIGHT, Action.WAIT], 'rejected_moves_and_timeout'),
             trace_episode(SingleAgentEnv(GridGraph(1, 1), (0, 0), (0, 0)), [], 'already_at_goal')]
    root = Path(__file__).resolve().parents[1]
    hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in
              ('environments/single_agent_env.py', 'environments/grid_graph.py',
               'algorithms/bfs.py', 'algorithms/search_result.py', 'experiments/run_episode.py')}
    return {'purpose': 'CP-03 scripted correctness demonstration', 'python': sys.version,
            'platform': platform.platform(), 'observation_version': OBSERVATION_VERSION,
            'observation_features': OBSERVATION_FEATURES, 'source_sha256': hashes, 'cases': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Optionally save JSON trace to a new file; refuses overwrite')
    args = parser.parse_args()
    result = run_demo()
    for case in result['cases']:
        info = case['final_info']
        print(f"{case['name']}: success={info['success']}, terminated={info['terminated']}, "
              f"truncated={info['truncated']}, turns={info['elapsed_steps']}, moves={info['moves']}, "
              f"reward={info['episode_reward']:g}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
            f.write('\n')
        print(f'Scripted validation trace saved to: {args.output}')


if __name__ == '__main__':
    main()
