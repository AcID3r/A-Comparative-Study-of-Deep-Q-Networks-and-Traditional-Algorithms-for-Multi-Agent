"""Replot audited values at readable single-column publication dimensions."""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean
from evaluation.team_protocol import ROOT


def generate(analysis, output):
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch
    report = json.loads((analysis/'report.json').read_text())
    output.mkdir(parents=True, exist_ok=True)
    methods = ('bfs', 'dijkstra', 'astar', 'solo', 'shared')
    colors = dict(zip(methods, ('#254b87','#3c906c','#bd6b29','#9370a7','#bc3f55')))
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':8,
                         'axes.spines.top':False,'axes.spines.right':False})
    def save(fig, name):
        for extension in ('png','pdf','svg'):
            fig.savefig(output/f'{name}.{extension}', dpi=300, bbox_inches='tight')
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(3.3,4.7))
    ax.set(xlim=(0,3.3),ylim=(0,6)); ax.axis('off')
    labels = ['Current graph and positions','Local observations: 17 features/agent',
              'Frozen shared DQN: 17–128–128–5','Joint proposed actions',
              'Movement referee: conflict rejection','Rewards and next observation']
    for i, label in enumerate(labels):
        y = 5.2-i
        ax.add_patch(FancyBboxPatch((.1,y),3.1,.65,boxstyle='round,pad=.025',
                     facecolor='#e8edf3',edgecolor='#254b87'))
        ax.text(1.65,y+.325,label,ha='center',va='center',fontsize=8)
        if i<5:
            ax.annotate('',xy=(1.65,y-.28),xytext=(1.65,y-.03),
                        arrowprops={'arrowstyle':'->','color':'#254b87'})
    save(fig,'workflow')
    settings = [('condition_agents','n_agents','success_rate','success_by_agents','Team success rate',[1,2,4]),
        ('condition_agents','n_agents','mean_successful_makespan','makespan_by_agents','Makespan (successes)',[1,2,4]),
        ('size_condition','grid_size','mean_successful_moves','moves_by_size','Moves (successes)',[5,10,15]),
        ('density_condition','density_requested','mean_attempts','attempts_by_density','Rejected attempts / episode',[.1,.2])]
    for group, field, metric, name, ylabel, ticks in settings:
        fig, axes = plt.subplots(2,1,figsize=(3.3,5.2),layout='constrained')
        for ax, condition in zip(axes, ('static','dynamic')):
            for method in methods:
                selected = sorted([g for g in report['groups'][group]
                    if g['method']==method and g['condition']==condition],key=lambda g:float(g[field]))
                y = [float('nan') if g[metric] is None else g[metric] for g in selected]
                ax.plot(ticks,y,'o-',markersize=3,linewidth=1,color=colors[method],label=method)
                if metric=='success_rate' and method in ('solo','shared'):
                    ax.errorbar(ticks,y,yerr=[g['seed_std'] for g in selected],
                        fmt='none',color=colors[method],capsize=2)
            ax.set(title=condition,ylabel=ylabel,xticks=ticks)
            ax.grid(alpha=.2)
            if metric=='success_rate': ax.set_ylim(-.02,1.02)
        axes[1].set_xlabel({'n_agents':'Agents','grid_size':'Grid side length',
                           'density_requested':'Requested wall probability'}[field])
        axes[0].legend(fontsize=6,ncol=3,loc='best')
        save(fig,name)
    fig, ax = plt.subplots(figsize=(3.3,2.8),layout='constrained')
    for method in methods:
        values = sorted([g for g in report['timing'] if g['method']==method],key=lambda g:g['n_agents'])
        ax.plot([1,2,4],[g['mean_planning_ms']+g['mean_selection_ms'] for g in values],
                'o-',markersize=3,linewidth=1,label=method,color=colors[method])
    ax.set(yscale='log',xlabel='Agents',ylabel='Planning + selection\nms / episode',xticks=[1,2,4])
    ax.legend(fontsize=6,ncol=2); ax.grid(alpha=.2); save(fig,'runtime_by_agents')
    config = json.loads((Path(report['run'])/'config.json').read_text())
    with (ROOT/config['training_run']/'training_episodes.csv').open(newline='') as handle:
        training = list(csv.DictReader(handle))
    fig, axes = plt.subplots(2,1,figsize=(3.3,5.2),layout='constrained')
    for ax, mode in zip(axes, ('solo','shared')):
        for seed in range(5):
            cycles = defaultdict(list)
            for row in training:
                if row['mode']==mode and int(row['seed'])==seed: cycles[int(row['cycle'])].append(row)
            ordered = sorted(cycles)
            returns = [sum(float(r['episode_reward']) for r in cycles[c])/
                       sum(int(r['agent_tasks']) for r in cycles[c]) for c in ordered]
            ax.plot(ordered,[mean(returns[max(0,i-99):i+1]) for i in range(len(returns))],
                    linewidth=.8,label=f'Seed {seed}')
        ax.set(title=mode,ylabel='Return / assigned task\n(100-cycle mean)'); ax.grid(alpha=.2)
    axes[0].legend(fontsize=6,ncol=3); axes[1].set_xlabel('Training cycle')
    save(fig,'training_returns')
