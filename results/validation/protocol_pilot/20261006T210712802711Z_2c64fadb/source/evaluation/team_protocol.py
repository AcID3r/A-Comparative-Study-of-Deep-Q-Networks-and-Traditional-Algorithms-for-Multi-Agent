"""Frozen static-team scenarios, source snapshots and greedy rollouts."""
import hashlib
import json
import random
from time import perf_counter
from pathlib import Path
from algorithms.bfs import bfs
from algorithms.dqn import DQNConfig, epsilon_at, positive_integer
from algorithms.prioritized import prioritized_plan, plan_actions
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv
from environments.random_maps import build_bank, map_id
from evaluation.varied_protocol import ROOT, new_run


def validate(config):
    expected = {'schema_version','purpose','map_spec','partitions','excluded_bank','seeds','cycles',
        'batch_size','replay_capacity','warmup_transitions','train_every_transitions','epsilon_initial',
        'epsilon_final','epsilon_decay_cycles','evaluate_every_cycles','network'}
    if not isinstance(config,dict) or set(config) != expected or type(config['schema_version']) is not int or config['schema_version'] != 1:
        raise ValueError('Unexpected static-team configuration')
    if config['purpose'] not in ('static_team_development','static_team_smoke'):
        raise ValueError('Unsupported purpose')
    for key in ('cycles','batch_size','replay_capacity','warmup_transitions','train_every_transitions','epsilon_decay_cycles','evaluate_every_cycles'):
        positive_integer(config[key],key)
    if config['batch_size'] > config['replay_capacity'] or config['warmup_transitions'] < config['batch_size']:
        raise ValueError('Replay/warmup cannot accommodate batch')
    seeds = config['seeds']
    if not isinstance(seeds,list) or not seeds or any(type(s) is not int or s < 0 for s in seeds) or len(set(seeds)) != len(seeds):
        raise ValueError('Seeds must be unique nonnegative integers')
    if list(config['partitions']) != ['train','validation','test']:
        raise ValueError('Expected train/validation/test partitions')
    spec = config['map_spec']
    if set(spec) != {'rows','cols','density','max_steps'}:
        raise ValueError('Unexpected map specification')
    for key in ('rows','cols','max_steps'):
        positive_integer(spec[key],key)
    DQNConfig(**config['network'])
    epsilon_at(0,config['epsilon_initial'],config['epsilon_final'],config['epsilon_decay_cycles'])


def generate_bank(config):
    validate(config)
    excluded_path = Path(config['excluded_bank'])
    if not excluded_path.is_absolute(): excluded_path = ROOT/excluded_path
    prior = json.loads(excluded_path.read_text(encoding='utf-8'))
    excluded = {s['map_id'] for group in prior['partitions'].values() for s in group}
    fixed = json.loads((ROOT/'configs/dqn_fixed.json').read_text(encoding='utf-8'))['map']
    excluded.add(map_id(fixed['rows'],fixed['cols'],fixed['obstacles']))
    spec = config['map_spec']
    bank = build_bank(spec['rows'],spec['cols'],spec['density'],config['partitions'],excluded_ids=excluded)
    bank['excluded_ids'] = sorted(excluded)
    bank['excluded_bank_sha256'] = hashlib.sha256(excluded_path.read_bytes()).hexdigest()
    for group in bank['partitions'].values():
        for scenario in group:
            graph = graph_for(scenario)
            free = [(r,c) for r in range(graph.rows) for c in range(graph.cols) if graph.is_free((r,c))]
            if len(free) < 8: raise ValueError('Four-agent scenarios need eight free endpoints')
            endpoints = random.Random(scenario['map_seed']+70000).sample(free,8)
            scenario['team_starts'], scenario['team_goals'] = endpoints[:4],endpoints[4:]
            scenario['individual_reachable'] = [bfs(graph,s,g) is not None for s,g in zip(endpoints[:4],endpoints[4:])]
    return bank


def graph_for(scenario):
    return GridGraph(scenario['rows'],scenario['cols'],frozenset(map(tuple,scenario['obstacles'])))


def environment(scenario,horizon,n_agents=2,route=None):
    starts,goals = tuple(map(tuple,scenario['team_starts'])),tuple(map(tuple,scenario['team_goals']))
    if route is not None: starts,goals = (starts[route],),(goals[route],)
    else: starts,goals = starts[:n_agents],goals[:n_agents]
    return MultiAgentEnv(graph_for(scenario),starts,goals,max_steps=horizon)


def create_run(output_root,config,bank,purpose):
    directory = new_run(output_root,config,bank,purpose)
    path = directory/'metadata.json'
    metadata = json.loads(path.read_text())
    metadata.update(split_rules='geometry-disjoint banks exclude CP-04 fixed map and all CP-05 geometries; unreachable tasks retained',
        dynamic_rules='none: static team development',
        limitations='5x5 static unit costs; seeded distinct endpoints; local v2 DQN vs full-map prioritized planning; matched tasks, actual updates differ',
        replay_rules='all agents including finished WAIT transitions; mask on team end or timeout; all rewards retained',
        budget_rules='one shared two-agent episode vs two solo episodes per cycle')
    path.write_text(json.dumps(metadata,indent=2)+'\n')
    return directory


def rollout(env,agent=None,method=None):
    began = perf_counter()
    obs,info = env.reset(seed=0)
    plan = None
    if method:
        plan = prioritized_plan(env.graph,env.starts,env.goals,method=method,max_steps=env.max_steps)
        if not plan.success:
            return {'success':False,'failure_reason':'planning_failure','final_info':None,'trace':[],
                'planning':{'paths':None,'failed_agent':plan.failed_agent,'failure_reason':plan.failure_reason,
                    'expanded_nodes':plan.expanded_nodes,'seconds':plan.planning_time_seconds},
                'decision_seconds':0.0,'episode_seconds':perf_counter()-began}
    trace,decision = [],0.0
    for tick in range(env.max_steps):
        if info['terminated'] or info['truncated']: break
        before = obs
        started = perf_counter()
        actions = plan_actions(plan.paths,tick) if plan else tuple(
            4 if t is not None else agent.act(o,epsilon=0) for o,t in zip(obs,info['arrival_steps']))
        decision += perf_counter()-started
        obs,rewards,term,trunc,info = env.step(actions)
        trace.append({'observations':before,'actions':actions,'next_observations':obs,'rewards':rewards,
                      'terminated':term,'truncated':trunc,'info':info})
    return {'success':info['success'],'failure_reason':info['failure_reason'],'final_info':info,'trace':trace,
        'planning':None if not plan else {'paths':plan.paths,'failed_agent':None,'failure_reason':None,
            'expanded_nodes':plan.expanded_nodes,'seconds':plan.planning_time_seconds},
        'decision_seconds':decision,'episode_seconds':perf_counter()-began}


def validation_cases(agent,config,bank):
    return [{'map_id':s['map_id'],'n_agents':2,'rollout':rollout(environment(s,config['map_spec']['max_steps']),agent)}
            for s in bank['partitions']['validation']]
