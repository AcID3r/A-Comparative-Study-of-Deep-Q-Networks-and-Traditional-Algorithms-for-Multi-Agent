"""Replay team training actions and held-out decisions, verify saved counters."""
import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path
import torch
from algorithms.dqn import DQNAgent,DQNConfig,epsilon_at
from evaluation.team_protocol import environment,generate_bank,validation_cases,rollout


def canonical(value): return json.loads(json.dumps(value))


def read_lines(path):
    with path.open(encoding='utf-8') as f:
        for line in f: yield json.loads(line)


def replay_record(scenario,config,n,record,agent=None,method=None):
    env = environment(scenario,config['map_spec']['max_steps'],n)
    actual = rollout(env,agent,method)
    for key in ('success','failure_reason','final_info','trace'):
        assert canonical(actual[key]) == record[key],key
    if actual['planning'] is not None:
        for key in ('paths','failed_agent','failure_reason','expanded_nodes'):
            assert canonical(actual['planning'][key]) == record['planning'][key],key
    else: assert record['planning'] is None
    for key in ('decision_seconds','episode_seconds'):
        assert math.isfinite(record[key]) and record[key] >= 0
    if record['planning'] is not None:
        assert math.isfinite(record['planning']['seconds']) and record['planning']['seconds'] >= 0


def audit(directory):
    directory = Path(directory)
    config = json.loads((directory/'config.json').read_text())
    bank = json.loads((directory/'map_bank.json').read_text())
    complete = json.loads((directory/'COMPLETE.json').read_text())
    assert canonical(generate_bank(config)) == bank
    metadata = json.loads((directory/'metadata.json').read_text())
    for name,digest in metadata['source_sha256'].items():
        assert hashlib.sha256((directory/'source'/name).read_bytes()).hexdigest() == digest,name
    torch.set_num_threads(1)
    scenarios = {s['map_id']:s for group in bank['partitions'].values() for s in group}
    if metadata['purpose'] == 'static_team_training':
        with (directory/'training_episodes.csv').open(newline='') as f: rows = list(csv.DictReader(f))
        with (directory/'optimizer_updates.csv').open(newline='') as f: updates = list(csv.DictReader(f))
        traces = list(read_lines(directory/'training_actions.jsonl'))
        assert len(rows) == len(traces) == 3*len(config['seeds'])*config['cycles']
        assert complete['models'] == 2*len(config['seeds']) and complete['test_maps_used'] is False
        choices,counts,totals = {},{},{}
        previous_key = None
        expected_order = [(m,s,c,r) for m in ('solo','shared') for s in config['seeds']
                          for c in range(1,config['cycles']+1) for r in ((0,1) if m=='solo' else (None,))]
        for row,trace in zip(rows,traces):
            mode,seed,cycle = row['mode'],int(row['seed']),int(row['cycle'])
            assert mode in ('solo','shared') and seed in config['seeds'] and 1 <= cycle <= config['cycles']
            key = mode,seed
            if key not in choices:
                rng = random.Random(seed+20000)
                choices[key] = [rng.choice(bank['partitions']['train'])['map_id'] for _ in range(config['cycles'])]
                counts[key] = 0; totals[key] = {'tasks':0,'ticks':0,'seconds':0.0,'episodes':0}
            identity = choices[key][cycle-1]
            assert row['map_id'] == trace['map_id'] == identity
            assert trace['mode']==mode and trace['seed']==seed and trace['cycle']==cycle
            route = None if row['route']=='' else int(row['route'])
            assert trace['route'] == route and route in ((0,1) if mode=='solo' else (None,))
            # Exact mode/seed/cycle/route order, not just row counts.
            record_key = (mode,seed,cycle,route)
            if previous_key is None: expected_index = 0
            assert record_key == expected_order[expected_index]
            expected_index += 1; previous_key = record_key
            env = environment(scenarios[identity],config['map_spec']['max_steps'],route=route)
            obs,info = env.reset(seed=seed)
            for actions in trace['actions']:
                for action,arrival in zip(actions,info['arrival_steps']):
                    assert arrival is None or action == 4
                obs,rewards,term,trunc,info = env.step(actions)
                assert all(r==sum(parts.values()) for r,parts in zip(rewards,info['reward_components']))
            assert info['terminated'] or info['truncated']
            assert canonical(info) == trace['final_info']
            transitions = info['elapsed_steps']*env.n_agents
            counts[key] += transitions
            assert int(row['steps'])==info['elapsed_steps'] and int(row['agent_tasks'])==env.n_agents
            assert int(row['transitions'])==transitions and int(row['cumulative_transitions'])==counts[key]
            assert int(row['success'])==info['success'] and int(row['total_moves'])==info['total_moves']
            assert int(row['conflict_attempts'])==sum(info['conflict_attempts'])
            assert float(row['episode_reward'])==sum(info['episode_rewards'])
            assert float(row['epsilon'])==epsilon_at(cycle-1,config['epsilon_initial'],config['epsilon_final'],config['epsilon_decay_cycles'])
            every,warm = config['train_every_transitions'],config['warmup_transitions']
            expected_updates = max(0,counts[key]//every-(warm+every-1)//every+1)
            assert int(row['updates'])==expected_updates
            assert math.isfinite(float(row['training_seconds'])) and float(row['training_seconds']) >= 0
            totals[key]['tasks'] += env.n_agents; totals[key]['ticks'] += info['elapsed_steps']
            totals[key]['seconds'] += float(row['training_seconds']); totals[key]['episodes'] += 1
        for key,count in counts.items():
            selected = [u for u in updates if (u['mode'],int(u['seed']))==key]
            expected_counts = list(range(((config['warmup_transitions']+config['train_every_transitions']-1)//config['train_every_transitions'])*config['train_every_transitions'],count+1,config['train_every_transitions']))
            assert len(selected)==len(expected_counts)
            for i,(row,counter) in enumerate(zip(selected,expected_counts),1):
                assert int(row['transition_count'])==counter and int(row['update'])==i
                assert row['target_synced']==str(i%config['network']['target_update_steps']==0)
                assert math.isfinite(float(row['loss'])) and float(row['loss']) >= 0
                assert math.isfinite(float(row['gradient_norm_before_clip'])) and float(row['gradient_norm_before_clip']) >= 0
        records = list(read_lines(directory/'validation.jsonl'))
        expected_cycles = [0]+[c for c in range(1,config['cycles']+1) if c%config['evaluate_every_cycles']==0 or c==config['cycles']]
        expected_records = [(m,s,c) for m in ('solo','shared') for s in config['seeds'] for c in expected_cycles]
        assert [(v['mode'],v['seed'],v['cycle']) for v in records]==expected_records
        for v in records:
            assert [c['map_id'] for c in v['cases']] == [s['map_id'] for s in bank['partitions']['validation']]
            for c in v['cases']:
                assert c['n_agents']==2
                env = environment(scenarios[c['map_id']],config['map_spec']['max_steps'])
                obs,info = env.reset(seed=0)
                for step in c['rollout']['trace']:
                    assert canonical(obs)==step['observations']
                    assert all(arrival is None or action==4 for arrival,action in zip(info['arrival_steps'],step['actions']))
                    obs,rewards,term,trunc,info = env.step(step['actions'])
                    assert canonical(obs)==step['next_observations'] and canonical(rewards)==step['rewards']
                    assert term==step['terminated'] and trunc==step['truncated']
                    assert canonical(info)==step['info']
                assert info['terminated'] or info['truncated']
                assert canonical(info)==c['rollout']['final_info']
                assert info['success']==c['rollout']['success'] and info['failure_reason']==c['rollout']['failure_reason']
        summary = json.loads((directory/'summary.json').read_text())
        assert len(summary)==len(counts)
        for s in summary:
            key = s['mode'],s['seed']
            assert s['transitions']==counts[key] and s['agent_tasks']==totals[key]['tasks']==2*config['cycles']
            assert s['joint_ticks']==totals[key]['ticks'] and s['episodes']==totals[key]['episodes']
            assert math.isclose(s['training_seconds'],totals[key]['seconds'])
            model,meta = DQNAgent.load(directory/'models'/f'{key[0]}_seed_{key[1]}.pt')
            assert model.observation_version==2 and model.updates==s['updates']
            assert meta['config']==config and meta['mode']==s['mode'] and meta['transitions']==s['transitions']
            final = next(r for r in records if (r['mode'],r['seed'],r['cycle'])==(*key,config['cycles']))
            cases = validation_cases(model,config,bank)
            assert s['validation_successes']==sum(c['rollout']['success'] for c in cases)
            assert s['validation_cases']==len(cases) and s['reload_matches'] is True
            assert [c['map_id'] for c in final['cases']]==[c['map_id'] for c in cases]
            for case,actual in zip(final['cases'],cases):
                for field in ('success','failure_reason','final_info','trace'):
                    assert case['rollout'][field]==canonical(actual['rollout'][field])
        return {'kind':'training','episodes':len(rows),'optimizer_updates':len(updates),'validation_records':len(records),
                'matched_agent_tasks_per_seed':2*config['cycles'],'source_snapshots_match':True,
                'training_actions_replayed':True,'no_test_maps_in_training':True,'final_reload_matches':True}
    # Held-out episodes: load the referenced final models, checking their digests.
    models = json.loads((directory/'models.json').read_text())
    agents = {}
    for m in models:
        path = Path(m['path'])
        assert hashlib.sha256(path.read_bytes()).hexdigest()==m['sha256']
        agent,meta = DQNAgent.load(path)
        assert agent.observation_version==2 and meta['config']==config and meta['mode']==m['method']
        agents[(m['method'],m['seed'])] = agent
    for seed in config['seeds']: agents[('untrained',seed)] = DQNAgent(DQNConfig(**config['network']),seed=seed,observation_version=2)
    with (directory/'raw_results.csv').open(newline='') as f: rows = list(csv.DictReader(f))
    traces = list(read_lines(directory/'trajectories.jsonl'))
    methods = [(m,None) for m in ('bfs','dijkstra','astar')]+list(agents)
    expected_keys = {(s['map_id'],n,m,seed) for s in bank['partitions']['test'] for n in (2,4) for m,seed in methods}
    assert len(rows)==len(traces)==len(expected_keys)==complete['episodes']
    assert complete['methods_per_scenario']==len(methods) and complete['test_maps']==len(bank['partitions']['test'])
    observed = set()
    for row,trace in zip(rows,traces):
        m,seed,n = row['method'],None if row['seed']=='' else int(row['seed']),int(row['n_agents'])
        key = row['map_id'],n,m,seed
        assert key not in observed and key in expected_keys
        observed.add(key)
        assert (trace['map_id'],trace['n_agents'],trace['method'],trace['seed'])==key
        scenario = scenarios[row['map_id']]
        record = trace['rollout']
        replay_record(scenario,config,n,record,agents.get((m,seed)),m if seed is None else None)
        info,p = record['final_info'],record['planning']
        assert int(row['success'])==record['success']
        assert row['failure_reason']==(record['failure_reason'] or '')
        assert int(row['map_seed'])==scenario['map_seed']
        assert int(row['individually_reachable'])==all(scenario['individual_reachable'][:n])
        expected = {'steps':None if info is None else info['elapsed_steps'],
            'makespan':None if info is None else info['makespan'],
            'sum_arrival_times':sum(info['arrival_steps']) if record['success'] else None,
            'total_moves':0 if info is None else info['total_moves'],'path_cost':0 if info is None else info['path_cost'],
            'conflict_attempts':0 if info is None else sum(info['conflict_attempts']),
            'vertex_conflicts':0 if info is None else info['vertex_conflicts'],
            'swap_conflicts':0 if info is None else info['swap_conflicts'],
            'actual_collisions':0 if info is None else info['actual_collisions'],
            'episode_reward':None if info is None else sum(info['episode_rewards']),
            'expanded_nodes':None if p is None else p['expanded_nodes'],
            'planning_seconds':None if p is None else p['seconds'],
            'decision_seconds':record['decision_seconds'],'episode_seconds':record['episode_seconds'],
            'inference_seconds':record['decision_seconds'] if seed is not None else None}
        for field,value in expected.items():
            assert row[field]=='' if value is None else float(row[field])==value,(field,row[field],value)
        assert expected['actual_collisions']==0
    assert observed==expected_keys
    return {'kind':'evaluation','episodes':len(rows),'test_maps':len(bank['partitions']['test']),
            'all_decisions_replayed':True,'source_snapshots_match':True,'model_digests_match':True,'actual_collisions':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path); parser.add_argument('--output',type=Path)
    args = parser.parse_args(); result = audit(args.run)
    if args.output:
        with args.output.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
