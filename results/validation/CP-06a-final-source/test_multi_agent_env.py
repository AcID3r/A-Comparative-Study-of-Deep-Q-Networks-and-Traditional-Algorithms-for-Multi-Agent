import itertools
import unittest
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv, OBSERVATION_FEATURES


class TeamEnvironmentTests(unittest.TestCase):
    def env(self, starts, goals=None, rows=3, cols=4, horizon=10, walls=()):
        e = MultiAgentEnv(GridGraph(rows, cols, frozenset(walls)), starts,
                          goals or tuple(reversed(starts)), max_steps=horizon)
        e.reset(seed=7)
        return e

    def test_vertex_rejects_both(self):
        e = self.env(((1,0),(1,2)))
        _, rewards, _, _, info = e.step((3,2))
        self.assertEqual(e.positions, ((1,0),(1,2)))
        self.assertEqual(rewards, (-26.,-26.))
        self.assertEqual(info['vertex_conflicts'], 1)
        self.assertEqual(info['actual_collisions'], 0)

    def test_swap_rejects_both(self):
        e = self.env(((1,0),(1,1)))
        info = e.step((3,2))[-1]
        self.assertEqual(info['swap_conflicts'], 1)
        self.assertEqual(info['conflict_attempts'], (1,1))
        self.assertEqual(e.positions, ((1,0),(1,1)))

    def test_following_is_legal(self):
        e = self.env(((1,0),(1,1)), ((0,0),(0,1)))
        info = e.step((3,3))[-1]
        self.assertEqual(e.positions, ((1,1),(1,2)))
        self.assertEqual(info['conflict_attempts'], (0,0))

    def test_cascade_four_agents(self):
        starts = ((1,0),(1,1),(1,2),(1,3))
        e = self.env(starts, ((0,0),(0,1),(0,2),(1,3)))
        info = e.step((3,3,3,4))[-1]
        self.assertEqual(e.positions, starts)
        self.assertEqual(info['conflict_attempts'], (1,1,1,0))
        self.assertEqual(info['vertex_conflicts'], 3)
        self.assertEqual(info['reward_components'][3]['step'], 0)

    def test_four_agent_rotation_allowed(self):
        starts = ((0,0),(0,1),(1,1),(1,0))
        goals = ((0,1),(1,1),(1,0),(0,0))
        e = self.env(starts, goals)
        _, rewards, term, trunc, info = e.step((3,1,2,0))
        self.assertEqual(e.positions, goals)
        self.assertEqual(rewards, (199.,)*4)
        self.assertTrue(term)
        self.assertFalse(trunc)
        self.assertEqual(info['makespan'], 1)

    def test_rewards_finished_agent_and_last_tick(self):
        e = self.env(((0,0),(1,0)), ((0,1),(1,2)), horizon=2)
        self.assertEqual(e.step((3,3))[1], (99.,-1.))
        _, rewards, term, trunc, info = e.step((2,3))
        self.assertEqual(rewards, (100.,199.))
        self.assertTrue(term)
        self.assertFalse(trunc)
        self.assertEqual(info['arrival_steps'], (1,2))
        self.assertEqual(info['moves'], (1,2))
        with self.assertRaises(RuntimeError): e.step((4,4))

    def test_boundaries_obstacles_timeout(self):
        e = self.env(((0,0),(1,0)), ((0,3),(1,3)), horizon=1, walls=((1,1),))
        _, rewards, term, trunc, info = e.step((0,3))
        self.assertEqual(rewards, (-6.,-11.))
        self.assertFalse(term)
        self.assertTrue(trunc)
        self.assertIsNone(info['makespan'])
        self.assertEqual(info['total_moves'], 0)

    def test_observation_reset_and_copy(self):
        e = self.env(((1,0),(1,1)), ((0,0),(0,1)))
        obs, info = e.reset(seed=12)
        self.assertEqual(len(OBSERVATION_FEATURES), 17)
        self.assertEqual(obs[0][-4:], (0.,0.,0.,1.))
        self.assertEqual(obs[1][-4:], (0.,0.,1.,0.))
        info['reward_components'][0]['goal'] = 999
        self.assertEqual(e.info()['reward_components'][0]['goal'], 0)
        e.step((3,3)); e.reset(seed=12)
        self.assertEqual(e.observe(), obs)

    def test_joint_validation_is_atomic(self):
        e = self.env(((0,0),(1,0)), ((0,3),(1,3)))
        before = e.info()
        for actions in ((3,99),(3,True),(3,), None):
            with self.assertRaises(ValueError): e.step(actions)
            self.assertEqual(e.info(), before)

    def test_endpoint_horizon_validation_and_reset_at_goal(self):
        g = GridGraph(2,2)
        for starts, goals in ((((0,0),(0,0)),((0,1),(1,1))), (((0,0),(1,0)),((1,1),(1,1)))):
            with self.assertRaises(ValueError): MultiAgentEnv(g, starts, goals)
        with self.assertRaises(ValueError): MultiAgentEnv(g, ((0,0),), ((1,1),), max_steps=True)
        with self.assertRaises(ValueError): MultiAgentEnv(GridGraph(2,2,cell_costs={(1,1):2}), ((0,0),), ((1,1),))
        e = MultiAgentEnv(g, ((0,0),), ((0,0),))
        with self.assertRaises(RuntimeError): e.observe()
        _, info = e.reset()
        self.assertEqual(info['episode_rewards'], (0.,))
        self.assertEqual(info['makespan'], 0)

    def test_exhaustive_four_agent_one_tick_invariant(self):
        starts = ((0,0),(0,1),(1,1),(1,0))
        goals = ((1,1),(1,0),(0,0),(0,1))
        e = MultiAgentEnv(GridGraph(2,2), starts, goals)
        for actions in itertools.product(range(5), repeat=4):
            e.reset()
            e.step(actions)
            self.assertEqual(len(set(e.positions)), 4)
            for i,j in itertools.combinations(range(4),2):
                self.assertFalse(e.positions[i]==starts[j] and e.positions[j]==starts[i])


if __name__ == '__main__': unittest.main()
