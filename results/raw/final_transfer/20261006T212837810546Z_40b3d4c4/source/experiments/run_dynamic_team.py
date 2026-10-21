"""Frozen-policy static/dynamic paired team evaluation; no training."""
import argparse
import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import torch
from algorithms.dqn import DQNAgent,DQNConfig
from evaluation.team_protocol import ROOT,create_run,generate_bank
from evaluation.dynamic_team_protocol import make_env,rollout,team_schedule

FIELDS=('method','seed','map_id','map_seed','n_agents','condition','scheduled_events','events_seen',
    'applied_events','rejected_events','success','failure_reason','steps','makespan','sum_arrival_times',
    'total_moves','path_cost','episode_reward','conflict_attempts','vertex_conflicts','swap_conflicts',
    'actual_collisions','plan_calls','plan_failures','expanded_nodes','planning_seconds',
    'decision_seconds','inference_seconds','episode_seconds')


def load_reference(profile):
    if set(profile) != {'schema_version','purpose','training_run','add_tick','remove_tick'} or profile['schema_version'] != 1:
        raise ValueError('Unexpected dynamic-team profile')
    if profile['purpose'] not in ('dynamic_team_transfer','dynamic_team_smoke'):
        raise ValueError('Unsupported dynamic-team purpose')
    a,b=profile['add_tick'],profile['remove_tick']
    if type(a) is not int or type(b) is not int or not 1 <= a < b:
        raise ValueError('Schedule ticks must be increasing positive integers')
    run=Path(profile['training_run'])
    if not run.is_absolute(): run=ROOT/run
    if not (run/'COMPLETE.json').is_file(): raise ValueError('Completed CP-06b run required')
    config=json.loads((run/'config.json').read_text())
    if b > config['map_spec']['max_steps']: raise ValueError('Schedule exceeds training evaluation horizon')
    bank=json.loads((run/'map_bank.json').read_text())
    if json.loads(json.dumps(generate_bank(config))) != bank: raise ValueError('Saved bank mismatch')
    agents,models={},[]
    for mode in ('solo','shared'):
        for seed in config['seeds']:
            path=run/'models'/f'{mode}_seed_{seed}.pt'
            agent,metadata=DQNAgent.load(path)
            if agent.observation_version != 2 or agent.seed != seed or metadata['config'] != config or metadata['mode'] != mode:
                raise ValueError('Model contract mismatch')
            agents[(mode,seed)]=agent
            models.append({'method':mode,'seed':seed,'path':str(path.resolve()),
                           'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for seed in config['seeds']:
        agents[('untrained',seed)]=DQNAgent(DQNConfig(**config['network']),seed=seed,observation_version=2)
    return config,bank,agents,models


def result_row(method,seed,scenario,n,condition,schedule,result):
    info=result['final_info']
    history=info.get('change_history',[])
    return {'method':method,'seed':seed,'map_id':scenario['map_id'],'map_seed':scenario['map_seed'],
        'n_agents':n,'condition':condition,'scheduled_events':len(schedule),'events_seen':len(history),
        'applied_events':sum(e['status']=='applied' for e in history),
        'rejected_events':sum(e['status']=='rejected_occupied' for e in history),
        'success':int(info['success']),'failure_reason':info['failure_reason'],'steps':info['elapsed_steps'],
        'makespan':info['makespan'],'sum_arrival_times':sum(info['arrival_steps']) if info['success'] else None,
        'total_moves':info['total_moves'],'path_cost':info['path_cost'],'episode_reward':sum(info['episode_rewards']),
        'conflict_attempts':sum(info['conflict_attempts']),'vertex_conflicts':info['vertex_conflicts'],
        'swap_conflicts':info['swap_conflicts'],'actual_collisions':info['actual_collisions'],
        'plan_calls':len(result['planning_calls']),'plan_failures':result['plan_failures'],
        'expanded_nodes':None if seed is not None else result['expanded_nodes'],
        'planning_seconds':None if seed is not None else result['planning_seconds'],
        'decision_seconds':result['decision_seconds'],'inference_seconds':result['decision_seconds'] if seed is not None else None,
        'episode_seconds':result['episode_seconds']}


def evaluate(profile,output_root):
    config,bank,agents,models=load_reference(profile)
    selected=bank['partitions']['test'][:2] if profile['purpose']=='dynamic_team_smoke' else bank['partitions']['test']
    schedules={s['map_id']:[asdict(e) for e in team_schedule(s,profile['add_tick'],profile['remove_tick'])] for s in selected}
    directory=create_run(output_root,profile,bank,'dynamic_team_evaluation')
    (directory/'training_config.json').write_text(json.dumps(config,indent=2)+'\n')
    (directory/'models.json').write_text(json.dumps(models,indent=2)+'\n')
    (directory/'schedules.json').write_text(json.dumps(schedules,indent=2)+'\n')
    metadata_path=directory/'metadata.json'
    metadata=json.loads(metadata_path.read_text())
    metadata.update(dynamic_rules='safe distant-cell add/remove; no future-event knowledge; early completion stops events',
        controller_rules='replan on graph changes/execution deviations; no plan means wait; frozen controls retry independent routes',
        empty_schedules=sum(not s for s in schedules.values()),evaluation_map_ids=list(schedules),
        limitations='static-trained policies; previously used CP-06b test maps; local vs full-map information; mild route-dependent perturbation',
        no_online_training=True)
    metadata_path.write_text(json.dumps(metadata,indent=2)+'\n')
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    original={key:({k:v.clone() for k,v in a.online.state_dict().items()},a.updates) for key,a in agents.items()}
    methods=[(name,None) for name in ('bfs','dijkstra','astar','bfs_frozen','dijkstra_frozen','astar_frozen')]+list(agents)
    count=0
    with (directory/'raw_results.csv').open('w',newline='',encoding='utf-8') as cf, \
         (directory/'trajectories.jsonl').open('w',encoding='utf-8') as tf:
        writer=csv.DictWriter(cf,FIELDS); writer.writeheader()
        for scenario in selected:
            for n in (2,4):
                for condition in ('static','dynamic'):
                    schedule=schedules[scenario['map_id']] if condition=='dynamic' else []
                    for method,seed in methods:
                        env=make_env(scenario,config['map_spec']['max_steps'],n,condition,profile['add_tick'],profile['remove_tick'])
                        result=rollout(env,agents.get((method,seed)),
                            method.removesuffix('_frozen') if seed is None else None,method.endswith('_frozen'))
                        writer.writerow(result_row(method,seed,scenario,n,condition,schedule,result))
                        tf.write(json.dumps({'method':method,'seed':seed,'map_id':scenario['map_id'],
                                             'n_agents':n,'condition':condition,'rollout':result})+'\n')
                        count+=1
            print(f'Evaluated map {scenario["map_seed"]}',flush=True)
    for key,a in agents.items():
        weights,updates=original[key]
        if updates != a.updates or any(not torch.equal(weights[k],v) for k,v in a.online.state_dict().items()):
            raise RuntimeError('Evaluation changed model weights or updates')
    (directory/'COMPLETE.json').write_text(json.dumps({'episodes':count,'test_maps':len(selected),
        'methods_per_scenario':len(methods),'no_online_training':True,'models_unchanged':True},indent=2)+'\n')
    print(f'Dynamic team evaluation saved: {directory}',flush=True)
    return directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/dynamic_team.json')
    parser.add_argument('--output-root',type=Path,default=ROOT/'results/raw/dynamic_team')
    parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args(); profile=json.loads(args.config.read_text())
    if args.smoke: profile['purpose']='dynamic_team_smoke'
    evaluate(profile,args.output_root)


if __name__=='__main__': main()
