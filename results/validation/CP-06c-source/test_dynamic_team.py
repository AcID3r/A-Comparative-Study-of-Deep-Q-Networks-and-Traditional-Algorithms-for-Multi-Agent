import unittest
from environments.grid_graph import GridGraph
from environments.dynamic_env import ObstacleChange as Change
from environments.dynamic_team_env import DynamicTeamEnv
from evaluation.dynamic_team_protocol import rollout,team_schedule


class DynamicTeamTests(unittest.TestCase):
    def env(self,schedule,starts=((0,0),(2,0)),goals=((0,3),(2,3)),horizon=10):
        return DynamicTeamEnv(GridGraph(3,4),starts,goals,max_steps=horizon,schedule=schedule)

    def test_prepare_visibility_idempotence_and_versions(self):
        env=self.env((Change(2,(0,2),'add'),))
        obs,_=env.reset()
        nxt,_,_,_,info=env.step((3,3))
        self.assertEqual(info['action_graph_version'],0)
        self.assertEqual(info['graph_version'],1)
        self.assertEqual(nxt[0][7],1)
        self.assertEqual(env.observe(),nxt)
        self.assertEqual(len(env.info()['change_history']),1)
        snapshot=env.graph
        env.step((3,3))
        self.assertEqual(env.positions[0],(0,1))
        self.assertIs(env.graph,snapshot)

    def test_reset_and_history_copy(self):
        env=self.env((Change(1,(1,2),'add'),Change(2,(1,2),'remove')))
        obs,info=env.reset(seed=5)
        info['change_history'][0]['status']='wrong'
        env.step((4,4))
        self.assertNotIn((1,2),env.graph.obstacles)
        again,info=env.reset(seed=5)
        self.assertEqual(again,obs)
        self.assertEqual(info['graph_version'],1)
        self.assertEqual(info['change_history'][0]['status'],'applied')

    def test_occupied_and_noop_events(self):
        env=self.env((Change(2,(0,1),'add'),Change(3,(1,2),'remove')))
        env.reset(); env.step((3,4))
        self.assertEqual(env.info()['change_history'][0]['status'],'rejected_occupied')
        env.step((4,4))
        self.assertEqual(env.info()['change_history'][1]['status'],'no_change')
        self.assertEqual(env.info()['graph_version'],0)

    def test_endpoint_duplicate_horizon_and_type_validation(self):
        for p in ((0,0),(2,0),(0,3),(2,3)):
            with self.assertRaises(ValueError): self.env((Change(1,p,'add'),))
        for schedule in ((Change(11,(1,2),'add'),),(Change(1,(9,9),'add'),),('wrong',),
                         (Change(1,(1,2),'add'),Change(1,(1,2),'remove'))):
            with self.assertRaises(ValueError): self.env(schedule)

    def test_invalid_action_and_seed_do_not_change_state(self):
        env=self.env((Change(2,(1,2),'add'),))
        env.reset(); before=env.info()
        for actions in ((3,99),(3,True),(3,),None):
            with self.assertRaises(ValueError): env.step(actions)
            self.assertEqual(env.info(),before)
        with self.assertRaises(ValueError): env.reset(seed=True)
        self.assertEqual(env.info(),before)

    def test_events_stop_after_goal_and_timeout(self):
        env=self.env((Change(2,(1,2),'add'),),goals=((0,1),(2,1)))
        env.reset(); env.step((3,3))
        self.assertEqual(env.info()['change_history'],[])
        with self.assertRaises(RuntimeError): env.step((4,4))
        env=self.env((Change(2,(1,2),'add'),),horizon=2)
        env.reset(); env.step((4,4)); env.step((4,4))
        self.assertTrue(env.info()['truncated'])
        self.assertEqual(env.info()['prepared_tick'],2)
        self.assertEqual(len(env.info()['change_history']),1)
        with self.assertRaises(RuntimeError): env.step((4,4))

    def test_four_agent_cascade_after_obstacle(self):
        env=DynamicTeamEnv(GridGraph(3,5),((1,0),(1,1),(1,2),(0,0)),
            ((2,0),(2,1),(2,2),(0,4)),schedule=(Change(1,(1,3),'add'),))
        env.reset(); info=env.step((3,3,3,4))[-1]
        self.assertEqual(info['conflict_attempts'],(1,1,0,0))
        self.assertEqual(info['obstacle_attempts'],(0,0,1,0))
        self.assertEqual(info['actual_collisions'],0)

    def test_safe_schedule_and_empty_candidate(self):
        scenario={'rows':5,'cols':5,'obstacles':[],
            'team_starts':[(0,0),(0,4),(4,0),(4,4)],
            'team_goals':[(0,1),(1,4),(3,0),(4,3)]}
        schedule=team_schedule(scenario)
        self.assertEqual(len(schedule),2)
        self.assertGreaterEqual(min(abs(schedule[0].position[0]-r)+abs(schedule[0].position[1]-c)
                                    for r,c in scenario['team_starts']),2)
        tiny={'rows':2,'cols':4,'obstacles':[],
              'team_starts':[(0,0),(0,1),(0,2),(0,3)],'team_goals':[(1,0),(1,1),(1,2),(1,3)]}
        self.assertEqual(team_schedule(tiny),())

    def test_replan_vs_frozen_detour_and_preserved_arrivals(self):
        changes=(Change(2,(0,2),'add'),Change(8,(0,2),'remove'))
        replanned=rollout(self.env(changes),'ignored',method='astar')
        frozen=rollout(self.env(changes),'ignored',method='astar',frozen=True)
        self.assertTrue(replanned['success'] and frozen['success'])
        self.assertLess(replanned['final_info']['makespan'],frozen['final_info']['makespan'])
        self.assertEqual(replanned['final_info']['arrival_steps'][1],3)
        self.assertEqual(replanned['planning_calls'][1]['positions'][0],(0,1))
        self.assertEqual(replanned['planning_calls'][1]['remaining_horizon'],9)
        self.assertEqual(len(frozen['planning_calls']),1)

    def test_wait_after_plan_failure_then_recover_on_removal(self):
        env=DynamicTeamEnv(GridGraph(2,4),((0,0),(1,0)),((0,3),(1,3)),max_steps=10,
            schedule=(Change(1,(0,2),'add'),Change(1,(1,2),'add'),
                      Change(3,(0,2),'remove'),Change(3,(1,2),'remove')))
        result=rollout(env,method='bfs')
        self.assertTrue(result['success'])
        self.assertEqual(result['plan_failures'],1)
        self.assertEqual(result['planning_calls'][1]['elapsed'],2)
        self.assertEqual(result['final_info']['makespan'],5)


if __name__=='__main__': unittest.main()
