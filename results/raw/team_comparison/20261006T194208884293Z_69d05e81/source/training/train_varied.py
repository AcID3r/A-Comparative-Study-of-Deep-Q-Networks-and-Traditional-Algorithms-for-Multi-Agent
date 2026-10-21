"""Random static-map training with held-out validation; no test-map feedback."""

import argparse
import csv
import json
from pathlib import Path
import random
from time import perf_counter

import torch
from algorithms.dqn import DQNAgent, DQNConfig, ReplayBuffer, Transition, epsilon_at
from environments.random_maps import make_scenario_env
from evaluation.evaluate_dqn import evaluate_agent
from evaluation.varied_protocol import ROOT, generate_bank, new_run
from training.train_dqn import EPISODE_FIELDS, UPDATE_FIELDS


def validation_rollouts(agent, config, scenarios):
    return [{'map_id': scenario['map_id'], 'map_seed': scenario['map_seed'],
             'initial_reachable': scenario['initial_reachable'],
             'rollout': evaluate_agent(agent, make_scenario_env(scenario, max_steps=config['map_spec']['max_steps']), seed=scenario['map_seed'])}
            for scenario in scenarios]


def run_training(config, output_root, *, make_plots=True):
    bank = generate_bank(config)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    directory = new_run(output_root, config, bank, config['purpose'])
    (directory / 'models').mkdir()
    train_maps, val_maps = bank['partitions']['train'], bank['partitions']['validation']
    summaries = []
    fields = EPISODE_FIELDS + ['map_id', 'map_seed', 'initial_reachable']
    with (directory / 'training_episodes.csv').open('x', newline='', encoding='utf-8') as ef, \
            (directory / 'optimizer_updates.csv').open('x', newline='', encoding='utf-8') as uf, \
            (directory / 'validation.jsonl').open('x', encoding='utf-8') as vf:
        episodes, updates = csv.DictWriter(ef, fieldnames=fields), csv.DictWriter(uf, fieldnames=UPDATE_FIELDS)
        episodes.writeheader(); updates.writeheader()
        for seed in config['seeds']:
            agent = DQNAgent(DQNConfig(**config['network']), seed=seed)
            replay = ReplayBuffer(config['replay_capacity'], seed=seed + 10000)
            map_rng = random.Random(seed + 20000)
            steps, training_seconds = 0, 0.0
            for episode in range(1, config['episodes'] + 1):
                started = perf_counter()
                scenario = train_maps[map_rng.randrange(len(train_maps))]
                env = make_scenario_env(scenario, max_steps=config['map_spec']['max_steps'])
                observation, info = env.reset(seed=scenario['map_seed'])
                epsilon = epsilon_at(episode - 1, config['epsilon_initial'], config['epsilon_final'], config['epsilon_decay_episodes'])
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
                            'gradient_norm_before_clip': metrics['gradient_norm_before_clip'], 'target_synced': int(metrics['target_synced'])})
                duration = perf_counter() - started
                training_seconds += duration
                row = {key: info[key] for key in ('success', 'failure_reason', 'episode_reward', 'elapsed_steps',
                    'moves', 'path_cost', 'arrival_step', 'obstacle_attempts', 'boundary_attempts')}
                row.update(seed=seed, episode=episode, epsilon=epsilon, success=int(info['success']),
                    environment_steps=steps, optimizer_updates=agent.updates,
                    mean_loss=sum(losses) / len(losses) if losses else None, training_time_seconds=duration,
                    map_id=scenario['map_id'], map_seed=scenario['map_seed'], initial_reachable=int(scenario['initial_reachable']))
                row.update({name + '_reward': value for name, value in components.items()})
                episodes.writerow(row)
                if episode % config['evaluate_every_episodes'] == 0:
                    checks = validation_rollouts(agent, config, val_maps)
                    vf.write(json.dumps({'seed': seed, 'episode': episode, 'cases': checks}) + '\n')
                    ef.flush(); uf.flush(); vf.flush()
                    rate = sum(c['rollout']['success'] for c in checks) / len(checks)
                    print(f'seed={seed} episode={episode}/{config["episodes"]} validation_success={rate:.3f} updates={agent.updates}', flush=True)
            checks = validation_rollouts(agent, config, val_maps)
            vf.write(json.dumps({'seed': seed, 'episode': config['episodes'], 'phase': 'final', 'cases': checks}) + '\n')
            model = directory / 'models' / f'seed_{seed}.pt'
            agent.save(model, metadata={'training_config': config, 'map_bank_file': 'map_bank.json', 'environment_steps': steps})
            reloaded, _ = DQNAgent.load(model)
            again = validation_rollouts(reloaded, config, val_maps)
            if any(a['rollout']['actions'] != b['rollout']['actions'] for a, b in zip(checks, again)):
                raise RuntimeError('Reload changed validation trajectories')
            summaries.append({'seed': seed, 'episodes': config['episodes'], 'environment_steps': steps,
                'optimizer_updates': agent.updates, 'training_time_seconds': training_seconds,
                'validation_successes': sum(c['rollout']['success'] for c in checks),
                'validation_episodes': len(checks), 'reload_matches': True})
    if make_plots:
        plot_varied(directory, config['rolling_window'])
    (directory / 'summary.json').write_text(json.dumps(summaries, indent=2) + '\n', encoding='utf-8')
    (directory / 'COMPLETE.json').write_text(json.dumps({'training_episode_rows': len(config['seeds']) * config['episodes'],
        'seeds': len(config['seeds']), 'plots_generated': make_plots, 'test_maps_used': False}, indent=2) + '\n', encoding='utf-8')
    print(f'Random-map training saved: {directory}', flush=True)
    return directory


def plot_varied(directory, window):
    import os
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    with (directory / 'training_episodes.csv').open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    figures = directory / 'figures'
    figures.mkdir()
    for metric, label in (('episode_reward', 'Training return'), ('success', 'Training success fraction'), ('mean_loss', 'Mean episode MSE')):
        fig, ax = plt.subplots(figsize=(9, 5), layout='constrained')
        for seed in sorted({r['seed'] for r in rows}, key=int):
            group = [r for r in rows if r['seed'] == seed]
            values = [float(r[metric]) if r[metric] else None for r in group]
            means = []
            for i in range(len(group)):
                selected = [v for v in values[max(0, i-window+1):i+1] if v is not None]
                means.append(sum(selected)/len(selected) if selected else float('nan'))
            ax.plot([int(r['episode']) for r in group], means, label=f'Seed {seed}')
        ax.set(xlabel='Training episode', ylabel=label, title=f'Random training maps; trailing window {window}')
        ax.legend(); ax.grid(alpha=.2)
        for suffix in ('png', 'svg'):
            fig.savefig(figures / f'{metric}.{suffix}', dpi=160)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/dqn_varied.json')
    parser.add_argument('--output-root', type=Path, default=ROOT / 'results/raw/dqn_varied')
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if args.smoke:
        config.update(purpose='random_map_smoke', episodes=20, seeds=[config['seeds'][0]], evaluate_every_episodes=10)
    run_training(config, args.output_root)


if __name__ == '__main__':
    main()
