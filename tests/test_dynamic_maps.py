"""CP-05 maps and changes: expected behavior before implementation."""

import unittest
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action
from environments.dynamic_env import DynamicSingleAgentEnv, ObstacleChange
from environments.random_maps import build_bank


class DynamicMapTests(unittest.TestCase):
    def test_partitions_repeat_and_have_no_shared_geometry(self):
        a = build_bank(5, 5, .15, {'train': (1000, 5), 'validation': (2000, 3), 'test': (3000, 4)})
        b = build_bank(5, 5, .15, {'train': (1000, 5), 'validation': (2000, 3), 'test': (3000, 4)})
        self.assertEqual(a, b)
        ids = [m['map_id'] for maps in a['partitions'].values() for m in maps]
        self.assertEqual(len(ids), len(set(ids)))
        for maps in a['partitions'].values():
            for m in maps:
                walls = {tuple(p) for p in m['obstacles']}
                self.assertNotIn((0, 0), walls)
                self.assertNotIn((4, 4), walls)

    def test_overlapping_seed_ranges_and_insufficient_unique_geometry_are_rejected(self):
        with self.assertRaises(ValueError):
            build_bank(5, 5, .15, {'train': (1000, 2), 'test': (1000, 1)})
        with self.assertRaises(ValueError):
            build_bank(1, 2, 0, {'train': (1000, 2)})

    def test_changes_are_visible_before_the_action_and_observation_is_idempotent(self):
        env = DynamicSingleAgentEnv(GridGraph(2, 3), (0, 0), (0, 2), max_steps=5,
                                    schedule=[ObstacleChange(1, (0, 1), 'add'), ObstacleChange(2, (0, 1), 'remove')])
        observation, info = env.reset()
        self.assertEqual(observation[7], 1)
        self.assertEqual(len(info['change_history']), 1)
        env.observe(); env.observe()
        _, reward, _, _, info = env.step(Action.RIGHT)
        self.assertEqual(reward, -11)
        self.assertEqual(info['position'], (0, 0))
        self.assertEqual(info['action_graph_version'], 1)
        self.assertEqual(len(info['change_history']), 2)
        self.assertEqual(env.observe()[7], 0)
        _, reward, _, _, info = env.step(Action.RIGHT)
        self.assertEqual(info['position'], (0, 1))
        self.assertEqual(reward, -1)

    def test_occupied_addition_is_rejected_and_logged(self):
        env = DynamicSingleAgentEnv(GridGraph(2, 3), (0, 0), (0, 2), max_steps=5,
                                    schedule=[ObstacleChange(2, (0, 1), 'add')])
        env.reset()
        _, _, _, _, info = env.step(Action.RIGHT)
        self.assertTrue(env.graph.is_free((0, 1)))
        self.assertEqual(info['change_history'][0]['status'], 'rejected_occupied')

    def test_endpoints_bad_events_and_duplicate_events_are_rejected(self):
        for schedule in ([ObstacleChange(1, (0, 0), 'add')], [ObstacleChange(1, (0, 2), 'add')],
                         [ObstacleChange(1, (3, 0), 'add')], [ObstacleChange(6, (0, 1), 'add')],
                         [ObstacleChange(1, (0, 1), 'add'), ObstacleChange(1, (0, 1), 'remove')]):
            with self.assertRaises(ValueError):
                DynamicSingleAgentEnv(GridGraph(2, 3), (0, 0), (0, 2), max_steps=5, schedule=schedule)
        with self.assertRaises(ValueError):
            ObstacleChange(0, (0, 1), 'add')
        with self.assertRaises(ValueError):
            ObstacleChange(1, (0, 1), 'move')

    def test_reset_restores_initial_map_and_replays_same_changes(self):
        env = DynamicSingleAgentEnv(GridGraph(2, 3), (0, 0), (0, 2), max_steps=5,
                                    schedule=[ObstacleChange(1, (0, 1), 'add'), ObstacleChange(2, (0, 1), 'remove')])
        first = env.reset(seed=7)
        transition = env.step(Action.WAIT)
        self.assertEqual(env.reset(seed=7), first)
        self.assertEqual(env.step(Action.WAIT), transition)

    def test_future_events_do_not_fire_after_termination(self):
        env = DynamicSingleAgentEnv(GridGraph(2, 3), (0, 0), (0, 1), max_steps=5,
                                    schedule=[ObstacleChange(2, (1, 1), 'add')])
        env.reset()
        _, _, terminated, _, info = env.step(Action.RIGHT)
        self.assertTrue(terminated)
        self.assertEqual(info['change_history'], [])


if __name__ == '__main__':
    unittest.main()
