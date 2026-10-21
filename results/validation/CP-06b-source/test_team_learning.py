import csv
import json
import tempfile
import unittest
from pathlib import Path
import torch
from algorithms.dqn import DQNAgent,DQNConfig,Transition,bellman_targets
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv
from evaluation.team_protocol import ROOT,generate_bank,environment
from evaluation.audit_team_run import audit
from evaluation.summarize_team import aggregate
from training.train_team import train,episode_transitions
from experiments.run_team_comparison import evaluate


class TeamLearningTests(unittest.TestCase):
    def tiny(self):
        c = json.loads((ROOT/'configs/dqn_team.json').read_text())
        c.update(seeds=[0],cycles=2,evaluate_every_cycles=1,batch_size=2,warmup_transitions=2,
                 train_every_transitions=2,replay_capacity=50,network={'hidden_sizes':[8,8],'target_update_steps':2})
        c['partitions'] = {'train':[4000,3],'validation':[5000,2],'test':[6000,2]}
        c['map_spec']['max_steps']=6
        return c

    def test_v2_shapes_reload_and_v1_default(self):
        agent = DQNAgent(DQNConfig(hidden_sizes=(8,8)),seed=4,observation_version=2)
        observation = (0.,)*17
        self.assertEqual(agent.q_values(observation).shape,(5,))
        self.assertEqual(DQNAgent().online[0].in_features,13)
        agent.train_batch([Transition(observation,4,1,observation,True,False,2)])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'v2.pt'; agent.save(path)
            loaded,_ = DQNAgent.load(path)
            self.assertTrue(torch.equal(agent.q_values(observation),loaded.q_values(observation)))
            self.assertEqual(loaded.observation_version,2)

    def test_mixed_layout_rejected_without_update(self):
        v1 = Transition((0.,)*13,0,0,(0.,)*13,False,False)
        agent = DQNAgent(observation_version=2)
        with self.assertRaises(ValueError): agent.train_batch([v1])
        self.assertEqual(agent.updates,0)
        with self.assertRaises(ValueError): agent.act((0.,)*13)
        with self.assertRaises(ValueError): Transition((0.,)*17,0,0,(0.,)*13,False,False,2)
        with self.assertRaises(ValueError): DQNAgent(observation_version=True)

    def test_delayed_team_bonus_and_team_masks(self):
        env = MultiAgentEnv(GridGraph(2,3),((0,0),(1,0)),((0,1),(1,2)),max_steps=2)
        obs,_ = env.reset()
        nxt,rewards,term,trunc,_ = env.step((3,3))
        first = episode_transitions(obs,(3,3),rewards,nxt,term,trunc)
        self.assertEqual(first[0].reward,99)
        self.assertFalse(first[0].terminated)
        last,rewards,term,trunc,_ = env.step((4,3))
        final = episode_transitions(nxt,(4,3),rewards,last,term,trunc)
        self.assertEqual(final[0].reward,100)
        self.assertTrue(final[0].terminated)
        targets = bellman_targets(torch.tensor([99.,100.]),torch.tensor([False,True]),
                                  torch.tensor([False,False]),torch.ones((2,5))*10,.9)
        self.assertTrue(torch.equal(targets,torch.tensor([108.,100.])))

    def test_finished_agent_timeout_masks_future(self):
        env = MultiAgentEnv(GridGraph(2,3),((0,0),(1,0)),((0,1),(1,2)),max_steps=1)
        obs,_=env.reset(); nxt,rewards,term,trunc,_=env.step((3,4))
        transitions=episode_transitions(obs,(3,4),rewards,nxt,term,trunc)
        self.assertTrue(all(t.truncated and not t.terminated for t in transitions))

    def test_geometry_and_endpoint_splits(self):
        bank = generate_bank(self.tiny())
        identities = [s['map_id'] for group in bank['partitions'].values() for s in group]
        self.assertEqual(len(identities),len(set(identities)))
        self.assertFalse(set(identities)&set(bank['excluded_ids']))
        for group in bank['partitions'].values():
            for s in group:
                self.assertEqual(len(set(map(tuple,s['team_starts']+s['team_goals']))),8)
                solo=environment(s,6,route=0); obs,_=solo.reset()
                self.assertEqual(obs[0][-4:],(0.,)*4)

    def test_real_training_evaluation_and_audits(self):
        with tempfile.TemporaryDirectory() as temp:
            trained=train(self.tiny(),Path(temp)/'training')
            result=audit(trained)
            self.assertEqual(result['episodes'],6)
            self.assertEqual(result['matched_agent_tasks_per_seed'],4)
            evaluated=evaluate(trained,Path(temp)/'evaluation')
            self.assertEqual(audit(evaluated)['episodes'],24)
            with (evaluated/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
            self.assertEqual(len(aggregate(rows)),12)
            path=trained/'training_actions.jsonl'
            records=path.read_text().splitlines()
            record=json.loads(records[0]); record['final_info']['moves'][0]=999
            records[0]=json.dumps(record); path.write_text('\n'.join(records)+'\n')
            with self.assertRaises(AssertionError): audit(trained)

    def test_invalid_config_creates_no_run(self):
        c=self.tiny(); c['map_spec']['density']=2
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'runs'
            with self.assertRaises(ValueError): train(c,path)
            self.assertFalse(path.exists())

    def test_aggregate_failures_and_successful_only_means(self):
        base={'method':'shared','n_agents':'2','seed':'0','conflict_attempts':'3','actual_collisions':'0','failure_reason':''}
        groups=aggregate([{**base,'success':'1','makespan':'4','total_moves':'5'},
                          {**base,'seed':'1','success':'0','makespan':'','total_moves':'100','failure_reason':'time_limit'}])
        self.assertEqual(groups[0]['success_rate'],.5)
        self.assertEqual(groups[0]['successful_mean_moves'],5)
        self.assertEqual(groups[0]['successful_mean_makespan'],4)
        failed=aggregate([{**base,'success':'0','makespan':'','total_moves':'0','failure_reason':'planning_failure'}])[0]
        self.assertIsNone(failed['successful_mean_makespan'])
        self.assertEqual(failed['planning_failures'],1)


if __name__ == '__main__': unittest.main()
