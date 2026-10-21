"""Hand-checkable transition/reward and baseline replay tests for CP-03."""

import math
import random
import unittest

from algorithms.bfs import bfs
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action, OBSERVATION_FEATURES, SingleAgentEnv


class SingleAgentEnvTests(unittest.TestCase):
    def make_env(self, graph=None, start=(1, 1), goal=(2, 2), max_steps=10):
        return SingleAgentEnv(graph or GridGraph(3, 3), start, goal, max_steps=max_steps)

    def test_step_requires_reset(self):
        with self.assertRaises(RuntimeError):
            self.make_env().step(Action.UP)
        with self.assertRaises(RuntimeError):
            self.make_env().observe()

    def test_reset_after_goal_or_timeout_starts_fresh_episode(self):
        for action in (Action.RIGHT, Action.WAIT):
            env = SingleAgentEnv(GridGraph(1, 2), (0, 0), (0, 1), max_steps=1)
            env.reset(seed=5)
            env.step(action)
            observation, info = env.reset(seed=6)
            self.assertFalse(info['terminated'] or info['truncated'])
            self.assertFalse(info['success'])
            self.assertEqual(info['elapsed_steps'], 0)
            self.assertEqual(info['episode_reward'], 0)
            self.assertEqual(info['position'], (0, 0))
            self.assertEqual(observation[-1], 1)
            self.assertEqual(env.step(Action.RIGHT)[1], 99)

    def test_reset_restores_state_and_same_seed_replays_episode(self):
        env = self.make_env()
        first = env.reset(seed=7)
        episode = [env.step(action) for action in (Action.UP, Action.LEFT, Action.WAIT)]
        self.assertEqual(env.reset(seed=7), first)
        self.assertEqual([env.step(a) for a in (Action.UP, Action.LEFT, Action.WAIT)], episode)
        _, info = env.reset()
        self.assertEqual(info['elapsed_steps'], 0)
        self.assertEqual(info['moves'], 0)
        self.assertEqual(info['episode_reward'], 0)
        self.assertIsNone(info['arrival_step'])

    def test_all_four_directions(self):
        for action, expected in ((Action.UP, (0, 1)), (Action.DOWN, (2, 1)),
                                 (Action.LEFT, (1, 0)), (Action.RIGHT, (1, 2))):
            with self.subTest(action=action):
                env = self.make_env()
                env.reset()
                _, reward, terminated, truncated, info = env.step(action)
                self.assertEqual(info['position'], expected)
                self.assertEqual(reward, -1)
                self.assertFalse(terminated or truncated)
                self.assertEqual(info['moves'], 1)
                self.assertEqual(info['path_cost'], 1)
                self.assertTrue(info['executed_move'])

    def test_wait_consumes_time_but_not_moves(self):
        env = self.make_env()
        env.reset()
        _, reward, _, _, info = env.step(Action.WAIT)
        self.assertEqual(info['position'], (1, 1))
        self.assertEqual(info['elapsed_steps'], 1)
        self.assertEqual(info['moves'], 0)
        self.assertEqual(info['path_cost'], 0)
        self.assertEqual(reward, -1)
        self.assertEqual(info['event'], 'wait')

    def test_obstacle_attempt_stays_put_with_separate_penalty(self):
        env = self.make_env(GridGraph(3, 3, {(0, 1)}))
        env.reset()
        _, reward, _, _, info = env.step(Action.UP)
        self.assertEqual(reward, -11)
        self.assertEqual(info['position'], (1, 1))
        self.assertEqual(info['requested_position'], (0, 1))
        self.assertEqual(info['obstacle_attempts'], 1)
        self.assertEqual(info['boundary_attempts'], 0)
        self.assertEqual(info['reward_components'], {'step': -1., 'obstacle': -10., 'boundary': 0., 'goal': 0.})
        self.assertFalse(info['executed_move'])

    def test_boundary_attempt_is_not_obstacle_attempt(self):
        env = self.make_env(start=(0, 0))
        env.reset()
        _, reward, _, _, info = env.step(Action.LEFT)
        self.assertEqual(reward, -6)
        self.assertEqual(info['position'], (0, 0))
        self.assertEqual(info['moves'], 0)
        self.assertEqual(info['boundary_attempts'], 1)
        self.assertEqual(info['obstacle_attempts'], 0)
        self.assertEqual(info['elapsed_steps'], 1)

    def test_arrival_has_one_goal_bonus_and_no_team_bonus(self):
        env = self.make_env(goal=(1, 2))
        env.reset()
        _, reward, terminated, truncated, info = env.step(Action.RIGHT)
        self.assertEqual(reward, 99)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertTrue(info['success'])
        self.assertEqual(info['arrival_step'], 1)
        self.assertEqual(info['reward_components']['goal'], 100)
        with self.assertRaises(RuntimeError):
            env.step(Action.WAIT)
        self.assertEqual(env.position, (1, 2))

    def test_timeout_is_failure_not_goal_termination(self):
        env = self.make_env(max_steps=2)
        env.reset()
        env.step(Action.WAIT)
        observation, reward, terminated, truncated, info = env.step(Action.WAIT)
        self.assertFalse(terminated)
        self.assertTrue(truncated)
        self.assertFalse(info['success'])
        self.assertEqual(info['failure_reason'], 'time_limit')
        self.assertIsNone(info['arrival_step'])
        self.assertEqual(observation[-1], 0)
        self.assertEqual(reward, -1)
        with self.assertRaises(RuntimeError):
            env.step(Action.UP)

    def test_arrival_on_last_allowed_step_is_success(self):
        env = self.make_env(goal=(1, 2), max_steps=1)
        env.reset()
        _, _, terminated, truncated, info = env.step(Action.RIGHT)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertTrue(info['success'])

    def test_start_at_goal_finishes_at_reset_without_reward(self):
        env = self.make_env(start=(1, 1), goal=(1, 1))
        _, info = env.reset()
        self.assertTrue(info['terminated'])
        self.assertTrue(info['success'])
        self.assertEqual(info['arrival_step'], 0)
        self.assertEqual(info['episode_reward'], 0)
        self.assertEqual(info['reward_components']['goal'], 0)
        with self.assertRaises(RuntimeError):
            env.step(Action.WAIT)

    def test_observation_has_fixed_order_and_distinguishes_wall_boundary(self):
        env = self.make_env(GridGraph(3, 5, {(0, 1)}), start=(0, 0), goal=(2, 4), max_steps=4)
        observation, _ = env.reset(seed=0)
        self.assertEqual(len(OBSERVATION_FEATURES), 13)
        self.assertEqual(observation, (0., 0., 1., 1., 0., 0., 0., 1., 1., 0., 1., 0., 1.))
        after, _, _, _, _ = env.step(Action.DOWN)
        self.assertEqual(after[:4], (.5, 0., .5, 1.))
        self.assertEqual(after[-1], .75)

    def test_degenerate_dimensions_have_finite_normalized_observations(self):
        for graph, start, goal in ((GridGraph(1, 1), (0, 0), (0, 0)),
                                   (GridGraph(1, 3), (0, 0), (0, 2)),
                                   (GridGraph(3, 1), (2, 0), (0, 0))):
            env = SingleAgentEnv(graph, start, goal, max_steps=5)
            obs, _ = env.reset()
            self.assertTrue(all(math.isfinite(x) and -1 <= x <= 1 for x in obs))

    def test_invalid_actions_do_not_consume_a_turn(self):
        env = self.make_env()
        initial = env.reset()
        for action in (-1, 5, True, 'up', None, 1.0):
            with self.subTest(action=action), self.assertRaises(ValueError):
                env.step(action)
        self.assertEqual(env.observe(), initial[0])
        self.assertEqual(env.position, (1, 1))
        _, _, _, _, info = env.step(4)
        self.assertEqual(info['elapsed_steps'], 1)

    def test_invalid_constructor_and_seed_are_rejected(self):
        for horizon in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                self.make_env(max_steps=horizon)
        with self.assertRaises(ValueError):
            self.make_env(start=(-1, 0))
        with self.assertRaises(ValueError):
            self.make_env(GridGraph(3, 3, {(1, 1)}))
        with self.assertRaises(ValueError):
            self.make_env(GridGraph(3, 3, cell_costs={(0, 0): 2}))
        env = self.make_env()
        env.reset(seed=1)
        env.step(Action.WAIT)
        for seed in (-1, True, '7', 1.5):
            with self.assertRaises(ValueError):
                env.reset(seed=seed)
        self.assertEqual(env.step(Action.WAIT)[4]['elapsed_steps'], 2)

    def test_info_mutation_does_not_change_environment(self):
        env = self.make_env()
        _, info = env.reset()
        info['reward_components']['goal'] = 999
        info['position'] = (9, 9)
        _, reward, _, _, next_info = env.step(Action.WAIT)
        self.assertEqual(reward, -1)
        self.assertEqual(next_info['reward_components']['goal'], 0)
        self.assertEqual(env.position, (1, 1))

    def test_reward_components_sum_to_step_and_episode_rewards(self):
        env = self.make_env(GridGraph(3, 3, {(0, 1)}))
        env.reset()
        total = 0
        for action in (Action.UP, Action.WAIT, Action.DOWN, Action.RIGHT):
            _, reward, _, _, info = env.step(action)
            self.assertEqual(reward, sum(info['reward_components'].values()))
            total += reward
            self.assertEqual(info['episode_reward'], total)
        self.assertEqual(total, 86)

    def test_baseline_route_replays_to_goal_with_correct_metrics(self):
        graph = GridGraph(3, 5, {(0, 2), (1, 2)})
        path = bfs(graph, (0, 0), (0, 4))
        env = SingleAgentEnv(graph, (0, 0), (0, 4), max_steps=8)
        env.reset(seed=42)
        directions = {(-1, 0): Action.UP, (1, 0): Action.DOWN,
                      (0, -1): Action.LEFT, (0, 1): Action.RIGHT}
        for source, target in zip(path, path[1:]):
            action = directions[(target[0] - source[0], target[1] - source[1])]
            _, _, terminated, truncated, info = env.step(action)
            self.assertEqual(info['position'], target)
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertEqual(info['moves'], 8)
        self.assertEqual(info['arrival_step'], 8)
        self.assertEqual(info['path_cost'], 8)
        self.assertEqual(info['episode_reward'], 92)

    def test_unreachable_map_runs_until_timeout_without_fake_success(self):
        env = SingleAgentEnv(GridGraph(1, 3, {(0, 1)}), (0, 0), (0, 2), max_steps=3)
        env.reset()
        for _ in range(3):
            _, _, _, truncated, info = env.step(Action.RIGHT)
        self.assertTrue(truncated)
        self.assertFalse(info['success'])
        self.assertEqual(info['moves'], 0)
        self.assertEqual(info['obstacle_attempts'], 3)
        self.assertEqual(info['episode_reward'], -33)

    def test_wait_delays_arrival_without_increasing_path_length(self):
        env = SingleAgentEnv(GridGraph(1, 2), (0, 0), (0, 1), max_steps=3)
        env.reset()
        env.step(Action.WAIT)
        _, _, _, _, info = env.step(Action.RIGHT)
        self.assertEqual(info['arrival_step'], 2)
        self.assertEqual(info['moves'], 1)
        self.assertEqual(info['episode_reward'], 98)

    def test_seeded_action_sequences_preserve_grid_and_metric_invariants(self):
        graph = GridGraph(5, 5, {(1, 1), (2, 3), (3, 2)})
        for seed in range(10):
            rng = random.Random(seed)
            env = SingleAgentEnv(graph, (0, 0), (4, 4), max_steps=30)
            env.reset(seed=seed)
            previous, expected_moves, total = (0, 0), 0, 0
            for _ in range(30):
                obs, reward, terminated, truncated, info = env.step(rng.randrange(5))
                current = info['position']
                self.assertTrue(graph.is_free(current))
                distance = abs(current[0] - previous[0]) + abs(current[1] - previous[1])
                self.assertIn(distance, (0, 1))
                expected_moves += distance
                total += reward
                self.assertEqual(info['moves'], expected_moves)
                self.assertEqual(info['episode_reward'], total)
                self.assertTrue(all(math.isfinite(x) and -1 <= x <= 1 for x in obs))
                previous = current
                if terminated or truncated:
                    break


if __name__ == '__main__':
    unittest.main()
