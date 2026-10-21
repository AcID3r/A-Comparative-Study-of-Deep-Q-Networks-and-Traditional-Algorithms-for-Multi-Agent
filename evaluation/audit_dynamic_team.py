"""Verify scheduled-event prefixes and replay every final-policy/controller decision."""
import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path
import torch
from experiments.run_dynamic_team import load_reference,result_row
from evaluation.dynamic_team_protocol import make_env,rollout,team_schedule


def canonical(value): return json.loads(json.dumps(value))


def audit(directory):
    directory=Path(directory)
    profile=json.loads((directory/'config.json').read_text())
    config,bank,agents,models=load_reference(profile)
    assert config==json.loads((directory/'training_config.json').read_text())
    assert bank==json.loads((directory/'map_bank.json').read_text())
    assert models==json.loads((directory/'models.json').read_text())
    metadata=json.loads((directory/'metadata.json').read_text())
    for name,digest in metadata['source_sha256'].items():
        assert hashlib.sha256((directory/'source'/name).read_bytes()).hexdigest()==digest,name
    complete=json.loads((directory/'COMPLETE.json').read_text())
    assert complete['no_online_training'] is True and complete['models_unchanged'] is True
    scenarios=bank['partitions']['test'][:2] if profile['purpose']=='dynamic_team_smoke' else bank['partitions']['test']
    lookup={s['map_id']:s for s in scenarios}
    schedules={s['map_id']:[asdict(e) for e in team_schedule(s,profile['add_tick'],profile['remove_tick'])] for s in scenarios}
    assert canonical(schedules)==json.loads((directory/'schedules.json').read_text())
    assert metadata['evaluation_map_ids']==list(lookup)
    assert metadata['empty_schedules']==sum(not s for s in schedules.values())
    methods=[(m,None) for m in ('bfs','dijkstra','astar','bfs_frozen','dijkstra_frozen','astar_frozen')]+list(agents)
    expected={(s['map_id'],n,c,m,seed) for s in scenarios for n in (2,4) for c in ('static','dynamic') for m,seed in methods}
    with (directory/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    with (directory/'trajectories.jsonl').open() as f: traces=[json.loads(line) for line in f]
    assert len(rows)==len(traces)==len(expected)==complete['episodes']
    assert complete['test_maps']==len(scenarios) and complete['methods_per_scenario']==len(methods)
    torch.set_num_threads(1)
    seen=set(); observed_histories={}; steps=0
    for row,trace in zip(rows,traces):
        key=(trace['map_id'],trace['n_agents'],trace['condition'],trace['method'],trace['seed'])
        assert key in expected and key not in seen
        seen.add(key)
        identity,n,condition,method,seed=key
        scenario=lookup[identity]; saved=trace['rollout']
        env=make_env(scenario,config['map_spec']['max_steps'],n,condition,profile['add_tick'],profile['remove_tick'])
        actual=rollout(env,agents.get((method,seed)),method.removesuffix('_frozen') if seed is None else None,method.endswith('_frozen'))
        for field in ('success','failure_reason','final_info','trace','expanded_nodes','plan_failures'):
            assert canonical(actual[field])==saved[field],(key,field)
        assert len(actual['planning_calls'])==len(saved['planning_calls'])
        for a,b in zip(actual['planning_calls'],saved['planning_calls']):
            for field in a:
                if field != 'seconds': assert canonical(a[field])==b[field],(key,field)
            assert math.isfinite(b['seconds']) and b['seconds']>=0
        assert saved['planning_seconds']==sum(c['seconds'] for c in saved['planning_calls'])
        for field in ('decision_seconds','planning_seconds','episode_seconds'):
            assert math.isfinite(saved[field]) and saved[field]>=0
        info=saved['final_info']; steps+=len(saved['trace'])
        assert info['actual_collisions']==0
        assert all(len(set(map(tuple,s['info']['positions'])))==n for s in saved['trace'])
        if condition=='dynamic':
            history=info['change_history']
            scheduled=schedules[identity]
            expected_history=[e|{'status':'applied','graph_version':i+1} for i,e in enumerate(scheduled)
                              if e['tick']<=info['prepared_tick']]
            assert history==canonical(expected_history),(key,'unexpected event status')
            previous=observed_histories.setdefault(identity,history)
            assert previous[:min(len(previous),len(history))]==history[:min(len(previous),len(history))]
            if len(history)>len(previous): observed_histories[identity]=history
        else: assert 'change_history' not in info
        projected=result_row(method,seed,scenario,n,condition,schedules[identity] if condition=='dynamic' else [],saved)
        for field,value in projected.items():
            expected_value='' if value is None else str(value)
            assert row[field]==expected_value,(key,field,row[field],expected_value)
    assert seen==expected
    return {'episodes':len(rows),'steps_replayed':steps,'test_maps':len(scenarios),
            'empty_schedules':sum(not s for s in schedules.values()),'all_decisions_replayed':True,
            'identical_active_event_prefixes':True,'source_snapshots_match':True,
            'model_digests_match':True,'actual_collisions':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path); parser.add_argument('--output',type=Path)
    args=parser.parse_args(); result=audit(args.run)
    if args.output:
        with args.output.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
