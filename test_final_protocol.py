import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from evaluation.team_protocol import ROOT
from evaluation.final_protocol import (generate_bank,collect_exclusions,metrics,freeze,check_freeze,method_list)
from evaluation.dynamic_team_protocol import make_env,rollout,team_schedule
from evaluation.summarize_final import aggregate,matched
from experiments.run_final import evaluate
from evaluation.audit_final import audit


class FinalProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((ROOT/'configs/final_experiment.json').read_text())
        cls.exclusions=collect_exclusions()
        cls.bank=generate_bank(cls.config,'pilot',cls.exclusions)

    def test_full_pilot_strata_reproducible_and_disjoint(self):
        self.assertEqual(self.bank,generate_bank(self.config,'pilot',self.exclusions))
        scenarios=self.bank['scenarios']
        self.assertEqual(len(scenarios),12)
        self.assertEqual(len({s['map_id'] for s in scenarios}),12)
        self.assertFalse({s['map_id'] for s in scenarios}&set(self.exclusions['excluded_ids']))
        self.assertEqual(len(method_list(self.config)),21)
        self.assertEqual({s['max_steps'] for s in scenarios},{30,60,90})

    def test_crossing_rule_and_endpoint_subsets(self):
        for s in self.bank['scenarios']:
            endpoints=s['team_starts']+s['team_goals']
            self.assertEqual(len({tuple(p) for p in endpoints}),8)
            self.assertTrue(all(p not in s['obstacles'] for p in endpoints))
            if s['arrangement']=='crossing':
                self.assertEqual(s['team_starts'],sorted(s['team_starts']))
                self.assertEqual(s['team_goals'],sorted(s['team_goals'],reverse=True))
                self.assertTrue(all(p[1]==0 for p in s['team_starts']))
                self.assertTrue(all(p[1]==s['cols']-1 for p in s['team_goals']))

    def test_event_safety_all_agent_counts(self):
        for s in self.bank['scenarios']:
            for e in team_schedule(s):
                self.assertNotIn(list(e.position),s['team_starts']+s['team_goals'])
                if e.operation=='add':
                    self.assertGreaterEqual(min(abs(e.position[0]-p[0])+abs(e.position[1]-p[1]) for p in s['team_starts']),e.tick)
        scenario=self.bank['scenarios'][0]
        for n in (1,2,4):
            for condition in ('static','dynamic'):
                result=rollout(make_env(scenario,30,n,condition),method='astar')
                self.assertEqual(result['final_info']['actual_collisions'],0)

    def test_defined_and_undefined_gaps(self):
        s=deepcopy(self.bank['scenarios'][0]); s['individual_optimal_moves']=[4,5,6,7]
        result={'final_info':dict(success=True,total_moves=6,makespan=8,change_history=[])}
        self.assertEqual(metrics(s,1,'static',result,2)['static_single_agent_gap'],.5)
        self.assertIsNone(metrics(s,2,'static',result,2)['static_single_agent_gap'])
        self.assertEqual(metrics(s,2,'static',result,2)['initial_independent_lower_bound'],9)
        self.assertIsNone(metrics(s,1,'dynamic',result,2)['static_single_agent_gap'])
        for value,reason in ((None,'initial goal unreachable'),(0,'zero reference')):
            s['individual_optimal_moves'][0]=value
            self.assertEqual(metrics(s,1,'static',result,2)['gap_undefined_reason'],reason)
        s['individual_optimal_moves'][0]=4; result['final_info']['success']=False
        self.assertEqual(metrics(s,1,'static',result,2)['gap_undefined_reason'],'episode failed')

    def test_after_addition_exposure_is_censored_on_failure(self):
        s=self.bank['scenarios'][0]
        info=dict(success=True,total_moves=9,makespan=10,change_history=[dict(operation='add',status='applied')])
        self.assertEqual(metrics(s,1,'dynamic',dict(final_info=info),2)['steps_after_addition'],9)
        info['success']=False; info['makespan']=None
        self.assertIsNone(metrics(s,1,'dynamic',dict(final_info=info),2)['steps_after_addition'])
        self.assertEqual(metrics(s,1,'dynamic',dict(final_info=info),2)['addition_exposed'],1)

    def row(self,seed,success,method='shared'):
        return dict(grid_size='5',density_requested='0.1',arrangement='uniform',n_agents='2',condition='static',
            method=method,map_id='a',seed=str(seed),success=str(success),makespan='8' if success else '',
            total_moves='12' if success else '999',conflict_attempts='2',planning_seconds='',inference_seconds='.01',
            static_single_agent_gap='',addition_exposed='0',steps_after_addition='')

    def test_denominators_success_means_and_seed_uncertainty(self):
        rows=[self.row(0,1),self.row(1,0)]
        g=aggregate(rows)[0]
        self.assertEqual(g['episodes'],2); self.assertEqual(g['success_rate'],.5)
        self.assertEqual(g['successful_mean_moves'],12)
        self.assertAlmostEqual(g['seed_success_std'],2**-.5)
        g=aggregate([self.row(0,0)])[0]
        self.assertIsNone(g['successful_mean_makespan']); self.assertIsNone(g['seed_success_std'])

    def test_matched_cases_use_same_scenarios_and_seed(self):
        rows=[self.row(0,1),self.row(1,0),self.row(0,1,'solo'),self.row(1,1,'solo')]
        result=matched(rows,'shared','solo')
        self.assertEqual(result['pairs'],2); self.assertEqual(result['both_successful'],1)
        self.assertEqual(result['mean_success_difference'],-.5)
        self.assertEqual(result['mean_makespan_difference_both_successful'],0)
        with self.assertRaises(ValueError): matched(rows[:-1],'shared','solo')

    def test_seal_and_tamper_rejection_without_final_cases(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=freeze(self.config,self.bank,Path(temporary)/'freeze')
            exclusions=check_freeze(self.config,directory)
            self.assertTrue({s['map_id'] for s in self.bank['scenarios']}<=set(exclusions['excluded_ids']))
            self.assertFalse(json.loads((directory/'manifest.json').read_text())['final_maps_generated'])
            (directory/'exclusions.json').write_text('{}')
            with self.assertRaises(ValueError): check_freeze(self.config,directory)

    def test_final_without_seal_and_bad_config_create_no_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'run'
            with self.assertRaises(ValueError): evaluate(self.config,output,'final')
            bad=deepcopy(self.config); bad['sizes']=[5]
            with self.assertRaises(ValueError): evaluate(bad,output)
            self.assertFalse(output.exists())

    def test_three_repeat_final_pipeline_on_pilot_geometry_and_tampering(self):
        # Exercise final execution/timer accounting without generating final maps.
        bank=deepcopy(self.bank); bank['phase']='final'; bank['scenarios']=bank['scenarios'][:1]
        with tempfile.TemporaryDirectory() as temporary:
            with patch('experiments.run_final.check_freeze',return_value=self.exclusions), \
                 patch('experiments.run_final.generate_bank',return_value=bank), \
                 patch('evaluation.audit_final.generate_bank',return_value=bank):
                run=evaluate(self.config,Path(temporary)/'run','final','test-double-seal')
                result=audit(run)
                self.assertEqual(result['episodes'],126)
                self.assertEqual(result['timing_repeats'],3)
                lines=(run/'trajectories.jsonl').read_text().splitlines()
                trace=json.loads(lines[0])
                self.assertEqual(len(trace['timing_repeats']),3)
                trace['timing_repeats'][1]['episode_seconds']=-1
                lines[0]=json.dumps(trace)
                (run/'trajectories.jsonl').write_text('\n'.join(lines)+'\n')
                with self.assertRaises(AssertionError): audit(run)


if __name__=='__main__': unittest.main()
