"""Audit immutable CP-05 banks, learning counters, and replayed evaluation traces."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import torch

from algorithms.bfs import bfs
from algorithms.dqn import DQNAgent, epsilon_at
from environments.grid_graph import GridGraph
from environments.random_maps import map_id, make_scenario_env
from evaluation.navigation import SearchController
from evaluation.varied_protocol import ROOT, fixed_directory
from training.train_varied import validation_rollouts


def rows(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def verify_bank(directory):
    completed = json.loads((directory / 'COMPLETE.json').read_text())
    config = json.loads((directory / 'config.json').read_text())
    bank = json.loads((directory / 'map_bank.json').read_text())
    metadata = json.loads((directory / 'metadata.json').read_text())
    identities = set()
    for partition, maps in bank['partitions'].items():
        assert len(maps) == config['partitions'][partition][1]
        for scenario in maps:
            identity = map_id(scenario['rows'], scenario['cols'], scenario['obstacles'])
            assert identity == scenario['map_id'] and identity not in identities
            identities.add(identity)
            graph = GridGraph(scenario['rows'], scenario['cols'], {tuple(p) for p in scenario['obstacles']})
            route = bfs(graph, tuple(scenario['start']), tuple(scenario['goal']))
            assert scenario['initial_reachable'] == (route is not None)
            assert scenario['initial_optimal_moves'] == (len(route)-1 if route else None)
    fixed = json.loads((fixed_directory(config) / 'config.json').read_text())['map']
    assert map_id(fixed['rows'], fixed['cols'], fixed['obstacles']) not in identities
    for name, digest in metadata['source_sha256'].items():
        assert hashlib.sha256((directory / 'source' / name).read_bytes()).hexdigest() == digest
    return config, bank, completed


def audit_training(directory):
    config, bank, completed = verify_bank(directory)
    recorded = rows(directory / 'training_episodes.csv')
    gradients = rows(directory / 'optimizer_updates.csv')
    validations = [json.loads(line) for line in (directory / 'validation.jsonl').read_text().splitlines()]
    summaries = json.loads((directory / 'summary.json').read_text())
    assert len(recorded) == completed['training_episode_rows'] == len(config['seeds']) * config['episodes']
    assert completed['test_maps_used'] is False
    training = bank['partitions']['train']
    validation_ids = {m['map_id'] for m in bank['partitions']['validation']}
    results = []
    for seed in config['seeds']:
        group = [r for r in recorded if int(r['seed']) == seed]
        updates = [r for r in gradients if int(r['seed']) == seed]
        assert [int(r['episode']) for r in group] == list(range(1, config['episodes']+1))
        rng = random.Random(seed + 20000)
        count = 0
        for r in group:
            expected_map = training[rng.randrange(len(training))]
            assert r['map_id'] == expected_map['map_id'] and int(r['map_seed']) == expected_map['map_seed']
            assert int(r['initial_reachable']) == expected_map['initial_reachable']
            count += int(r['elapsed_steps'])
            assert int(r['environment_steps']) == count
            assert 0 <= int(r['moves']) <= int(r['elapsed_steps']) <= config['map_spec']['max_steps']
            assert float(r['path_cost']) == int(r['moves'])
            reward = 100 * int(r['success']) - int(r['elapsed_steps']) - 10 * int(r['obstacle_attempts']) - 5 * int(r['boundary_attempts'])
            assert float(r['episode_reward']) == reward
            assert sum(float(r[k+'_reward']) for k in ('step', 'obstacle', 'boundary', 'goal')) == reward
            assert r['arrival_step'] == (r['elapsed_steps'] if int(r['success']) else '')
            assert math.isclose(float(r['epsilon']), epsilon_at(int(r['episode'])-1, config['epsilon_initial'], config['epsilon_final'], config['epsilon_decay_episodes']))
            expected_updates = max(0, count // config['train_every_steps'] - (config['warmup_steps']-1) // config['train_every_steps'])
            assert int(r['optimizer_updates']) == expected_updates
        assert len(updates) == int(group[-1]['optimizer_updates'])
        assert [int(r['optimizer_update']) for r in updates] == list(range(1, len(updates)+1))
        for r in updates:
            assert math.isfinite(float(r['loss'])) and float(r['loss']) >= 0
            assert math.isfinite(float(r['gradient_norm_before_clip']))
            assert int(r['target_synced']) == (int(r['optimizer_update']) % config['network']['target_update_steps'] == 0)
        checks = [v for v in validations if v['seed'] == seed]
        assert len(checks) == config['episodes'] // config['evaluate_every_episodes'] + 1
        assert all(c['map_id'] in validation_ids for v in checks for c in v['cases'])
        final = next(v for v in checks if v.get('phase') == 'final')
        agent, metadata = DQNAgent.load(directory / 'models' / f'seed_{seed}.pt')
        assert metadata['training_config'] == config and metadata['environment_steps'] == count
        repeat = validation_rollouts(agent, config, bank['partitions']['validation'])
        assert all(a['rollout']['actions'] == b['rollout']['actions'] for a, b in zip(final['cases'], repeat))
        summary = next(s for s in summaries if s['seed'] == seed)
        assert summary['optimizer_updates'] == len(updates) and summary['environment_steps'] == count
        assert summary['validation_successes'] == sum(c['rollout']['success'] for c in repeat)
        results.append({'seed': seed, 'validation_successes': summary['validation_successes'], 'validation_episodes': len(repeat)})
    return {'kind': 'training', 'episodes': len(recorded), 'optimizer_updates': len(gradients),
            'validation_records': len(validations), 'seed_results': results,
            'splits_disjoint': True, 'no_test_maps_in_training': True, 'reload_matches': True, 'source_snapshots_match': True}


def audit_evaluation(directory):
    config, bank, completed = verify_bank(directory)
    recorded = rows(directory / 'raw_results.csv')
    traces = [json.loads(line) for line in (directory / 'trajectories.jsonl').read_text().splitlines()]
    assert len(recorded) == len(traces) == completed['row_count']
    scenarios = {m['map_id']: m for m in bank['partitions']['test']}
    checkpoints = json.loads((directory / 'checkpoints.json').read_text())
    agents = {}
    for identity, reference in checkpoints.items():
        path = Path(reference['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest() == reference['sha256']
        agents[identity], _ = DQNAgent.load(path)
    for seed in config['seeds']:
        fixed = agents[f'dqn_fixed/{seed}']
        agents[f'dqn_untrained/{seed}'] = DQNAgent(fixed.config, seed=seed)
    identities = set()
    applied_changes = {}
    for row, trace in zip(recorded, traces):
        seed = None if row['training_seed'] == '' else int(row['training_seed'])
        identity = (row['method'], seed, row['map_id'], row['condition'])
        assert identity == (trace['method'], trace['training_seed'], trace['map_id'], trace['condition'])
        assert identity not in identities
        identities.add(identity)
        scenario = scenarios[row['map_id']]
        assert int(row['map_seed']) == scenario['map_seed']
        env = make_scenario_env(scenario, max_steps=config['map_spec']['max_steps'], dynamic=row['condition']=='dynamic')
        agent = agents.get(f'{row["method"]}/{seed}')
        controller = agent or SearchController(env, 'astar' if row['method']=='astar_frozen' else row['method'], frozen=row['method']=='astar_frozen')
        observation, info = env.reset(seed=scenario['map_seed'])
        rollout = trace['rollout']
        assert list(observation) == rollout['initial_observation']
        for transition in rollout['transitions']:
            assert list(observation) == transition['observation']
            assert int(controller.act(observation, epsilon=0)) == transition['action']
            observation, reward, _, _, info = env.step(transition['action'])
            assert reward == transition['reward'] == sum(transition['reward_components'].values())
            assert list(observation) == transition['next_observation']
            assert list(info['position']) == transition['position']
            assert info.get('action_graph_version', 0) == transition['action_graph_version']
        assert info['terminated'] or info['truncated']
        for key in ('elapsed_steps', 'moves', 'path_cost', 'episode_reward', 'obstacle_attempts', 'boundary_attempts'):
            assert float(row[key]) == info[key]
        assert int(row['success']) == info['success']
        assert row['arrival_step'] == (str(info['arrival_step']) if info['success'] else '')
        assert row['failure_reason'] == (info['failure_reason'] or '')
        if row['condition']=='dynamic':
            assert row['static_move_gap'] == ''
            changes = info['change_history']
            assert not any(c['status']=='rejected_occupied' for c in changes)
            canonical = json.dumps(changes, sort_keys=True)
            if row['map_id'] in applied_changes:
                assert applied_changes[row['map_id']] == canonical
            applied_changes[row['map_id']] = canonical
        elif info['success']:
            assert math.isclose(float(row['static_move_gap']), (info['moves']-scenario['initial_optimal_moves'])/scenario['initial_optimal_moves'])
        for key in ('decision_time_seconds', 'inference_time_seconds', 'planning_time_seconds', 'episode_time_seconds'):
            if row.get(key):
                assert math.isfinite(float(row[key])) and float(row[key]) >= 0
    expected_methods = 4 + len(config['seeds']) * (3 if completed['varied_models_included'] else 2)
    assert len(recorded) == completed['test_map_count'] * 2 * expected_methods
    return {'kind': 'evaluation', 'episodes': len(recorded), 'test_maps': completed['test_map_count'],
            'methods_per_map_condition': expected_methods, 'splits_disjoint': True, 'source_snapshots_match': True,
            'all_actions_replayed': True, 'identical_realized_schedules': True, 'model_digests_match': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    torch.set_num_threads(1)
    result = audit_evaluation(args.run_directory) if (args.run_directory / 'raw_results.csv').exists() else audit_training(args.run_directory)
    if args.output:
        with args.output.open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
