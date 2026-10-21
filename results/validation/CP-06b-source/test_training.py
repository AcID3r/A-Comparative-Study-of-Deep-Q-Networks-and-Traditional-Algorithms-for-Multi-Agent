"""Tiny pipeline tests use temporary outputs and make no learning claims."""

import copy
import csv
import json
import math
from pathlib import Path
import tempfile
import unittest

from algorithms.dqn import DQNAgent
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action, SingleAgentEnv
from evaluation.evaluate_dqn import evaluate_agent
from training.train_dqn import run_training


def config():
    value = json.loads(Path('configs/dqn_fixed.json').read_text(encoding='utf-8'))
    value.update(episodes=4, seeds=[7], batch_size=4, replay_capacity=32,
                 warmup_steps=4, train_every_steps=1, epsilon_decay_episodes=2,
                 evaluate_every_episodes=2, rolling_window=2, purpose='fixed_map_smoke')
    value['network'].update(hidden_sizes=[8, 8], target_update_steps=2)
    value['map'] = {'rows': 2, 'cols': 2, 'obstacles': [], 'start': [0, 0], 'goal': [1, 1], 'max_steps': 4}
    return value


class WaitPolicy:
    def act(self, observation, *, epsilon):
        assert epsilon == 0
        return Action.WAIT


class TrainingTests(unittest.TestCase):
    def test_greedy_timeout_keeps_missing_arrival_and_counts_only_action_time(self):
        result = evaluate_agent(WaitPolicy(), SingleAgentEnv(GridGraph(1, 2), (0, 0), (0, 1), max_steps=3))
        self.assertFalse(result['success'])
        self.assertTrue(result['truncated'])
        self.assertIsNone(result['arrival_step'])
        self.assertEqual(result['moves'], 0)
        self.assertEqual(result['episode_reward'], -3)
        self.assertEqual(len(result['actions']), 3)
        self.assertGreaterEqual(result['inference_time_seconds'], 0)
        self.assertGreaterEqual(result['episode_time_seconds'], result['inference_time_seconds'])

    def test_start_at_goal_evaluation_requires_no_action_calls(self):
        result = evaluate_agent(WaitPolicy(), SingleAgentEnv(GridGraph(1, 1), (0, 0), (0, 0)))
        self.assertTrue(result['success'])
        self.assertEqual(result['actions'], [])
        self.assertEqual(result['inference_time_seconds'], 0)

    def test_training_pipeline_logs_real_metrics_and_reload(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = run_training(config(), folder, make_plots=True)
            with (directory / 'training_episodes.csv').open(newline='', encoding='utf-8') as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 4)
            for row in rows:
                parts = [float(row[name + '_reward']) for name in ('step', 'obstacle', 'boundary', 'goal')]
                self.assertEqual(sum(parts), float(row['episode_reward']))
                self.assertEqual(float(row['step_reward']), -int(row['elapsed_steps']))
                self.assertEqual(float(row['obstacle_reward']), -10 * int(row['obstacle_attempts']))
                self.assertEqual(float(row['boundary_reward']), -5 * int(row['boundary_attempts']))
                self.assertEqual(float(row['goal_reward']), 100 * int(row['success']))
            with (directory / 'optimizer_updates.csv').open(newline='', encoding='utf-8') as file:
                updates = list(csv.DictReader(file))
            self.assertGreater(len(updates), 0)
            self.assertTrue(all(math.isfinite(float(row['loss'])) for row in updates))
            for row in updates:
                self.assertEqual(int(row['target_synced']), int(row['optimizer_update']) % 2 == 0)
            with (directory / 'evaluations.csv').open(newline='', encoding='utf-8') as file:
                evaluation = list(csv.DictReader(file))
            self.assertEqual(len(evaluation), 5)  # before, two progress, final, reload
            trained = next(r for r in evaluation if r['phase'] == 'trained')
            reloaded = next(r for r in evaluation if r['phase'] == 'reloaded')
            self.assertEqual(trained['actions_json'], reloaded['actions_json'])
            self.assertEqual(trained['success'], reloaded['success'])
            _, metadata = DQNAgent.load(directory / 'models/seed_7.pt')
            self.assertEqual(metadata['training_config'], config())
            for metric in ('reward', 'success', 'loss'):
                self.assertTrue((directory / 'figures' / f'{metric}.png').is_file())
                self.assertTrue((directory / 'figures' / f'{metric}.svg').is_file())
            self.assertTrue(json.loads((directory / 'COMPLETE.json').read_text())['checkpoint_reload_verified'])

    def test_fixed_seed_repeats_training_and_preserves_prior_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            a = run_training(config(), folder, make_plots=False)
            original = (a / 'training_episodes.csv').read_bytes()
            b = run_training(config(), folder, make_plots=False)
            self.assertNotEqual(a, b)
            self.assertEqual((a / 'training_episodes.csv').read_bytes(), original)
            def records(directory):
                with (directory / 'training_episodes.csv').open(newline='', encoding='utf-8') as f:
                    return [{k: v for k, v in row.items() if k != 'training_time_seconds'} for row in csv.DictReader(f)]
            self.assertEqual(records(a), records(b))

    def test_invalid_training_configs_create_no_run(self):
        variants = [{'episodes': 0}, {'seeds': [1, 1]}, {'batch_size': 100},
                    {'epsilon_final': 1.1}, {'extra': True}, {'network': {'gamma': .9}}]
        with tempfile.TemporaryDirectory() as folder:
            for change in variants:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    run_training(config() | change, folder, make_plots=False)
            self.assertEqual(list(Path(folder).iterdir()), [])


if __name__ == '__main__':
    unittest.main()
