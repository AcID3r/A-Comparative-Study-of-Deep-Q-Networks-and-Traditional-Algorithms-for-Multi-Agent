"""Read-only audit of saved DQN outputs: python -m evaluation.audit_dqn_run RUN_DIR."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import torch
from algorithms.dqn import DQNAgent, epsilon_at
from evaluation.evaluate_dqn import evaluate_agent
from training.train_dqn import make_env, validate_config


def csv_rows(path):
    with path.open(newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))


def audit_run(directory):
    directory = Path(directory)
    config = json.loads((directory / 'config.json').read_text(encoding='utf-8'))
    validate_config(config)
    completed = json.loads((directory / 'COMPLETE.json').read_text(encoding='utf-8'))
    metadata = json.loads((directory / 'metadata.json').read_text(encoding='utf-8'))
    root = Path(__file__).resolve().parents[1]
    for file, digest in metadata['source_sha256'].items():
        if hashlib.sha256((root / file).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Source changed since recorded run: {file}')
    episodes = csv_rows(directory / 'training_episodes.csv')
    updates = csv_rows(directory / 'optimizer_updates.csv')
    evaluations = csv_rows(directory / 'evaluations.csv')
    assert len(episodes) == len(config['seeds']) * config['episodes'] == completed['training_episode_rows']
    summaries = json.loads((directory / 'summary.json').read_text(encoding='utf-8'))
    assert len(summaries['seeds']) == len(config['seeds'])
    final_checks = []
    torch.set_num_threads(1)
    for seed in config['seeds']:
        records = [r for r in episodes if int(r['seed']) == seed]
        gradient_records = [r for r in updates if int(r['seed']) == seed]
        assert [int(r['episode']) for r in records] == list(range(1, config['episodes'] + 1))
        elapsed = 0
        for row in records:
            elapsed += int(row['elapsed_steps'])
            success = int(row['success'])
            assert success in (0, 1)
            assert 0 <= int(row['moves']) <= int(row['elapsed_steps']) <= config['map']['max_steps']
            assert float(row['path_cost']) == int(row['moves'])
            expected_reward = 100 * success - int(row['elapsed_steps']) - 10 * int(row['obstacle_attempts']) - 5 * int(row['boundary_attempts'])
            assert float(row['episode_reward']) == expected_reward
            assert sum(float(row[k + '_reward']) for k in ('step', 'obstacle', 'boundary', 'goal')) == expected_reward
            assert row['arrival_step'] == (row['elapsed_steps'] if success else '')
            assert row['failure_reason'] == ('' if success else 'time_limit')
            assert int(row['environment_steps']) == elapsed
            expected_updates = max(0, elapsed // config['train_every_steps'] - (config['warmup_steps'] - 1) // config['train_every_steps'])
            assert int(row['optimizer_updates']) == expected_updates
            assert math.isclose(float(row['epsilon']), epsilon_at(int(row['episode']) - 1,
                config['epsilon_initial'], config['epsilon_final'], config['epsilon_decay_episodes']), abs_tol=1e-12)
            assert math.isfinite(float(row['training_time_seconds'])) and float(row['training_time_seconds']) >= 0
        assert len(gradient_records) == int(records[-1]['optimizer_updates'])
        assert [int(r['optimizer_update']) for r in gradient_records] == list(range(1, len(gradient_records) + 1))
        for row in gradient_records:
            assert math.isfinite(float(row['loss'])) and float(row['loss']) >= 0
            assert math.isfinite(float(row['gradient_norm_before_clip']))
            assert int(row['target_synced']) == int(int(row['optimizer_update']) % config['network']['target_update_steps'] == 0)
        seed_eval = [r for r in evaluations if int(r['seed']) == seed]
        assert len(seed_eval) == config['episodes'] // config['evaluate_every_episodes'] + 3
        final = next(r for r in seed_eval if r['phase'] == 'trained')
        reloaded = next(r for r in seed_eval if r['phase'] == 'reloaded')
        assert final['actions_json'] == reloaded['actions_json']
        agent, stored_metadata = DQNAgent.load(directory / 'models' / f'seed_{seed}.pt')
        assert stored_metadata['training_config'] == config
        result = evaluate_agent(agent, make_env(config), seed=seed)
        assert int(result['success']) == int(final['success'])
        assert result['actions'] == json.loads(final['actions_json'])
        assert [list(p) for p in result['positions']] == json.loads(final['positions_json'])
        trace = json.loads((directory / 'paths' / f'seed_{seed}.json').read_text(encoding='utf-8'))
        assert trace['actions'] == result['actions']
        summary = next(s for s in summaries['seeds'] if s['seed'] == seed)
        assert summary['trained_success'] == result['success']
        assert summary['environment_steps'] == elapsed
        assert summary['optimizer_updates'] == len(gradient_records)
        assert math.isclose(summary['training_time_seconds'], sum(float(r['training_time_seconds']) for r in records))
        for row in seed_eval:
            for key in ('inference_time_seconds', 'episode_time_seconds'):
                assert math.isfinite(float(row[key])) and float(row[key]) >= 0
            assert float(row['episode_time_seconds']) >= float(row['inference_time_seconds'])
            if not int(row['success']):
                assert row['optimality_gap'] == '' and row['arrival_step'] == ''
        ET.parse(directory / 'paths' / f'seed_{seed}.svg')
        final_checks.append({'seed': seed, 'success': result['success'], 'moves': result['moves'],
                             'arrival_step': result['arrival_step'], 'episode_reward': result['episode_reward']})
    if completed['plots_generated']:
        for name in ('reward', 'success', 'loss'):
            ET.parse(directory / 'figures' / f'{name}.svg')
            assert (directory / 'figures' / f'{name}.png').read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
    return {'run_directory': str(directory.resolve()), 'training_episode_rows': len(episodes),
            'optimizer_update_rows': len(updates), 'evaluation_rows': len(evaluations),
            'seed_results': final_checks, 'source_hashes_match': True,
            'checkpoint_trajectories_match': True, 'reward_and_counter_checks_passed': True,
            'scope': 'same fixed training map; no generalization claim'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--output', type=Path, help='Save audit report to a new file, outside measured raw files')
    args = parser.parse_args()
    result = audit_run(args.run_directory)
    if args.output:
        with args.output.open('x', encoding='utf-8') as file:
            json.dump(result, file, indent=2)
            file.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
