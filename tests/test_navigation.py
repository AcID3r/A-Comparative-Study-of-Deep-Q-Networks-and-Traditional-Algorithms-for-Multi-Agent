"""Space/time hand examples for replanning and frozen routes."""

import unittest
from environments.grid_graph import GridGraph
from environments.dynamic_env import DynamicSingleAgentEnv, ObstacleChange
from environments.single_agent_env import Action
from environments.random_maps import blocked_route_schedule
from evaluation.navigation import SearchController, rollout


class NavigationTests(unittest.TestCase):
    def test_changed_route_replans_but_frozen_route_retries_original_edge(self):
        changes = [ObstacleChange(2, (0, 2), 'add'), ObstacleChange(6, (0, 2), 'remove')]
        def env():
            return DynamicSingleAgentEnv(GridGraph(2, 4), (0, 0), (0, 3), max_steps=12, schedule=changes)
        for method in ('bfs', 'dijkstra', 'astar'):
            e = env()
            controller = SearchController(e, method)
            result = rollout(controller, e)
            self.assertTrue(result['final_info']['success'])
            self.assertEqual(result['final_info']['moves'], 5)
            self.assertEqual(result['final_info']['arrival_step'], 5)
            self.assertEqual(result['final_info']['obstacle_attempts'], 0)
            self.assertEqual(result['plan_calls'], 2)
        e = env()
        frozen = rollout(SearchController(e, frozen=True), e)
        self.assertTrue(frozen['final_info']['success'])
        self.assertEqual(frozen['final_info']['moves'], 3)
        self.assertEqual(frozen['final_info']['arrival_step'], 7)
        self.assertEqual(frozen['final_info']['obstacle_attempts'], 4)
        self.assertEqual(frozen['plan_calls'], 1)

    def test_schedule_addition_cannot_target_an_occupied_cell_at_its_tick(self):
        scenario = {'rows': 5, 'cols': 5, 'start': (0, 0), 'goal': (4, 4), 'obstacles': []}
        events = blocked_route_schedule(scenario)
        self.assertEqual([e.tick for e in events], [3, 8])
        self.assertGreaterEqual(sum(events[0].position), 3)
        self.assertEqual(events[0].position, events[1].position)

    def test_unreachable_search_waits_until_horizon_without_fake_success(self):
        e = DynamicSingleAgentEnv(GridGraph(1, 3, {(0, 1)}), (0, 0), (0, 2), max_steps=5)
        result = rollout(SearchController(e), e)
        self.assertFalse(result['final_info']['success'])
        self.assertEqual(result['final_info']['failure_reason'], 'time_limit')
        self.assertEqual(result['plan_calls'], 1)
        self.assertEqual(result['final_info']['moves'], 0)

    def test_invalid_action_preserves_dynamic_diagnostics(self):
        e = DynamicSingleAgentEnv(GridGraph(2, 3), (0, 0), (0, 2), schedule=[ObstacleChange(2, (0, 1), 'add')])
        _, before = e.reset()
        with self.assertRaises(ValueError):
            e.step(True)
        self.assertEqual(e._info(), before)


if __name__ == '__main__':
    unittest.main()
