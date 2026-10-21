import itertools
import unittest
from algorithms.prioritized import prioritized_plan, plan_actions
from algorithms.bfs import bfs
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv


class PrioritizedTests(unittest.TestCase):
    def replay(self, graph, starts, goals, plan, horizon=20):
        self.assertTrue(plan.success)
        env = MultiAgentEnv(graph, starts, goals, max_steps=horizon)
        _, info = env.reset()
        for tick in range(horizon):
            if info['success']: break
            info = env.step(plan_actions(plan.paths, tick))[-1]
            self.assertEqual(sum(info['conflict_attempts']), 0)
            self.assertEqual(info['actual_collisions'], 0)
            self.assertEqual(len(set(env.positions)), len(starts))
        self.assertTrue(info['success'])
        self.assertEqual(info['arrival_steps'], tuple(len(p)-1 for p in plan.paths))
        return info

    def test_wait_required_all_methods(self):
        g = GridGraph(2,3)
        starts, goals = ((0,0),(1,1)), ((0,2),(0,1))
        for method in ('bfs','dijkstra','astar'):
            p = prioritized_plan(g, starts, goals, method=method, max_steps=5)
            info = self.replay(g, starts, goals, p, 5)
            self.assertEqual(info['arrival_steps'], (2,2))
            self.assertEqual(info['moves'], (2,1))

    def test_swap_requires_detour(self):
        g = GridGraph(2,2)
        starts, goals = ((0,0),(0,1)), ((0,1),(0,0))
        for method in ('bfs','dijkstra','astar'):
            p = prioritized_plan(g, starts, goals, method=method, max_steps=5)
            self.assertEqual(tuple(len(path)-1 for path in p.paths), (1,3))
            self.replay(g, starts, goals, p, 5)

    def test_permanent_goal_and_partial_failure(self):
        g = GridGraph(1,3)
        p = prioritized_plan(g, ((0,0),(0,2)), ((0,1),(0,0)), max_steps=8)
        self.assertFalse(p.success)
        self.assertIsNone(p.paths)
        self.assertEqual(p.failed_agent, 1)
        self.assertIsNotNone(p.partial_paths[0])
        self.assertEqual(p.failure_reason, 'no_reserved_path_within_horizon')

    def test_initial_goal_reserved_regardless_priority(self):
        g = GridGraph(1,3)
        p = prioritized_plan(g, ((0,0),(0,1)), ((0,2),(0,1)), max_steps=8)
        self.assertFalse(p.success)
        self.assertEqual(p.failed_agent, 0)

    def test_horizon_and_invalid_parameters(self):
        g = GridGraph(2,3)
        starts, goals = ((0,0),), ((0,2),)
        self.assertFalse(prioritized_plan(g, starts, goals, max_steps=1).success)
        p = prioritized_plan(g, starts, goals, max_steps=2)
        self.replay(g, starts, goals, p, 2)
        for kwargs in ({'priority':(True,)},{'priority':(1,)},{'method':'wrong'}):
            with self.assertRaises(ValueError): prioritized_plan(g, starts, goals, **kwargs)

    def test_four_agents_and_all_start_at_goal(self):
        g = GridGraph(4,4)
        starts = ((0,0),(1,0),(2,0),(3,0))
        goals = ((0,3),(1,3),(2,3),(3,3))
        for method in ('bfs','dijkstra','astar'):
            p = prioritized_plan(g, starts, goals, method=method)
            self.assertEqual(self.replay(g, starts, goals, p)['makespan'], 3)
        p = prioritized_plan(g, starts, starts)
        self.assertEqual(self.replay(g, starts, starts, p)['makespan'], 0)

    def test_single_agent_optimum_against_static_baseline(self):
        for bits in itertools.product((0,1), repeat=4):
            cells = ((0,1),(1,0),(1,1),(1,2))
            g = GridGraph(3,3, frozenset(p for p,b in zip(cells,bits) if b))
            expected = bfs(g, (0,0), (2,2))
            for method in ('bfs','dijkstra','astar'):
                p = prioritized_plan(g, ((0,0),), ((2,2),), method=method, max_steps=10)
                self.assertEqual(p.success, expected is not None)
                if expected:
                    self.assertEqual(len(p.paths[0]), len(expected))
                    self.replay(g, ((0,0),), ((2,2),), p, 10)

    def test_priority_order_can_change_success(self):
        g = GridGraph(2,3)
        starts, goals = ((0,0),(1,0)), ((1,2),(1,1))
        self.assertFalse(prioritized_plan(g, starts, goals, max_steps=8).success)
        reverse = prioritized_plan(g, starts, goals, max_steps=8, priority=(1,0))
        self.replay(g, starts, goals, reverse, 8)


if __name__ == '__main__': unittest.main()
