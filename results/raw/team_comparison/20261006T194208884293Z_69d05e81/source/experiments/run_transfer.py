"""Shared held-out static/dynamic rollout protocol for CP-04 and CP-05 policies."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from time import perf_counter

import torch
from algorithms.dqn import DQNAgent
from environments.random_maps import make_scenario_env, blocked_route_schedule
from evaluation.navigation import SearchController, rollout
from evaluation.varied_protocol import ROOT, fixed_directory, generate_bank, new_run

FIELDS = ['method', 'training_seed', 'map_id', 'map_seed', 'condition', 'initial_reachable',
          'success', 'failure_reason', 'elapsed_steps', 'moves', 'path_cost', 'arrival_step',
          'episode_reward', 'obstacle_attempts', 'boundary_attempts', 'initial_optimal_moves',
          'static_move_gap', 'decision_time_seconds', 'episode_time_seconds', 'inference_time_seconds',
          'planning_time_seconds', 'expanded_nodes', 'plan_calls', 'change_count', 'rejected_changes']


def run_evaluation(config, output_root, *, varied_run=None, smoke=False):
    bank = generate_bank(config)
    test_maps = bank['partitions']['test'][:2] if smoke else bank['partitions']['test']
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    policies = []
    checkpoints = {}
    for seed in config['seeds']:
        model = fixed_directory(config) / 'models' / f'seed_{seed}.pt'
        fixed, _ = DQNAgent.load(model)
        policies.extend([('dqn_fixed', seed, fixed), ('dqn_untrained', seed, DQNAgent(fixed.config, seed=seed))])
        checkpoints[f'dqn_fixed/{seed}'] = {'path': str(model.resolve()), 'sha256': hashlib.sha256(model.read_bytes()).hexdigest()}
        if varied_run:
            directory = Path(varied_run)
            if not (directory / 'COMPLETE.json').exists():
                raise ValueError('Random-map evaluation requires completed training')
            saved_bank = json.loads((directory / 'map_bank.json').read_text(encoding='utf-8'))
            if json.dumps(saved_bank, sort_keys=True) != json.dumps(bank, sort_keys=True):
                raise ValueError('Training and evaluation map banks differ')
            model = directory / 'models' / f'seed_{seed}.pt'
            varied, _ = DQNAgent.load(model)
            policies.append(('dqn_varied', seed, varied))
            checkpoints[f'dqn_varied/{seed}'] = {'path': str(model.resolve()), 'sha256': hashlib.sha256(model.read_bytes()).hexdigest()}
    directory = new_run(output_root, config, bank, 'heldout_transfer_smoke' if smoke else 'heldout_transfer')
    (directory / 'checkpoints.json').write_text(json.dumps(checkpoints, indent=2) + '\n', encoding='utf-8')
    rows = []
    with (directory / 'raw_results.csv').open('x', newline='', encoding='utf-8') as cf, \
            (directory / 'trajectories.jsonl').open('x', encoding='utf-8') as tf:
        writer = csv.DictWriter(cf, fieldnames=FIELDS)
        writer.writeheader()
        for index, scenario in enumerate(test_maps):
            for dynamic in (False, True):
                condition = 'dynamic' if dynamic else 'static'
                methods = [(name, None, None) for name in ('bfs', 'dijkstra', 'astar', 'astar_frozen')] + policies
                for method, seed, agent in methods:
                    env = make_scenario_env(scenario, max_steps=config['map_spec']['max_steps'], dynamic=dynamic)
                    setup_started = perf_counter()
                    controller = SearchController(env, 'astar' if method == 'astar_frozen' else method, frozen=method == 'astar_frozen') if agent is None else agent
                    setup_seconds = perf_counter() - setup_started
                    result = rollout(controller, env, seed=scenario['map_seed'])
                    info = result['final_info']
                    row = {key: info[key] for key in ('success', 'failure_reason', 'elapsed_steps', 'moves', 'path_cost',
                                                      'arrival_step', 'episode_reward', 'obstacle_attempts', 'boundary_attempts')}
                    changes = info.get('change_history', [])
                    row.update(method=method, training_seed=seed, map_id=scenario['map_id'], map_seed=scenario['map_seed'],
                        condition=condition, initial_reachable=int(scenario['initial_reachable']), success=int(info['success']),
                        initial_optimal_moves=scenario['initial_optimal_moves'],
                        static_move_gap=(info['moves'] - scenario['initial_optimal_moves']) / scenario['initial_optimal_moves']
                            if not dynamic and info['success'] and scenario['initial_optimal_moves'] else None,
                        decision_time_seconds=result['decision_time_seconds'] + setup_seconds,
                        episode_time_seconds=result['episode_time_seconds'] + setup_seconds,
                        inference_time_seconds=result['decision_time_seconds'] if agent is not None else None,
                        planning_time_seconds=result['planning_time_seconds'] if agent is None else None,
                        expanded_nodes=result['expanded_nodes'], plan_calls=result['plan_calls'],
                        change_count=sum(c['status'] == 'applied' for c in changes),
                        rejected_changes=sum(c['status'] == 'rejected_occupied' for c in changes))
                    writer.writerow(row)
                    rows.append(row)
                    schedule = blocked_route_schedule(scenario) if dynamic else ()
                    tf.write(json.dumps({'method': method, 'training_seed': seed, 'map_id': scenario['map_id'],
                        'condition': condition, 'schedule': [{'tick': e.tick, 'position': e.position, 'operation': e.operation} for e in schedule],
                        'rollout': result}) + '\n')
            if (index + 1) % 10 == 0:
                cf.flush(); tf.flush()
                print(f'Evaluated {index + 1}/{len(test_maps)} held-out maps', flush=True)
    summary = []
    for method in sorted({r['method'] for r in rows}):
        for condition in ('static', 'dynamic'):
            for seed in sorted({r['training_seed'] for r in rows if r['method'] == method}, key=lambda x: -1 if x is None else x):
                group = [r for r in rows if r['method'] == method and r['condition'] == condition and r['training_seed'] == seed]
                successful = [r for r in group if r['success']]
                reachable = [r for r in group if r['initial_reachable']]
                summary.append({'method': method, 'condition': condition, 'training_seed': seed,
                    'episodes': len(group), 'successes': len(successful), 'success_rate': len(successful) / len(group),
                    'initial_reachable_episodes': len(reachable),
                    'reachable_success_rate': sum(r['success'] for r in reachable) / len(reachable) if reachable else None,
                    'successful_mean_moves': sum(r['moves'] for r in successful) / len(successful) if successful else None,
                    'successful_mean_arrival': sum(r['arrival_step'] for r in successful) / len(successful) if successful else None})
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (directory / 'COMPLETE.json').write_text(json.dumps({'row_count': len(rows), 'test_map_count': len(test_maps),
        'varied_models_included': bool(varied_run), 'smoke': smoke}, indent=2) + '\n', encoding='utf-8')
    print(f'Transfer evaluation saved: {directory}', flush=True)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/dqn_varied.json')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'results/raw/transfer')
    parser.add_argument('--varied-run', type=Path)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    run_evaluation(json.loads(args.config.read_text(encoding='utf-8')), args.output_root, varied_run=args.varied_run, smoke=args.smoke)


if __name__ == '__main__':
    main()
