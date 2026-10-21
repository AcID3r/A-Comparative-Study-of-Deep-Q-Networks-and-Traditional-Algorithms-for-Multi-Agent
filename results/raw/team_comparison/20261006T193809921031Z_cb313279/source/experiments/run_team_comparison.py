"""Matched held-out static two/four-agent comparisons; no online learning."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import torch
from algorithms.dqn import DQNAgent,DQNConfig
from evaluation.team_protocol import ROOT,create_run,environment,generate_bank,rollout

FIELDS = ('method','seed','map_id','map_seed','n_agents','individually_reachable','success','failure_reason',
          'steps','makespan','sum_arrival_times','total_moves','path_cost','conflict_attempts','vertex_conflicts',
          'swap_conflicts','actual_collisions','episode_reward','decision_seconds','planning_seconds',
          'inference_seconds','episode_seconds','expanded_nodes')


def evaluate(training_run,output_root):
    training_run = Path(training_run).resolve()
    if not (training_run/'COMPLETE.json').is_file(): raise ValueError('Completed training run required')
    config = json.loads((training_run/'config.json').read_text())
    bank = json.loads((training_run/'map_bank.json').read_text())
    if json.loads(json.dumps(generate_bank(config))) != bank: raise ValueError('Training scenario bank mismatch')
    agents,models = {},[]
    for mode in ('solo','shared'):
        for seed in config['seeds']:
            path = training_run/'models'/f'{mode}_seed_{seed}.pt'
            agent,metadata = DQNAgent.load(path)
            if agent.observation_version != 2 or metadata['mode'] != mode or metadata['config'] != config:
                raise ValueError('Model training contract mismatch')
            agents[(mode,seed)] = agent
            models.append({'method':mode,'seed':seed,'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for seed in config['seeds']:
        agents[('untrained',seed)] = DQNAgent(DQNConfig(**config['network']),seed=seed,observation_version=2)
    directory = create_run(output_root,config,bank,'static_team_evaluation')
    (directory/'models.json').write_text(json.dumps(models,indent=2)+'\n')
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    count = 0
    methods = [(name,None) for name in ('bfs','dijkstra','astar')] + list(agents)
    with (directory/'raw_results.csv').open('w',newline='',encoding='utf-8') as cf, \
         (directory/'trajectories.jsonl').open('w',encoding='utf-8') as tf:
        writer = csv.DictWriter(cf,FIELDS); writer.writeheader()
        for scenario in bank['partitions']['test']:
            for n in (2,4):
                for method,seed in methods:
                    result = rollout(environment(scenario,config['map_spec']['max_steps'],n),
                                     agents.get((method,seed)),method if seed is None else None)
                    info,p = result['final_info'],result['planning']
                    row = {'method':method,'seed':seed,'map_id':scenario['map_id'],'map_seed':scenario['map_seed'],
                        'n_agents':n,'individually_reachable':int(all(scenario['individual_reachable'][:n])),
                        'success':int(result['success']),'failure_reason':result['failure_reason'],
                        'steps':None if info is None else info['elapsed_steps'],
                        'makespan':None if info is None else info['makespan'],
                        'sum_arrival_times':sum(info['arrival_steps']) if result['success'] else None,
                        'total_moves':0 if info is None else info['total_moves'],
                        'path_cost':0 if info is None else info['path_cost'],
                        'conflict_attempts':0 if info is None else sum(info['conflict_attempts']),
                        'vertex_conflicts':0 if info is None else info['vertex_conflicts'],
                        'swap_conflicts':0 if info is None else info['swap_conflicts'],
                        'actual_collisions':0 if info is None else info['actual_collisions'],
                        'episode_reward':None if info is None else sum(info['episode_rewards']),
                        'decision_seconds':result['decision_seconds'],'planning_seconds':None if p is None else p['seconds'],
                        'inference_seconds':result['decision_seconds'] if seed is not None else None,
                        'episode_seconds':result['episode_seconds'],'expanded_nodes':None if p is None else p['expanded_nodes']}
                    writer.writerow(row)
                    tf.write(json.dumps({'method':method,'seed':seed,'map_id':scenario['map_id'],'n_agents':n,'rollout':result})+'\n')
                    count += 1
    (directory/'COMPLETE.json').write_text(json.dumps({'episodes':count,'test_maps':len(bank['partitions']['test']),
                                                     'methods_per_scenario':len(methods)},indent=2)+'\n')
    print(f'Team evaluation saved: {directory}',flush=True)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('training_run',type=Path)
    parser.add_argument('--output-root',type=Path,default=ROOT/'results/raw/team_comparison')
    args = parser.parse_args()
    evaluate(args.training_run,args.output_root)


if __name__ == '__main__': main()
