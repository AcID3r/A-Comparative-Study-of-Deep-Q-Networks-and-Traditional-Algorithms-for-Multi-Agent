"""Stratified summaries and matched-case contrasts; repeated timers are not episodes."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean,stdev


def aggregate(rows):
    buckets=defaultdict(list)
    for r in rows:
        buckets[(int(r['grid_size']),float(r['density_requested']),r['arrangement'],int(r['n_agents']),r['condition'],r['method'])].append(r)
    result=[]
    for (size,density,arrangement,n,condition,method),cases in sorted(buckets.items()):
        good=[r for r in cases if int(r['success'])]; seeds=defaultdict(list)
        for r in cases: seeds[r['seed']].append(r)
        rates=[mean(int(r['success']) for r in v) for v in seeds.values()]
        exposed=[r for r in cases if int(r['addition_exposed'])]
        def average(field,selected):
            values=[float(r[field]) for r in selected if r[field]!='']
            return mean(values) if values else None
        result.append(dict(grid_size=size,density=density,arrangement=arrangement,n_agents=n,condition=condition,method=method,
            episodes=len(cases),successes=len(good),success_rate=len(good)/len(cases),
            seed_success_rates={s:mean(int(r['success']) for r in v) for s,v in seeds.items()},
            seed_success_std=stdev(rates) if len(rates)>1 else None,
            successful_mean_makespan=average('makespan',good),successful_mean_moves=average('total_moves',good),
            mean_conflict_attempts=average('conflict_attempts',cases),mean_planning_seconds=average('planning_seconds',cases),
            mean_inference_seconds=average('inference_seconds',cases),successful_mean_gap=average('static_single_agent_gap',good),
            addition_exposed_episodes=len(exposed),addition_exposed_successes=sum(int(r['success']) for r in exposed),
            successful_mean_steps_after_addition=average('steps_after_addition',exposed)))
    return result


def matched(rows,left,right):
    def key(r): return (r['map_id'],r['n_agents'],r['condition'],r['seed'])
    a={key(r):r for r in rows if r['method']==left}; b={key(r):r for r in rows if r['method']==right}
    if set(a)!=set(b): raise ValueError('Matched-case sets differ')
    both=[k for k in a if a[k]['success']==b[k]['success']=='1']
    return dict(left=left,right=right,pairs=len(a),both_successful=len(both),
        mean_success_difference=mean(int(a[k]['success'])-int(b[k]['success']) for k in a) if a else None,
        mean_makespan_difference_both_successful=mean(float(a[k]['makespan'])-float(b[k]['makespan']) for k in both) if both else None)


def summarize(directory,output):
    directory,output=Path(directory),Path(output)
    with (directory/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    groups=aggregate(rows); output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(groups,indent=2)+'\n')
    contrasts=[matched(rows,'shared','solo')]+[matched(rows,m,m+'_frozen') for m in ('bfs','dijkstra','astar')]
    (output/'matched_cases.json').write_text(json.dumps(contrasts,indent=2)+'\n')
    timers=[]
    with (directory/'trajectories.jsonl').open() as f:
        for line in f:
            trace=json.loads(line)
            timers.append({k:trace[k] for k in ('map_id','method','seed','n_agents','condition')}|
                {f'mean_{field}':mean(t[field] for t in trace['timing_repeats']) for field in ('planning_seconds','decision_seconds','episode_seconds')})
    (output/'repeated_timing.json').write_text(json.dumps(timers,indent=2)+'\n')
    lines=['# Stratified transfer results','',
        'Generated from raw data. Pilot outputs validate software only. Failures remain in success denominators; path means use successes. Seed std describes model variation on shared maps, not map independence. Timing repetitions never increase episode counts. Endpoint arrangements are proxies; crossing does not guarantee congestion.','',
        '| Size | Density | Arrangement | Agents | Condition | Method | Successes / episodes | Successful makespan | Mean attempts |',
        '|---|---|---|---|---|---|---|---|---|']
    num=lambda x:'n/a' if x is None else f'{x:.3f}'
    for g in groups:
        lines.append(f"| {g['grid_size']} | {g['density']} | {g['arrangement']} | {g['n_agents']} | {g['condition']} | {g['method']} | {g['successes']}/{g['episodes']} | {num(g['successful_mean_makespan'])} | {num(g['mean_conflict_attempts'])} |")
    (output/'comparison.md').write_text('\n'.join(lines)+'\n')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('run',type=Path)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    print(summarize(args.run,args.output))


if __name__=='__main__': main()
