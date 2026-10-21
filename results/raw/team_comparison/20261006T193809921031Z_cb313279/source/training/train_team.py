"""Task-matched static shared-policy and solo v2 DQN training."""
import argparse
import csv
import json
import random
from pathlib import Path
from time import perf_counter
import torch
from algorithms.dqn import DQNAgent,DQNConfig,ReplayBuffer,Transition,epsilon_at
from evaluation.team_protocol import ROOT,generate_bank,create_run,environment,validation_cases

MODES = ('solo','shared')
EPISODE_FIELDS = ('mode','seed','cycle','route','map_id','epsilon','steps','agent_tasks','transitions',
    'cumulative_transitions','updates','success','total_moves','conflict_attempts','episode_reward','training_seconds')
UPDATE_FIELDS = ('mode','seed','cycle','transition_count','update','loss','gradient_norm_before_clip','target_synced')


def episode_transitions(obs,actions,rewards,next_obs,terminated,truncated):
    return tuple(Transition(o,a,r,n,terminated,truncated,observation_version=2)
                 for o,a,r,n in zip(obs,actions,rewards,next_obs))


def train(config,output_root):
    bank = generate_bank(config)
    directory = create_run(output_root,config,bank,'static_team_training')
    (directory/'models').mkdir()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    summaries = []
    with (directory/'training_episodes.csv').open('w',newline='',encoding='utf-8') as ef, \
         (directory/'optimizer_updates.csv').open('w',newline='',encoding='utf-8') as uf, \
         (directory/'training_actions.jsonl').open('w',encoding='utf-8') as tf, \
         (directory/'validation.jsonl').open('w',encoding='utf-8') as vf:
        ew,uw = csv.DictWriter(ef,EPISODE_FIELDS),csv.DictWriter(uf,UPDATE_FIELDS)
        ew.writeheader(); uw.writeheader()
        for mode in MODES:
            for seed in config['seeds']:
                agent = DQNAgent(DQNConfig(**config['network']),seed=seed,observation_version=2)
                replay = ReplayBuffer(config['replay_capacity'],seed=seed+10000)
                maps = random.Random(seed+20000)
                count = ticks = episodes = 0
                elapsed = 0.0
                checks = validation_cases(agent,config,bank)
                vf.write(json.dumps({'mode':mode,'seed':seed,'cycle':0,'phase':'initial','cases':checks})+'\n')
                for cycle in range(1,config['cycles']+1):
                    scenario = maps.choice(bank['partitions']['train'])
                    epsilon = epsilon_at(cycle-1,config['epsilon_initial'],config['epsilon_final'],config['epsilon_decay_cycles'])
                    for route in ((0,1) if mode == 'solo' else (None,)):
                        env = environment(scenario,config['map_spec']['max_steps'],route=route)
                        obs,info = env.reset(seed=seed)
                        actions_log = []
                        start_count = count
                        began = perf_counter()
                        for _ in range(env.max_steps):
                            if info['terminated'] or info['truncated']: break
                            actions = tuple(4 if t is not None else agent.act(o,epsilon=epsilon) for o,t in zip(obs,info['arrival_steps']))
                            nxt,rewards,term,trunc,info = env.step(actions)
                            # Insert in stable agent order, and trigger updates by
                            # transition count rather than joint ticks.
                            for transition in episode_transitions(obs,actions,rewards,nxt,term,trunc):
                                replay.append(transition); count += 1
                                if count >= config['warmup_transitions'] and count % config['train_every_transitions'] == 0:
                                    report = agent.train_batch(replay.sample(config['batch_size']))
                                    uw.writerow({'mode':mode,'seed':seed,'cycle':cycle,'transition_count':count,
                                                 'update':agent.updates,**report})
                            actions_log.append(actions)
                            obs = nxt; ticks += 1
                        seconds = perf_counter()-began
                        elapsed += seconds; episodes += 1
                        ew.writerow({'mode':mode,'seed':seed,'cycle':cycle,'route':route,'map_id':scenario['map_id'],
                            'epsilon':epsilon,'steps':info['elapsed_steps'],'agent_tasks':env.n_agents,
                            'transitions':count-start_count,'cumulative_transitions':count,'updates':agent.updates,
                            'success':int(info['success']),'total_moves':info['total_moves'],
                            'conflict_attempts':sum(info['conflict_attempts']),'episode_reward':sum(info['episode_rewards']),
                            'training_seconds':seconds})
                        tf.write(json.dumps({'mode':mode,'seed':seed,'cycle':cycle,'route':route,'map_id':scenario['map_id'],
                                             'actions':actions_log,'final_info':info})+'\n')
                    if cycle % config['evaluate_every_cycles'] == 0 or cycle == config['cycles']:
                        checks = validation_cases(agent,config,bank)
                        vf.write(json.dumps({'mode':mode,'seed':seed,'cycle':cycle,'phase':'validation','cases':checks})+'\n')
                        ef.flush(); uf.flush(); tf.flush(); vf.flush()
                        print(f'{mode} seed={seed} cycle={cycle}/{config["cycles"]} validation={sum(c["rollout"]["success"] for c in checks)}/{len(checks)} updates={agent.updates}',flush=True)
                model = directory/'models'/f'{mode}_seed_{seed}.pt'
                agent.save(model,metadata={'config':config,'mode':mode,'transitions':count,'budget':'two navigation tasks per cycle'})
                loaded,_ = DQNAgent.load(model)
                reloaded = validation_cases(loaded,config,bank)
                if [[s['actions'] for s in c['rollout']['trace']] for c in checks] != [[s['actions'] for s in c['rollout']['trace']] for c in reloaded]:
                    raise RuntimeError('Reload changed final validation actions')
                summaries.append({'mode':mode,'seed':seed,'cycles':config['cycles'],'episodes':episodes,
                    'agent_tasks':2*config['cycles'],'transitions':count,'joint_ticks':ticks,'updates':agent.updates,
                    'training_seconds':elapsed,'validation_successes':sum(c['rollout']['success'] for c in checks),
                    'validation_cases':len(checks),'reload_matches':True})
    (directory/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    (directory/'COMPLETE.json').write_text(json.dumps({'models':len(summaries),'test_maps_used':False,'four_agent_training':False},indent=2)+'\n')
    print(f'Team training saved: {directory}',flush=True)
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'configs/dqn_team.json')
    parser.add_argument('--output-root',type=Path,default=ROOT/'results/raw/dqn_team')
    parser.add_argument('--smoke',action='store_true')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.smoke: config.update(purpose='static_team_smoke',seeds=[config['seeds'][0]],cycles=20,evaluate_every_cycles=10)
    train(config,args.output_root)


if __name__ == '__main__': main()
