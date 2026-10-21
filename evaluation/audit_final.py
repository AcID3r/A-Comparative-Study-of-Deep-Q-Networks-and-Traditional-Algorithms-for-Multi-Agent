"""Regenerate cases and replay each saved policy/controller; fail on altered data."""
import argparse
import csv
import json
import math
from dataclasses import asdict
from pathlib import Path
import torch
from evaluation.final_protocol import generate_bank,reference,method_list,metrics,digest
from evaluation.dynamic_team_protocol import make_env,rollout,team_schedule
from experiments.run_dynamic_team import result_row
from experiments.run_final import STABLE_FIELDS


def canonical(value): return json.loads(json.dumps(value))


def audit(directory):
    directory=Path(directory)
    config=json.loads((directory/'config.json').read_text()); bank=json.loads((directory/'map_bank.json').read_text())
    exclusions=json.loads((directory/'exclusions.json').read_text())
    assert bank==generate_bank(config,bank['phase'],exclusions),'bank mismatch'
    training,agents,models=reference(config)
    assert models==json.loads((directory/'models.json').read_text())
    assert training==json.loads((directory/'training_config.json').read_text())
    metadata=json.loads((directory/'metadata.json').read_text())
    for path,value in metadata['source_sha256'].items(): assert digest(directory/'source'/path)==value
    complete=json.loads((directory/'COMPLETE.json').read_text())
    assert complete['models_unchanged'] and complete['no_online_training']
    assert complete['phase']==metadata['phase']==bank['phase']
    repeats=1 if bank['phase']=='pilot' else config['timing_repeats']
    assert complete['timing_repeats']==metadata['timing_repeats']==repeats
    scenarios={s['map_id']:s for s in bank['scenarios']}
    schedules={s['map_id']:[asdict(e) for e in team_schedule(s,config['add_tick'],config['remove_tick'])] for s in scenarios.values()}
    assert canonical(schedules)==json.loads((directory/'schedules.json').read_text())
    expected={(s,n,c,m,seed) for s in scenarios for n in config['agent_counts'] for c in config['conditions'] for m,seed in method_list(config)}
    with (directory/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==len(expected)==complete['episodes'] and complete['scenarios']==len(scenarios)
    torch.set_num_threads(1); seen=set(); steps=0; histories={}
    with (directory/'trajectories.jsonl').open() as f:
        for row,line in zip(rows,f,strict=True):
            trace=json.loads(line); key=(trace['map_id'],trace['n_agents'],trace['condition'],trace['method'],trace['seed'])
            assert key in expected and key not in seen; seen.add(key)
            identity,n,condition,method,seed=key; scenario=scenarios[identity]; saved=trace['rollout']
            env=make_env(scenario,scenario['max_steps'],n,condition,config['add_tick'],config['remove_tick'])
            actual=rollout(env,agents.get((method,seed)),method.removesuffix('_frozen') if seed is None else None,method.endswith('_frozen'))
            for field in STABLE_FIELDS: assert canonical(actual[field])==saved[field],(key,field)
            assert len(actual['planning_calls'])==len(saved['planning_calls'])
            for a,b in zip(actual['planning_calls'],saved['planning_calls']):
                for field in a:
                    if field!='seconds': assert canonical(a[field])==b[field],(key,field)
                assert math.isfinite(b['seconds']) and b['seconds']>=0
            assert saved['planning_seconds']==sum(c['seconds'] for c in saved['planning_calls'])
            assert len(trace['timing_repeats'])==repeats
            for timing in trace['timing_repeats']:
                assert set(timing)=={'decision_seconds','planning_seconds','episode_seconds'}
                assert all(math.isfinite(v) and v>=0 for v in timing.values())
            assert trace['timing_repeats'][0]=={k:saved[k] for k in trace['timing_repeats'][0]}
            info=saved['final_info']; assert info['actual_collisions']==0
            steps+=len(saved['trace'])
            if condition=='dynamic':
                history=info['change_history']
                expected_history=[e|dict(status='applied',graph_version=i+1) for i,e in enumerate(schedules[identity]) if e['tick']<=info['prepared_tick']]
                assert history==canonical(expected_history),(key,'event history mismatch')
                previous=histories.setdefault(identity,history); length=min(len(previous),len(history))
                assert previous[:length]==history[:length]
                if len(history)>len(previous): histories[identity]=history
            projected=result_row(method,seed,scenario,n,condition,schedules[identity] if condition=='dynamic' else [],saved)|metrics(scenario,n,condition,saved,config['add_tick'])
            assert set(row)==set(projected)
            for field,value in projected.items(): assert row[field]==('' if value is None else str(value)),(key,field)
    assert seen==expected
    return dict(episodes=len(rows),steps_replayed=steps,scenarios=len(scenarios),strata=len({s['stratum'] for s in scenarios.values()}),
        empty_schedules=sum(not v for v in schedules.values()),all_decisions_replayed=True,
        geometry_exclusions_checked=True,active_event_prefixes_match=True,source_and_models_match=True,actual_collisions=0,
        timing_repeats=repeats,phase=bank['phase'])


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('run',type=Path)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    result=audit(args.run)
    with args.output.open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
