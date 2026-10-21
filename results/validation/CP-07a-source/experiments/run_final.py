"""Run CP-07a validation or the sealed CP-07b transfer matrix (never train)."""
import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
import torch
from evaluation.team_protocol import ROOT
from evaluation.varied_protocol import new_run
from evaluation.final_protocol import (validate, reference, collect_exclusions, generate_bank,
    check_freeze, method_list, metrics)
from evaluation.dynamic_team_protocol import make_env, rollout, team_schedule
from experiments.run_dynamic_team import FIELDS, result_row

EXTRA_FIELDS=('grid_size','density_requested','density_realized','arrangement','max_steps',
    'route_overlap_pairs','initially_unreachable_agents','initial_independent_lower_bound',
    'static_single_agent_gap','gap_undefined_reason','addition_exposed','steps_after_addition')
STABLE_FIELDS=('success','failure_reason','final_info','trace','expanded_nodes','plan_failures')


def evaluate(config,output_root,phase='pilot',freeze_directory=None):
    validate(config)
    if phase not in ('pilot','final'): raise ValueError('Unknown phase')
    if phase=='final' and freeze_directory is None: raise ValueError('Final run requires CP-07a freeze')
    exclusions = check_freeze(config,freeze_directory) if phase=='final' else collect_exclusions()
    bank=generate_bank(config,phase,exclusions)
    training,agents,models=reference(config)
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    methods=method_list(config)
    # One fresh rollout per timing repeat. Only repeat 0 enters outcome denominators.
    repeats=config['timing_repeats'] if phase=='final' else 1
    directory=new_run(output_root,config,bank,'protocol_pilot' if phase=='pilot' else 'final_transfer')
    for name,value in [('exclusions',exclusions),('training_config',training),('models',models)]:
        (directory/f'{name}.json').write_text(json.dumps(value,indent=2)+'\n')
    schedules={s['map_id']:[asdict(e) for e in team_schedule(s,config['add_tick'],config['remove_tick'])]
        for s in bank['scenarios']}
    (directory/'schedules.json').write_text(json.dumps(schedules,indent=2)+'\n')
    meta_path=directory/'metadata.json'; meta=json.loads(meta_path.read_text())
    meta.update(phase=phase,split_rules='fresh geometry; all recorded development maps excluded; final also excludes pilot',
        dynamic_rules='safe distant cell add 2/remove 8; shared active-event prefixes; empty schedules retained',
        limitations='static 5x5-trained v2 policies; local vs full-map inputs; crossing is an endpoint proxy, not guaranteed congestion',
        no_online_training=True,timing_repeats=repeats,
        timing_rules='fresh deterministic rollouts; repeat zero outcome only; all repeated timers stored; fixed order/no speed superiority')
    meta_path.write_text(json.dumps(meta,indent=2)+'\n')
    original={key:({k:v.clone() for k,v in a.online.state_dict().items()},a.updates) for key,a in agents.items()}
    count=0
    with (directory/'raw_results.csv').open('w',newline='') as cf, (directory/'trajectories.jsonl').open('w') as tf:
        writer=csv.DictWriter(cf,FIELDS+EXTRA_FIELDS); writer.writeheader()
        for scenario in bank['scenarios']:
            for n in config['agent_counts']:
                for condition in config['conditions']:
                    schedule=schedules[scenario['map_id']] if condition=='dynamic' else []
                    for method,seed in methods:
                        result=None; timings=[]
                        for repeat in range(repeats):
                            env=make_env(scenario,scenario['max_steps'],n,condition,config['add_tick'],config['remove_tick'])
                            actual=rollout(env,agents.get((method,seed)),method.removesuffix('_frozen') if seed is None else None,
                                method.endswith('_frozen'))
                            if result is None: result=actual
                            elif any(actual[k]!=result[k] for k in STABLE_FIELDS):
                                raise RuntimeError('Timing repetition changed deterministic outcomes')
                            timings.append({k:actual[k] for k in ('decision_seconds','planning_seconds','episode_seconds')})
                        writer.writerow(result_row(method,seed,scenario,n,condition,schedule,result)|
                            metrics(scenario,n,condition,result,config['add_tick']))
                        tf.write(json.dumps(dict(method=method,seed=seed,map_id=scenario['map_id'],n_agents=n,
                            condition=condition,rollout=result,timing_repeats=timings))+'\n')
                        count+=1
            print(f'{phase}: {scenario["rows"]}x{scenario["cols"]} {scenario["density_requested"]} {scenario["arrangement"]}',flush=True)
    for key,a in agents.items():
        weights,updates=original[key]
        if updates!=a.updates or any(not torch.equal(weights[k],v) for k,v in a.online.state_dict().items()):
            raise RuntimeError('Evaluation mutated model')
    (directory/'COMPLETE.json').write_text(json.dumps(dict(episodes=count,scenarios=len(bank['scenarios']),
        phase=phase,timing_repeats=repeats,no_online_training=True,models_unchanged=True),indent=2)+'\n')
    print(f'Saved: {directory}',flush=True)
    return directory


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final',action='store_true')
    parser.add_argument('--freeze',type=Path,default=ROOT/'results/validation/CP-07a-freeze')
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args(); phase='final' if args.final else 'pilot'
    config=json.loads((ROOT/'configs/final_experiment.json').read_text())
    output=args.output_root or ROOT/('results/raw/final_transfer' if args.final else 'results/validation/protocol_pilot')
    evaluate(config,output,phase,args.freeze if args.final else None)


if __name__=='__main__': main()
