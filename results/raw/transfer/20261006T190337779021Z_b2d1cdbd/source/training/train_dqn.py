"""Train fixed-map CPU DQN: python -m training.train_dqn [--smoke]."""

import argparse
import copy
import csv
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import sys
from time import perf_counter
from uuid import uuid4

import torch
from algorithms.astar import astar_result
from algorithms.bfs import bfs_result
from algorithms.dijkstra import dijkstra_result
from algorithms.dqn import DQNAgent, DQNConfig, ReplayBuffer, Transition, epsilon_at, positive_integer, finite_number
from environments.grid_graph import GridGraph
from environments.single_agent_env import SingleAgentEnv, OBSERVATION_FEATURES, OBSERVATION_VERSION
from evaluation.evaluate_dqn import evaluate_agent
from evaluation.plot_learning import plot_run
from evaluation.visualize import render_svg

ROOT = Path(__file__).resolve().parents[1]
EPISODE_FIELDS = ['seed', 'episode', 'epsilon', 'success', 'failure_reason', 'episode_reward',
                  'elapsed_steps', 'moves', 'path_cost', 'arrival_step', 'obstacle_attempts',
                  'boundary_attempts', 'step_reward', 'obstacle_reward', 'boundary_reward', 'goal_reward',
                  'environment_steps', 'optimizer_updates', 'mean_loss', 'training_time_seconds']
UPDATE_FIELDS = ['seed', 'episode', 'environment_steps', 'optimizer_update', 'loss',
                 'gradient_norm_before_clip', 'target_synced']
EVALUATION_FIELDS = ['seed', 'phase', 'training_episode', 'success', 'failure_reason', 'episode_reward',
                     'elapsed_steps', 'moves', 'path_cost', 'arrival_step', 'obstacle_attempts',
                     'boundary_attempts', 'inference_time_seconds', 'episode_time_seconds',
                     'optimal_moves', 'optimality_gap', 'actions_json', 'positions_json']


def validate_config(config):
    expected = {'schema_version', 'purpose', 'map', 'seeds', 'episodes', 'batch_size', 'replay_capacity',
                'warmup_steps', 'train_every_steps', 'epsilon_initial', 'epsilon_final',
                'epsilon_decay_episodes', 'evaluate_every_episodes', 'rolling_window', 'network'}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError('Config fields must match the documented DQN schema')
    if type(config['schema_version']) is not int or config['schema_version'] != 1:
        raise ValueError('Unsupported config schema')
    if config['purpose'] not in ('fixed_map_development', 'fixed_map_smoke'):
        raise ValueError('Unsupported run purpose')
    for name in ('episodes', 'batch_size', 'replay_capacity', 'warmup_steps', 'train_every_steps',
                 'epsilon_decay_episodes', 'evaluate_every_episodes', 'rolling_window'):
        positive_integer(config[name], name)
    if config['batch_size'] > config['replay_capacity'] or config['warmup_steps'] < config['batch_size']:
        raise ValueError('Warm-up and replay must accommodate the batch')
    if not isinstance(config['seeds'], list) or not config['seeds']:
        raise ValueError('Training seeds must be a nonempty list')
    if any(type(seed) is not int or seed < 0 for seed in config['seeds']) or len(set(config['seeds'])) != len(config['seeds']):
        raise ValueError('Training seeds must be distinct nonnegative integers')
    epsilon_at(0, config['epsilon_initial'], config['epsilon_final'], config['epsilon_decay_episodes'])
    if not isinstance(config['network'], dict) or set(config['network']) != set(asdict(DQNConfig())):
        raise ValueError('Network fields must match the documented schema')
    DQNConfig(**config['network'])
    scenario = config['map']
    if not isinstance(scenario, dict) or set(scenario) != {'rows', 'cols', 'obstacles', 'start', 'goal', 'max_steps'}:
        raise ValueError('Map fields must match the documented schema')
    if not isinstance(scenario['obstacles'], list) or any(not isinstance(p, list) or len(p) != 2 for p in scenario['obstacles']):
        raise ValueError('Obstacles must be coordinate pairs')
    if len({tuple(p) for p in scenario['obstacles']}) != len(scenario['obstacles']):
        raise ValueError('Duplicate obstacles are not allowed')
    env = make_env(config)
    optimal = bfs_result(env.graph, env.start, env.goal)
    if not optimal.success or optimal.moves == 0 or optimal.moves > env.max_steps:
        raise ValueError('Fixed-map training requires a nontrivial route within the horizon')


def make_env(config):
    m = config['map']
    graph = GridGraph(m['rows'], m['cols'], {tuple(p) for p in m['obstacles']})
    return SingleAgentEnv(graph, tuple(m['start']), tuple(m['goal']), max_steps=m['max_steps'])


def evaluation_row(seed, phase, episode, result, optimal_moves):
    names = ('success', 'failure_reason', 'episode_reward', 'elapsed_steps', 'moves', 'path_cost',
             'arrival_step', 'obstacle_attempts', 'boundary_attempts', 'inference_time_seconds', 'episode_time_seconds')
    row = {name: result[name] for name in names}
    row['success'] = int(row['success'])
    row.update(seed=seed, phase=phase, training_episode=episode, optimal_moves=optimal_moves,
               optimality_gap=(result['moves'] - optimal_moves) / optimal_moves if result['success'] else None,
               actions_json=json.dumps(result['actions']), positions_json=json.dumps(result['positions']))
    return row


def source_hashes():
    files = [*sorted((ROOT / 'algorithms').glob('*.py')), *sorted((ROOT / 'environments').glob('*.py')),
             *sorted((ROOT / 'evaluation').glob('*.py')), Path(__file__).resolve()]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def run_training(config, output_root, *, make_plots=True):
    validate_config(config)
    # Snapshot caller data so saved config and execution use the same values.
    config = copy.deepcopy(config)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    started = perf_counter()
    stamp = datetime.now(timezone.utc)
    run_id = stamp.strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid4().hex[:8]
    directory = Path(output_root) / run_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'models').mkdir()
    (directory / 'paths').mkdir()
    (directory / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    metadata = {'run_id': run_id, 'purpose': config['purpose'], 'created_at_utc': stamp.isoformat(),
                'python': sys.version, 'platform': platform.platform(), 'processor': platform.processor(),
                'logical_cpus': os.cpu_count(), 'device': 'cpu', 'torch_threads': 1,
                'deterministic_algorithms': True,
                'versions': {name: importlib.metadata.version(name) for name in ('torch', 'numpy', 'matplotlib')},
                'source_sha256': source_hashes(), 'observation_version': OBSERVATION_VERSION,
                'observation_features': list(OBSERVATION_FEATURES),
                'task': 'finite horizon; both terminated and truncated mask bootstrap',
                'checkpoint_scope': 'inference restoration; optimizer/replay/RNG state not saved for training resume',
                'evaluation_scope': 'same deterministic training map; one greedy rollout per phase; not held out',
                'training_time': 'sum of episode wall times including env/updates/log writes; excludes evaluations, initialization, plots',
                'inference_time': 'greedy action calls only; excludes env transitions and training',
                'smoke': config['purpose'] == 'fixed_map_smoke'}
    (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    env = make_env(config)
    baseline_rows = []
    for name, search in (('bfs', bfs_result), ('dijkstra', dijkstra_result), ('astar', astar_result)):
        result = search(env.graph, env.start, env.goal)
        baseline_rows.append({'algorithm': name, 'moves': result.moves, 'path_cost': result.path_cost,
                              'expanded_nodes': result.expanded_nodes, 'planning_time_seconds': result.planning_time_seconds,
                              'path_json': json.dumps(result.path)})
    optimal_moves = baseline_rows[0]['moves']
    with (directory / 'baselines.csv').open('x', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(baseline_rows[0]))
        writer.writeheader()
        writer.writerows(baseline_rows)
    summaries = []
    with (directory / 'training_episodes.csv').open('x', newline='', encoding='utf-8') as ef, \
            (directory / 'optimizer_updates.csv').open('x', newline='', encoding='utf-8') as uf, \
            (directory / 'evaluations.csv').open('x', newline='', encoding='utf-8') as vf:
        episodes = csv.DictWriter(ef, fieldnames=EPISODE_FIELDS)
        updates = csv.DictWriter(uf, fieldnames=UPDATE_FIELDS)
        evaluations = csv.DictWriter(vf, fieldnames=EVALUATION_FIELDS)
        for writer in (episodes, updates, evaluations):
            writer.writeheader()
        for seed in config['seeds']:
            agent = DQNAgent(DQNConfig(**config['network']), seed=seed)
            replay = ReplayBuffer(config['replay_capacity'], seed=seed + 10000)
            before = evaluate_agent(agent, make_env(config), seed=seed)
            evaluations.writerow(evaluation_row(seed, 'untrained', 0, before, optimal_moves))
            steps, training_seconds = 0, 0.0
            for episode in range(1, config['episodes'] + 1):
                episode_started = perf_counter()
                epsilon = epsilon_at(episode - 1, config['epsilon_initial'], config['epsilon_final'], config['epsilon_decay_episodes'])
                observation, info = env.reset(seed=seed)
                components = {name: 0.0 for name in ('step', 'obstacle', 'boundary', 'goal')}
                losses = []
                while not (info['terminated'] or info['truncated']):
                    action = agent.act(observation, epsilon=epsilon)
                    following, reward, terminated, truncated, info = env.step(action)
                    replay.append(Transition(observation, action, reward, following, terminated, truncated))
                    observation = following
                    steps += 1
                    for name, value in info['reward_components'].items():
                        components[name] += value
                    if steps >= config['warmup_steps'] and steps % config['train_every_steps'] == 0:
                        metrics = agent.train_batch(replay.sample(config['batch_size']))
                        losses.append(metrics['loss'])
                        updates.writerow({'seed': seed, 'episode': episode, 'environment_steps': steps,
                                          'optimizer_update': agent.updates, 'loss': metrics['loss'],
                                          'gradient_norm_before_clip': metrics['gradient_norm_before_clip'],
                                          'target_synced': int(metrics['target_synced'])})
                episode_seconds = perf_counter() - episode_started
                training_seconds += episode_seconds
                row = {name: info[name] for name in ('success', 'failure_reason', 'episode_reward', 'elapsed_steps',
                                                     'moves', 'path_cost', 'arrival_step', 'obstacle_attempts', 'boundary_attempts')}
                row.update(seed=seed, episode=episode, epsilon=epsilon, success=int(info['success']),
                           environment_steps=steps, optimizer_updates=agent.updates,
                           mean_loss=sum(losses) / len(losses) if losses else None,
                           training_time_seconds=episode_seconds)
                row.update({name + '_reward': value for name, value in components.items()})
                episodes.writerow(row)
                if episode % config['evaluate_every_episodes'] == 0:
                    check = evaluate_agent(agent, make_env(config), seed=seed)
                    evaluations.writerow(evaluation_row(seed, 'progress', episode, check, optimal_moves))
                    ef.flush(); uf.flush(); vf.flush()
                    print(f"seed={seed} episode={episode}/{config['episodes']} greedy_success={check['success']} "
                          f"greedy_moves={check['moves']} updates={agent.updates}", flush=True)
            final = evaluate_agent(agent, make_env(config), seed=seed)
            evaluations.writerow(evaluation_row(seed, 'trained', config['episodes'], final, optimal_moves))
            model = directory / 'models' / f'seed_{seed}.pt'
            agent.save(model, metadata={'run_id': run_id, 'training_config': config, 'environment_steps': steps})
            loaded, _ = DQNAgent.load(model)
            after_reload = evaluate_agent(loaded, make_env(config), seed=seed)
            if any(not torch.equal(agent.q_values(obs), loaded.q_values(obs)) for obs in final['observations']):
                raise RuntimeError('Checkpoint reload changed Q-values')
            if final['actions'] != after_reload['actions'] or final['positions'] != after_reload['positions']:
                raise RuntimeError('Checkpoint reload changed greedy trajectory')
            evaluations.writerow(evaluation_row(seed, 'reloaded', config['episodes'], after_reload, optimal_moves))
            (directory / 'paths' / f'seed_{seed}.json').write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8')
            # Movement-only route strips waits/rejected attempts; unsuccessful views show no claimed path.
            route = [final['positions'][0]]
            for position in final['positions'][1:]:
                if position != route[-1]:
                    route.append(position)
            (directory / 'paths' / f'seed_{seed}.svg').write_text(render_svg(
                env.graph, env.start, env.goal, route if final['success'] else None, f'DQN final greedy route, seed {seed}'), encoding='utf-8')
            summaries.append({'seed': seed, 'episodes': config['episodes'], 'environment_steps': steps,
                              'optimizer_updates': agent.updates, 'training_time_seconds': training_seconds,
                              'untrained_success': before['success'], 'trained_success': final['success'],
                              'final_moves': final['moves'], 'final_arrival_step': final['arrival_step'],
                              'final_reward': final['episode_reward'], 'optimal_moves': optimal_moves,
                              'optimality_gap': (final['moves'] - optimal_moves) / optimal_moves if final['success'] else None,
                              'checkpoint_reload_matches': True})
    if make_plots:
        plot_run(directory, config['rolling_window'])
    summary = {'run_id': run_id, 'purpose': config['purpose'], 'seeds': summaries,
               'trained_success_fraction_across_seeds': sum(s['trained_success'] for s in summaries) / len(summaries),
               'run_time_seconds': perf_counter() - started,
               'interpretation': 'same fixed training map; development evidence, not unseen-map generalization'}
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (directory / 'COMPLETE.json').write_text(json.dumps({'seeds': len(summaries),
        'training_episode_rows': len(summaries) * config['episodes'], 'plots_generated': make_plots,
        'checkpoint_reload_verified': True}, indent=2) + '\n', encoding='utf-8')
    print(f'Completed DQN run: {directory}', flush=True)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/dqn_fixed.json')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'results/raw/dqn_fixed')
    parser.add_argument('--smoke', action='store_true', help='Explicit 20-episode, one-seed pipeline check; not full training')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if args.smoke:
        config.update(purpose='fixed_map_smoke', episodes=20, seeds=[config['seeds'][0]], evaluate_every_episodes=10)
    run_training(config, args.output_root)


if __name__ == '__main__':
    main()
