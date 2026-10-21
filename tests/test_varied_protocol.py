"""Tiny CP-05 pipelines: disjoint splits, real updates and trace replay."""

import csv
import json
from pathlib import Path
import tempfile
import unittest

from experiments.run_transfer import run_evaluation
from training.train_varied import run_training
from evaluation.varied_protocol import ROOT, generate_bank
from environments.random_maps import map_id


def tiny_config():
    config = json.loads((ROOT / 'configs/dqn_varied.json').read_text(encoding='utf-8'))
    config.update(purpose='random_map_smoke', seeds=[0], episodes=2, batch_size=4,
                  warmup_steps=4, replay_capacity=32, train_every_steps=1,
                  evaluate_every_episodes=1, epsilon_decay_episodes=2)
    config['partitions'] = {'train': [1000, 3], 'validation': [2000, 2], 'test': [3000, 2]}
    config['map_spec']['max_steps'] = 10
    config['network'].update(hidden_sizes=[8, 8], target_update_steps=2)
    return config


class VariedProtocolTests(unittest.TestCase):
    def test_training_rows_use_training_maps_only_and_reload_works(self):
        with tempfile.TemporaryDirectory() as folder:
            config = tiny_config()
            directory = run_training(config, folder, make_plots=False)
            bank = json.loads((directory / 'map_bank.json').read_text())
            allowed = {m['map_id'] for m in bank['partitions']['train']}
            with (directory / 'training_episodes.csv').open(newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(r['map_id'] in allowed for r in rows))
            validations = [json.loads(line) for line in (directory / 'validation.jsonl').read_text().splitlines()]
            self.assertEqual(len(validations), 3)
            self.assertTrue(all(c['map_id'] in {m['map_id'] for m in bank['partitions']['validation']}
                                for v in validations for c in v['cases']))
            completed = json.loads((directory / 'COMPLETE.json').read_text())
            self.assertFalse(completed['test_maps_used'])
            self.assertTrue(json.loads((directory / 'summary.json').read_text())[0]['reload_matches'])
            evaluation = run_evaluation(config, folder, varied_run=directory)
            with (evaluation / 'raw_results.csv').open(newline='') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 28)  # 2 maps * 2 conditions * (4 classical + 3 policies)
            self.assertEqual({r['method'] for r in rows}, {'bfs', 'dijkstra', 'astar', 'astar_frozen', 'dqn_fixed', 'dqn_untrained', 'dqn_varied'})
            self.assertTrue(all(r['rejected_changes'] == '0' for r in rows))
            self.assertTrue(all(r['static_move_gap'] == '' for r in rows if r['condition'] == 'dynamic'))
            traces = [json.loads(line) for line in (evaluation / 'trajectories.jsonl').read_text().splitlines()]
            self.assertEqual(len(traces), len(rows))

    def test_invalid_density_creates_no_output(self):
        with tempfile.TemporaryDirectory() as folder:
            config = tiny_config()
            config['map_spec']['density'] = -1
            with self.assertRaises(ValueError):
                run_training(config, folder, make_plots=False)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_default_bank_keeps_unreachable_maps_and_excludes_fixed_training_geometry(self):
        bank = generate_bank(json.loads((ROOT / 'configs/dqn_varied.json').read_text()))
        self.assertEqual([len(group) for group in bank['partitions'].values()], [100, 10, 50])
        identities = [m['map_id'] for group in bank['partitions'].values() for m in group]
        self.assertEqual(len(identities), len(set(identities)))
        fixed = json.loads((ROOT / 'results/raw/dqn_fixed/20261006T103855437859Z_d455330a/config.json').read_text())['map']
        self.assertNotIn(map_id(fixed['rows'], fixed['cols'], fixed['obstacles']), identities)
        self.assertTrue(any(not m['initial_reachable'] for group in bank['partitions'].values() for m in group))


if __name__ == '__main__':
    unittest.main()
