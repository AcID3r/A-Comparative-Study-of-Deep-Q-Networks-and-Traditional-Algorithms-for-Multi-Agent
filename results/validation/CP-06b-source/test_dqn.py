"""DQN checks use hand-computed targets and small CPU networks."""

import math
import random
import tempfile
import unittest
from pathlib import Path
import torch

from algorithms.dqn import DQNAgent, DQNConfig, ReplayBuffer, Transition, bellman_targets, epsilon_at

OBS = (0.,) * 13


class DQNTests(unittest.TestCase):
    def test_terminal_and_timeout_targets_ignore_next_values(self):
        result = bellman_targets(torch.tensor([1., 2., 3.]), torch.tensor([False, True, False]),
                                 torch.tensor([False, False, True]),
                                 torch.tensor([[4., 8.], [100., 200.], [300., 400.]]), .5)
        self.assertEqual(result.tolist(), [5., 2., 3.])
        self.assertFalse(result.requires_grad)

    def test_replay_capacity_and_seeded_sampling(self):
        a, b = ReplayBuffer(3, seed=7), ReplayBuffer(3, seed=7)
        for reward in range(5):
            item = Transition(OBS, 0, reward, OBS, False, False)
            a.append(item)
            b.append(item)
        self.assertEqual(len(a), 3)
        self.assertEqual(a.sample(3), b.sample(3))
        self.assertEqual({t.reward for t in a.sample(3)}, {2, 3, 4})
        with self.assertRaises(ValueError):
            a.sample(4)
        with self.assertRaises(ValueError):
            ReplayBuffer(0)

    def test_transitions_copy_observations_and_reject_bad_inputs(self):
        mutable = list(OBS)
        item = Transition(mutable, 0, 1, OBS, False, False)
        mutable[0] = 1
        self.assertEqual(item.observation, OBS)
        for args in ((OBS, True, 1, OBS, False, False), (OBS, 5, 1, OBS, False, False),
                     ((0.,), 0, 1, OBS, False, False), (OBS, 0, float('nan'), OBS, False, False),
                     (OBS, 0, 1, OBS, True, True)):
            with self.assertRaises(ValueError):
                Transition(*args)

    def test_epsilon_schedule_has_exact_endpoints_and_clamps(self):
        self.assertEqual(epsilon_at(0, 1, .05, 10), 1)
        self.assertAlmostEqual(epsilon_at(5, 1, .05, 10), .525)
        self.assertEqual(epsilon_at(10, 1, .05, 10), .05)
        self.assertEqual(epsilon_at(100, 1, .05, 10), .05)

    def test_network_shapes_and_seed_repeatability(self):
        a, b = DQNAgent(DQNConfig(hidden_sizes=(8, 8)), seed=4), DQNAgent(DQNConfig(hidden_sizes=(8, 8)), seed=4)
        self.assertEqual(tuple(a.online(torch.zeros(2, 13)).shape), (2, 5))
        self.assertTrue(torch.equal(a.q_values(OBS), b.q_values(OBS)))

    def test_greedy_action_uses_q_values_without_gradients(self):
        agent = DQNAgent(DQNConfig(hidden_sizes=(8, 8)), seed=0)
        with torch.no_grad():
            for parameter in agent.online.parameters():
                parameter.zero_()
            agent.online[-1].bias.copy_(torch.tensor([0., 1., 3., 2., -1.]))
        self.assertEqual(agent.act(OBS, epsilon=0), 2)
        self.assertFalse(agent.q_values(OBS).requires_grad)
        self.assertTrue(all(p.grad is None for p in agent.online.parameters()))
        with self.assertRaises(ValueError):
            agent.act(OBS, epsilon=1.1)

    def test_exploration_is_seeded_and_covers_actions(self):
        a, b = DQNAgent(DQNConfig(hidden_sizes=(8, 8)), seed=9), DQNAgent(DQNConfig(hidden_sizes=(8, 8)), seed=9)
        actions = [a.act(OBS, epsilon=1) for _ in range(100)]
        self.assertEqual(actions, [b.act(OBS, epsilon=1) for _ in range(100)])
        self.assertEqual(set(actions), set(range(5)))

    def test_training_changes_online_and_syncs_target_on_update_schedule(self):
        agent = DQNAgent(DQNConfig(hidden_sizes=(8, 8), target_update_steps=2), seed=1)
        batch = [Transition(OBS, 1, 10, OBS, True, False)] * 4
        initial = [p.clone() for p in agent.online.parameters()]
        first = agent.train_batch(batch)
        self.assertTrue(math.isfinite(first['loss']))
        self.assertFalse(first['target_synced'])
        self.assertTrue(any(not torch.equal(x, y) for x, y in zip(initial, agent.online.parameters())))
        self.assertTrue(all(torch.equal(x, y) for x, y in zip(initial, agent.target.parameters())))
        second = agent.train_batch(batch)
        self.assertTrue(second['target_synced'])
        self.assertTrue(all(torch.equal(x, y) for x, y in zip(agent.online.parameters(), agent.target.parameters())))
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in agent.target.parameters()))

    def test_saved_checkpoint_restores_predictions_and_refuses_overwrite(self):
        agent = DQNAgent(DQNConfig(hidden_sizes=(8, 8)), seed=3)
        agent.train_batch([Transition(OBS, 1, 3, OBS, True, False)])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'model.pt'
            agent.save(path, metadata={'purpose': 'test'})
            loaded, metadata = DQNAgent.load(path)
            self.assertTrue(torch.equal(agent.q_values(OBS), loaded.q_values(OBS)))
            self.assertEqual(loaded.updates, agent.updates)
            self.assertEqual(metadata, {'purpose': 'test'})
            with self.assertRaises(FileExistsError):
                agent.save(path)

    def test_incompatible_feature_layout_is_rejected_on_load(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.pt'
            DQNAgent(DQNConfig(hidden_sizes=(8, 8))).save(path)
            payload = torch.load(path, weights_only=True)
            payload['observation_features'][0] = 'wrong_feature'
            torch.save(payload, path)
            with self.assertRaises(ValueError):
                DQNAgent.load(path)

    def test_invalid_config_values_are_rejected(self):
        for values in ({'gamma': 1.1}, {'learning_rate': 0}, {'hidden_sizes': (0, 8)},
                       {'target_update_steps': True}, {'gradient_clip': float('inf')}):
            with self.assertRaises(ValueError):
                DQNConfig(**values)


if __name__ == '__main__':
    unittest.main()
