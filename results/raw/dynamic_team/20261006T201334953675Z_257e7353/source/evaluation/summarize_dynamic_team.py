"""Generate static/dynamic team tables and success figures from measured CSV."""
import argparse
import csv
import json
import os
from pathlib import Path
from statistics import mean
from evaluation.summarize_team import aggregate
from evaluation.team_protocol import ROOT


def summarize(run,output):
    run,output=Path(run),Path(output)
    with (run/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    groups=[]
    for condition in ('static','dynamic'):
        selected=[r for r in rows if r['condition']==condition]
        for group in aggregate(selected):
            cases=[r for r in selected if r['method']==group['method'] and int(r['n_agents'])==group['n_agents']]
            group.update(condition=condition,mean_plan_calls=mean(int(r['plan_calls']) for r in cases),
                         mean_plan_failures=mean(int(r['plan_failures']) for r in cases),
                         episodes_with_addition=sum(int(r['applied_events'])>0 for r in cases))
            groups.append(group)
    output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(groups,indent=2)+'\n')
    lines=['# Paired static/dynamic team transfer','','Generated from measured CSV. All failures/empty schedules are retained. Path/time means include successes only. Five model seeds reuse the same 20 geometries. Frozen controls retry independent original routes. Early completion stops later events. The static-trained policies receive no online updates.','',
        '| Method | Agents | Condition | Successes / episodes | Success | Successful makespan | Successful moves | Mean attempts | Mean plan calls | Mean plan failures | Episodes seeing addition |',
        '|---|---|---|---|---|---|---|---|---|---|---|']
    number=lambda v:'n/a' if v is None else f'{v:.3f}'
    for g in groups:
        lines.append(f"| {g['method']} | {g['n_agents']} | {g['condition']} | {g['successes']} / {g['episodes']} | {g['success_rate']:.1%} | {number(g['successful_mean_makespan'])} | {number(g['successful_mean_moves'])} | {number(g['mean_conflict_attempts'])} | {number(g['mean_plan_calls'])} | {number(g['mean_plan_failures'])} | {g['episodes_with_addition']} |")
    (output/'comparison.md').write_text('\n'.join(lines)+'\n')
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    methods=sorted({g['method'] for g in groups})
    fig,axes=plt.subplots(1,2,figsize=(16,5),layout='constrained')
    for ax,n in zip(axes,(2,4)):
        for offset,condition in ((-.18,'static'),(.18,'dynamic')):
            values=[next(g['success_rate'] for g in groups if g['method']==m and g['n_agents']==n and g['condition']==condition) for m in methods]
            ax.bar([i+offset for i in range(len(methods))],values,width=.34,label=condition)
        ax.set(xticks=range(len(methods)),xticklabels=methods,ylim=(0,1.05),ylabel='Team success rate',title=f'{n} agents; all held-out cases')
        ax.tick_params(axis='x',rotation=65); ax.legend(); ax.grid(axis='y',alpha=.2)
    for suffix in ('png','svg'): fig.savefig(output/f'success_comparison.{suffix}',dpi=160)
    plt.close(fig)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); print(f'Generated analysis: {summarize(args.run,args.output)}')


if __name__=='__main__': main()
