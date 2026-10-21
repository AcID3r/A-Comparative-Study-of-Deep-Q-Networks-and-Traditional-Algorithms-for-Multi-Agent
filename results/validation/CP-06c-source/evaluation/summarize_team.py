"""Generate static team result tables and figures from measured CSV only."""
import argparse
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean,stdev
from evaluation.team_protocol import ROOT


def aggregate(rows):
    groups = []
    for method in sorted({r['method'] for r in rows}):
        for n in sorted({int(r['n_agents']) for r in rows}):
            selected = [r for r in rows if r['method']==method and int(r['n_agents'])==n]
            if not selected: continue
            by_seed = defaultdict(list)
            for row in selected: by_seed[row['seed']].append(row)
            rates = [mean(int(r['success']) for r in group) for group in by_seed.values()]
            successes = [r for r in selected if r['success']=='1']
            groups.append({'method':method,'n_agents':n,'episodes':len(selected),'successes':len(successes),
                'success_rate':len(successes)/len(selected),'seed_success_std':stdev(rates) if len(rates)>1 else None,
                'successful_mean_makespan':mean(float(r['makespan']) for r in successes) if successes else None,
                'successful_mean_moves':mean(float(r['total_moves']) for r in successes) if successes else None,
                'mean_conflict_attempts':mean(float(r['conflict_attempts']) for r in selected),
                'planning_failures':sum(r['failure_reason']=='planning_failure' for r in selected),
                'actual_collisions':sum(int(r['actual_collisions']) for r in selected)})
    return groups


def summarize(run,output,training_run=None):
    run,output = Path(run),Path(output)
    with (run/'raw_results.csv').open(newline='') as f: rows = list(csv.DictReader(f))
    groups = aggregate(rows)
    output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(groups,indent=2)+'\n')
    lines = ['# Static held-out team comparison','','Generated from raw CSV. All maps and planning/time-limit failures are included in success denominators. Makespan/moves means include successes only. Seed std describes variation across five models, not independent map uncertainty. Attempts are rejected agents per tick; actual collisions are checked separately.','',
        '| Method | Agents | Successes / episodes | Success rate | Seed std | Successful makespan | Successful moves | Mean attempts | Planning failures | Actual collisions |',
        '|---|---|---|---|---|---|---|---|---|---|']
    value = lambda v: 'n/a' if v is None else f'{v:.3f}'
    for g in groups:
        lines.append(f"| {g['method']} | {g['n_agents']} | {g['successes']} / {g['episodes']} | {g['success_rate']:.1%} | {value(g['seed_success_std'])} | {value(g['successful_mean_makespan'])} | {value(g['successful_mean_moves'])} | {value(g['mean_conflict_attempts'])} | {g['planning_failures']} | {g['actual_collisions']} |")
    (output/'comparison.md').write_text('\n'.join(lines)+'\n')
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    methods = sorted({g['method'] for g in groups})
    fig,ax = plt.subplots(figsize=(10,5),layout='constrained')
    for offset,n in ((-.18,2),(.18,4)):
        values = [next(g['success_rate'] for g in groups if g['method']==m and g['n_agents']==n) for m in methods]
        ax.bar([i+offset for i in range(len(methods))],values,width=.34,label=f'{n} agents')
    ax.set(xticks=range(len(methods)),xticklabels=methods,ylim=(0,1.05),ylabel='Team success rate',title='Held-out static 5x5 team scenarios')
    ax.legend(); ax.grid(axis='y',alpha=.2)
    for suffix in ('png','svg'): fig.savefig(output/f'success_comparison.{suffix}',dpi=160)
    plt.close(fig)
    if training_run:
        with (Path(training_run)/'training_episodes.csv').open(newline='') as f: training = list(csv.DictReader(f))
        fig,axes = plt.subplots(1,2,figsize=(12,4),layout='constrained')
        for ax,mode in zip(axes,('solo','shared')):
            for seed in sorted({r['seed'] for r in training},key=int):
                by_cycle = defaultdict(list)
                for row in training:
                    if row['mode']==mode and row['seed']==seed: by_cycle[int(row['cycle'])].append(row)
                cycles = sorted(by_cycle)
                returns = [sum(float(r['episode_reward']) for r in by_cycle[c])/sum(int(r['agent_tasks']) for r in by_cycle[c]) for c in cycles]
                ax.plot(cycles,[mean(returns[max(0,i-99):i+1]) for i in range(len(returns))],label=f'Seed {seed}')
            ax.set(title=f'{mode}: exploratory training',xlabel='Training cycle',ylabel='Return per assigned task; trailing 100 cycles')
            ax.legend(); ax.grid(alpha=.2)
        for suffix in ('png','svg'): fig.savefig(output/f'training_returns.{suffix}',dpi=160)
        plt.close(fig)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path); parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--training-run',type=Path)
    args = parser.parse_args()
    print(f'Generated analysis: {summarize(args.run,args.output,args.training_run)}')


if __name__ == '__main__': main()
