"""CP-07 frozen transfer protocol: fresh cases, explicit gaps and denominators."""
import hashlib
import json
import math
import random
from itertools import combinations
from pathlib import Path
from algorithms.bfs import bfs
from environments.random_maps import map_id
from evaluation.team_protocol import ROOT, graph_for
from experiments.run_dynamic_team import load_reference


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(config):
    reference = json.loads((ROOT/'configs/final_experiment.json').read_text())
    # This is a fixed research protocol, not a parameter-tuning interface.
    if config != reference or any(type(config[k]) is not int for k in (
        'schema_version','add_tick','remove_tick','pilot_maps_per_stratum',
        'final_maps_per_stratum','pilot_first_seed','final_first_seed',
        'candidate_stride','timing_repeats')):
        raise ValueError('Use the frozen final experiment configuration unchanged')
    if config['schema_version'] != 1 or config['sizes'] != [5,10,15] or config['seeds'] != list(range(5)):
        raise ValueError('Unsupported final experiment protocol')
    if not 1 <= config['add_tick'] < config['remove_tick'] <= min(config['horizons'].values()):
        raise ValueError('Invalid event/horizon contract')


def reference(config):
    training, _, agents, models = load_reference(dict(schema_version=1,
        purpose='dynamic_team_transfer',training_run=config['training_run'],
        add_tick=config['add_tick'],remove_tick=config['remove_tick']))
    if training['seeds'] != config['seeds']:
        raise ValueError('Training seeds do not match final seeds')
    return training, agents, models


def collect_exclusions():
    """Capture all existing development geometries, including baseline smoke maps."""
    sources = sorted((ROOT/'results/raw').glob('*/*/map_bank.json'))
    sources += sorted((ROOT/'results/raw/static_smoke').glob('*/scenarios.json'))
    ids, fingerprints = set(), {}
    def visit(value):
        if isinstance(value,dict):
            if {'rows','cols','obstacles'} <= value.keys():
                ids.add(map_id(value['rows'],value['cols'],value['obstacles']))
            for child in value.values(): visit(child)
        elif isinstance(value,list):
            for child in value: visit(child)
    for path in sources + [ROOT/'configs/dqn_fixed.json']:
        visit(json.loads(path.read_text()))
        fingerprints[path.relative_to(ROOT).as_posix()] = digest(path)
    return {'excluded_ids':sorted(ids),'development_sources':fingerprints}


def generate_bank(config, phase, exclusions):
    validate(config)
    if phase not in ('pilot','final'): raise ValueError('Unknown phase')
    used = set(exclusions['excluded_ids'])
    bank = {'phase':phase,'scenarios':[],'rejected_candidates':[],
            'reachability_filter':'none; initially unreachable tasks retained'}
    index = 0
    for size in config['sizes']:
        for density in config['densities']:
            for arrangement in config['arrangements']:
                first = config[f'{phase}_first_seed'] + index*config['candidate_stride']
                count = config[f'{phase}_maps_per_stratum']; accepted = 0
                for seed in range(first, first+config['candidate_stride']):
                    rng = random.Random(seed)
                    walls = sorted((r,c) for r in range(size) for c in range(size) if rng.random()<density)
                    identity = map_id(size,size,walls)
                    reason = None
                    scenario = dict(map_id=identity,map_seed=seed,rows=size,cols=size,obstacles=walls)
                    graph = graph_for(scenario)
                    free = [(r,c) for r in range(size) for c in range(size) if graph.is_free((r,c))]
                    erng = random.Random(seed+70000)
                    if identity in used: reason='duplicate_geometry'
                    elif len(free)<8: reason='fewer_than_eight_free_cells'
                    elif arrangement == 'uniform':
                        endpoints = erng.sample(free,8)
                        starts,goals = endpoints[:4],endpoints[4:]
                    else:
                        left = [p for p in free if p[1]==0]
                        right = [p for p in free if p[1]==size-1]
                        if min(len(left),len(right))<4: reason='fewer_than_four_free_boundary_endpoints'
                        else:
                            starts = sorted(erng.sample(left,4))
                            goals = sorted(erng.sample(right,4),reverse=True)
                    if reason:
                        bank['rejected_candidates'].append(dict(seed=seed,stratum=index,reason=reason)); continue
                    used.add(identity)
                    paths = [bfs(graph,s,g) for s,g in zip(starts,goals)]
                    scenario.update(team_starts=starts,team_goals=goals,
                        density_requested=density,density_realized=len(walls)/(size*size),
                        arrangement=arrangement,stratum=index,max_steps=config['horizons'][str(size)],
                        individual_optimal_moves=[None if p is None else len(p)-1 for p in paths],
                        route_overlap_pairs={str(n):sum(bool(set(paths[i] or []) & set(paths[j] or []))
                            for i,j in combinations(range(n),2)) for n in config['agent_counts']})
                    bank['scenarios'].append(scenario); accepted += 1
                    if accepted == count: break
                if accepted != count: raise ValueError('Insufficient cases in declared candidate range')
                index += 1
    return json.loads(json.dumps(bank))


def metrics(scenario,n,condition,result,add_tick):
    info = result['final_info']; optimum = scenario['individual_optimal_moves'][:n]
    lower_bound = sum(optimum) if all(x is not None for x in optimum) else None
    gap,reason = None,None
    if condition!='static': reason='dynamic optimum not computed'
    elif n!=1: reason='independent paths are only a team lower bound'
    elif optimum[0] is None: reason='initial goal unreachable'
    elif optimum[0]==0: reason='zero reference'
    elif not info['success']: reason='episode failed'
    else: gap=(info['total_moves']-optimum[0])/optimum[0]
    exposed = any(e['operation']=='add' and e['status']=='applied' for e in info.get('change_history',[]))
    return dict(grid_size=scenario['rows'],density_requested=scenario['density_requested'],
        density_realized=scenario['density_realized'],arrangement=scenario['arrangement'],
        max_steps=scenario['max_steps'],route_overlap_pairs=scenario['route_overlap_pairs'][str(n)],
        initially_unreachable_agents=sum(x is None for x in optimum),
        initial_independent_lower_bound=lower_bound,static_single_agent_gap=gap,gap_undefined_reason=reason,
        addition_exposed=int(exposed),steps_after_addition=info['makespan']-add_tick+1
            if exposed and info['success'] else None)


def method_list(config):
    return [(m,None) for m in config['methods'] if m not in ('solo','shared','untrained')] + [
        (m,s) for m in ('solo','shared','untrained') for s in config['seeds']]


def freeze(config, pilot_bank, output):
    validate(config)
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    exclusions=collect_exclusions()
    exclusions['excluded_ids']=sorted(set(exclusions['excluded_ids'])|{s['map_id'] for s in pilot_bank['scenarios']})
    (output/'exclusions.json').write_text(json.dumps(exclusions,indent=2)+'\n')
    _,_,models=reference(config)
    sources={p.relative_to(ROOT).as_posix():digest(p) for folder in (
        'algorithms','environments','evaluation','experiments') for p in (ROOT/folder).glob('*.py')}
    sources['configs/final_experiment.json']=digest(ROOT/'configs/final_experiment.json')
    manifest=dict(schema_version=1,config=config,source_sha256=sources,models=models,
        exclusions_sha256=digest(output/'exclusions.json'),pilot_ids=[s['map_id'] for s in pilot_bank['scenarios']],
        final_maps_generated=False,final_maps=120,final_unique_episodes=15120,timing_repeats=3,
        analysis_rules='five-seed descriptive mean/std; matched cases; failures retained; no significance/architecture-only/speed-superiority claim')
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return output


def check_freeze(config,directory):
    directory=Path(directory); manifest=json.loads((directory/'manifest.json').read_text())
    if manifest['config'] != config: raise ValueError('Frozen configuration changed')
    for path,value in manifest['source_sha256'].items():
        if digest(ROOT/path)!=value: raise ValueError(f'Frozen source changed: {path}')
    if digest(directory/'exclusions.json')!=manifest['exclusions_sha256']:
        raise ValueError('Exclusions changed')
    if reference(config)[2]!=manifest['models']: raise ValueError('Frozen models changed')
    return json.loads((directory/'exclusions.json').read_text())
