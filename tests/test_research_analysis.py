import unittest
from evaluation.research_analysis import summarize,pair,scaling


class ResearchAnalysisTests(unittest.TestCase):
    def row(self,method,seed,success,n=1,map_id='map',moves=5,exposed=1):
        return dict(method=method,seed=str(seed) if seed is not None else '',success=str(success),n_agents=str(n),
            condition='static',map_id=map_id,total_moves=str(moves),makespan='8' if success else '',actual_collisions='0',
            sum_arrival_times='8' if success else '',static_single_agent_gap='',conflict_attempts=str(n-1),
            addition_exposed=str(exposed),steps_after_addition='7' if success and exposed else '',initially_unreachable_agents='0',expanded_nodes='')

    def test_failure_and_seed_denominators(self):
        result=summarize([self.row('shared',0,1),self.row('shared',1,0,moves=999)])
        self.assertEqual(result['episodes'],2); self.assertEqual(result['mean_successful_moves'],5)
        self.assertEqual(result['exposed_episodes'],2); self.assertEqual(result['exposed_successes'],1)
        self.assertEqual(result['seed_std'],2**-.5)
        self.assertIsNone(summarize([self.row('shared',0,0)])['mean_successful_makespan'])

    def test_paired_reference_reused_without_fake_classical_seeds(self):
        rows=[self.row('shared',0,1,moves=7),self.row('shared',1,1,moves=5),self.row('astar',None,1,moves=5)]
        result=pair(rows,'shared','astar',classical_reference=True)
        self.assertEqual(result['pairs'],2); self.assertEqual(result['moves_difference'],1)
        self.assertEqual(result['ties'],1); self.assertEqual(result['right_shorter'],1)
        with self.assertRaises(ValueError): pair(rows[:-1],'shared','astar',classical_reference=True)

    def test_joint_success_and_exposure_selection(self):
        rows=[self.row('shared',0,1,moves=4),self.row('solo',0,1,moves=5),
              self.row('shared',1,0),self.row('solo',1,1),
              self.row('shared',2,1,exposed=0),self.row('solo',2,1)]
        result=pair(rows,'shared','solo',exposed=True)
        self.assertEqual(result['pairs'],2); self.assertEqual(result['jointly_successful'],1)
        self.assertEqual(result['success_difference'],-.5); self.assertEqual(result['moves_difference'],-1)

    def test_nested_scaling_compares_same_seed_and_map(self):
        rows=[self.row('shared',0,1,n=1),self.row('shared',0,0,n=2)]
        result=scaling(rows,'shared',1,2,'static')
        self.assertEqual(result['success_difference'],-1); self.assertEqual(result['attempts_difference'],1)
        with self.assertRaises(ValueError): scaling(rows,'shared',1,4,'static')


if __name__=='__main__': unittest.main()
