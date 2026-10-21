"""Final scientific analysis: stratified denominators, paired cases and figures."""
import argparse
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean,stdev
from evaluation.team_protocol import ROOT
from evaluation.final_protocol import digest

MAIN=('bfs','dijkstra','astar','solo','shared')
METHODS=MAIN+('bfs_frozen','dijkstra_frozen','astar_frozen','untrained')


def average(values):
    values=list(values)
    return mean(values) if values else None


def summarize(cases):
    good=[r for r in cases if r['success']=='1']; seeds=defaultdict(list)
    for r in cases: seeds[r['seed']].append(r)
    rates={s:mean(int(r['success']) for r in group) for s,group in seeds.items()}
    def metric(field,selected=good): return average(float(r[field]) for r in selected if r[field]!='')
    exposed=[r for r in cases if r['addition_exposed']=='1']
    return dict(episodes=len(cases),successes=len(good),success_rate=len(good)/len(cases),
        seed_rates=rates,seed_std=stdev(rates.values()) if len(rates)>1 else None,
        mean_successful_moves=metric('total_moves'),mean_successful_makespan=metric('makespan'),
        mean_successful_arrival_sum=metric('sum_arrival_times'),mean_static_single_gap=metric('static_single_agent_gap'),
        mean_attempts=metric('conflict_attempts',cases),actual_collisions=sum(int(r['actual_collisions']) for r in cases),
        mean_expanded_nodes=metric('expanded_nodes',cases),
        exposed_episodes=len(exposed),exposed_successes=sum(r['success']=='1' for r in exposed),
        exposed_successful_completion_steps=metric('steps_after_addition',exposed),
        initial_unreachable_episodes=sum(int(r['initially_unreachable_agents'])>0 for r in cases))


def grouped(rows,fields):
    groups=defaultdict(list)
    for row in rows: groups[tuple(row[f] for f in fields)].append(row)
    return [dict(zip(fields,key))|summarize(cases) for key,cases in sorted(groups.items())]


def pair(rows,left,right,*,classical_reference=False,conditions=None,agent_counts=None,exposed=False):
    selected=[r for r in rows if (conditions is None or r['condition'] in conditions) and
        (agent_counts is None or int(r['n_agents']) in agent_counts)]
    a=[r for r in selected if r['method']==left]
    def key(r): return (r['map_id'],r['n_agents'],r['condition'])+(() if classical_reference else (r['seed'],))
    b={key(r):r for r in selected if r['method']==right}
    if not a or any(key(r) not in b for r in a): raise ValueError('Missing paired cases')
    matched=[(r,b[key(r)]) for r in a]
    if exposed: matched=[(x,y) for x,y in matched if x['addition_exposed']==y['addition_exposed']=='1']
    successful=[(x,y) for x,y in matched if x['success']==y['success']=='1']
    def difference(field, pairs): return average(float(x[field])-float(y[field]) for x,y in pairs if x[field]!='' and y[field]!='')
    seed_differences=defaultdict(list)
    for x,y in matched: seed_differences[x['seed']].append(int(x['success'])-int(y['success']))
    seed_rates={s:mean(v) for s,v in seed_differences.items()}
    return dict(left=left,right=right,pairs=len(matched),jointly_successful=len(successful),
        success_difference=average(int(x['success'])-int(y['success']) for x,y in matched),
        seed_success_differences=seed_rates,seed_difference_std=stdev(seed_rates.values()) if len(seed_rates)>1 else None,
        moves_difference= difference('total_moves',successful),makespan_difference=difference('makespan',successful),
        attempts_difference=difference('conflict_attempts',matched),
        post_addition_steps_difference=difference('steps_after_addition',successful) if exposed else None,
        left_shorter=sum(float(x['total_moves'])<float(y['total_moves']) for x,y in successful),
        ties=sum(float(x['total_moves'])==float(y['total_moves']) for x,y in successful),
        right_shorter=sum(float(x['total_moves'])>float(y['total_moves']) for x,y in successful))


def scaling(rows,method,a,b,condition):
    def key(r): return (r['map_id'],r['seed'])
    first={key(r):r for r in rows if r['method']==method and int(r['n_agents'])==a and r['condition']==condition}
    last={key(r):r for r in rows if r['method']==method and int(r['n_agents'])==b and r['condition']==condition}
    if set(first)!=set(last) or not first: raise ValueError('Scaling sets differ')
    return dict(method=method,condition=condition,from_agents=a,to_agents=b,pairs=len(first),
        success_difference=mean(int(last[k]['success'])-int(first[k]['success']) for k in first),
        attempts_difference=mean(int(last[k]['conflict_attempts'])-int(first[k]['conflict_attempts']) for k in first))


def save_table(path,headings,records):
    lines=['| '+' | '.join(headings)+' |','|'+'|'.join('---' for _ in headings)+'|']
    lines += ['| '+' | '.join(str(x) for x in r)+' |' for r in records]
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def analyze(run,audit_path,output):
    run,audit_path,output=Path(run).resolve(),Path(audit_path).resolve(),Path(output).resolve()
    complete=json.loads((run/'COMPLETE.json').read_text()); audit=json.loads(audit_path.read_text())
    if complete['phase']!='final' or audit['phase']!='final' or audit['episodes']!=complete['episodes'] or not audit['all_decisions_replayed']:
        raise ValueError('Completed audited final run required')
    with (run/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    if len(rows)!=complete['episodes']: raise ValueError('Episode count mismatch')
    output.mkdir(parents=True,exist_ok=False); figures=output/'figures'; figures.mkdir()
    tables=output/'tables'; tables.mkdir()
    groups={name:grouped(rows,fields) for name,fields in {
        'overall':('method',),'condition_agents':('method','condition','n_agents'),
        'size_condition':('method','condition','grid_size'),
        'density_condition':('method','condition','density_requested'),
        'arrangement_condition':('method','condition','arrangement'),
        'full_strata':('method','grid_size','density_requested','arrangement','n_agents','condition')}.items()}
    contrasts=dict(
        h1=[pair(rows,m,'astar',classical_reference=True,conditions=['static'],agent_counts=[n]) for m in ('solo','shared') for n in (1,2,4)],
        h2=[pair(rows,m,'astar_frozen',classical_reference=True,conditions=['dynamic'],agent_counts=[n],exposed=True) for m in ('solo','shared') for n in (1,2,4)],
        replanning=[pair(rows,m,m+'_frozen',conditions=['dynamic'],agent_counts=[n]) for m in ('bfs','dijkstra','astar') for n in (1,2,4)],
        h3=[scaling(rows,m,a,b,c) for m in MAIN for c in ('static','dynamic') for a,b in ((1,2),(2,4))],
        h4=[pair(rows,'shared','solo',conditions=[c],agent_counts=[n]) for c in ('static','dynamic') for n in (1,2,4)])
    # Detailed paired effects retain each grid/density/arrangement stratum.
    contrasts['h4_strata']=[dict(grid_size=size,density_requested=density,arrangement=arrangement,
        condition=condition,n_agents=n)|pair([r for r in rows if r['grid_size']==size and r['density_requested']==density and r['arrangement']==arrangement],
            'shared','solo',conditions=[condition],agent_counts=[n])
        for size in ('5','10','15') for density in ('0.1','0.2') for arrangement in ('uniform','crossing')
        for condition in ('static','dynamic') for n in (1,2,4)]
    bank=json.loads((run/'map_bank.json').read_text())
    scenario_summary=dict(geometries=len(bank['scenarios']),rejected_candidates=len(bank['rejected_candidates']),
        initially_unreachable_by_agents={str(n):sum(any(x is None for x in s['individual_optimal_moves'][:n]) for s in bank['scenarios']) for n in (1,2,4)},
        mean_realized_density_by_requested={str(d):mean(s['density_realized'] for s in bank['scenarios'] if s['density_requested']==d) for d in (.1,.2)},
        mean_overlap_by_arrangement={arr:mean(s['route_overlap_pairs']['4'] for s in bank['scenarios'] if s['arrangement']==arr) for arr in ('uniform','crossing')})
    timers=defaultdict(list)
    with (run/'trajectories.jsonl').open() as f:
        for line in f:
            record=json.loads(line); saved=record['rollout']; repetitions=record['timing_repeats']
            if len(repetitions)!=3: raise ValueError('Final timing repetitions missing')
            timings={field:mean(t[field] for t in repetitions) for field in ('decision_seconds','planning_seconds','episode_seconds')}
            arrivals=saved['final_info']['arrival_steps']; ticks=saved['final_info']['elapsed_steps']
            # Every arrived policy is forced WAIT; sum first-arrival ticks or full timeout for active selections.
            decisions=sum(ticks if a is None else a for a in arrivals)
            timers[(record['method'],record['n_agents'])].append(timings|dict(decisions=decisions,ticks=ticks,plan_calls=len(saved['planning_calls'])))
    timing_summary=[dict(method=m,n_agents=n,episodes=len(values),
        mean_planning_ms=1000*mean(v['planning_seconds'] for v in values),
        mean_selection_ms=1000*mean(v['decision_seconds'] for v in values),
        mean_episode_ms=1000*mean(v['episode_seconds'] for v in values),
        total_decisions=sum(v['decisions'] for v in values),
        pooled_selection_ms_per_policy_action=1000*sum(v['decision_seconds'] for v in values)/sum(v['decisions'] for v in values) if m in ('solo','shared','untrained') else None)
        for (m,n),values in sorted(timers.items())]
    training_run=ROOT/json.loads((run/'config.json').read_text())['training_run']
    training=json.loads((training_run/'summary.json').read_text())
    training_summary=[dict(mode=m,models=5,assigned_tasks=sum(r['agent_tasks'] for r in training if r['mode']==m),
        episodes=sum(r['episodes'] for r in training if r['mode']==m),
        transitions=sum(r['transitions'] for r in training if r['mode']==m),
        updates=sum(r['updates'] for r in training if r['mode']==m),
        recorded_training_seconds=sum(r['training_seconds'] for r in training if r['mode']==m)) for m in ('solo','shared')]
    report=dict(groups=groups,contrasts=contrasts,scenarios=scenario_summary,timing=timing_summary,training=training_summary,
        run=str(run.resolve()),audit=audit,unique_episodes=len(rows),fresh_timing_rollouts=len(rows)*3)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    fmt=lambda x:'n/a' if x is None else f'{x:.3f}'
    save_table(tables/'overall.md',['Method','Successes / episodes','Success (%)','Seed SD (pp)','Successful moves','Successful makespan','Mean attempts'],
        [[g['method'],f"{g['successes']}/{g['episodes']}",f"{100*g['success_rate']:.2f}",fmt(None if g['seed_std'] is None else 100*g['seed_std']),fmt(g['mean_successful_moves']),fmt(g['mean_successful_makespan']),fmt(g['mean_attempts'])] for g in groups['overall']])
    save_table(tables/'condition_agents.md',['Method','Condition','Agents','Successes / episodes','Success (%)','Successful makespan','Mean attempts'],
        [[g['method'],g['condition'],g['n_agents'],f"{g['successes']}/{g['episodes']}",f"{100*g['success_rate']:.2f}",fmt(g['mean_successful_makespan']),fmt(g['mean_attempts'])] for g in groups['condition_agents']])
    save_table(tables/'size_condition.md',['Method','Condition','Grid side','Successes / episodes','Success (%)','Seed SD (pp)'],
        [[g['method'],g['condition'],g['grid_size'],f"{g['successes']}/{g['episodes']}",f"{100*g['success_rate']:.2f}",fmt(None if g['seed_std'] is None else 100*g['seed_std'])] for g in groups['size_condition'] if g['method'] in MAIN])
    save_table(tables/'training.md',['Mode','Tasks','Episodes','Transitions','Updates','Recorded seconds'],
        [[g['mode'],g['assigned_tasks'],g['episodes'],g['transitions'],g['updates'],fmt(g['recorded_training_seconds'])] for g in training_summary])
    save_table(tables/'h1_paired.md',['Policy minus A*','Agents','Pairs','Joint success','Move difference','Policy shorter / ties / A* shorter'],
        [[g['left'],n,g['pairs'],g['jointly_successful'],fmt(g['moves_difference']),f"{g['left_shorter']} / {g['ties']} / {g['right_shorter']}"] for g,n in zip(contrasts['h1'],[1,2,4]*2)])
    save_table(tables/'static_single_gap.md',['Method','Successes / episodes','Mean exact movement gap'],
        [[g['method'],f"{g['successes']}/{g['episodes']}",fmt(g['mean_static_single_gap'])]
         for g in groups['condition_agents'] if g['condition']=='static' and g['n_agents']=='1'])
    save_table(tables/'h2_exposed.md',['Policy minus frozen A*','Agents','Both exposed pairs','Joint success','Success difference (pp)','Post-addition step difference'],
        [[g['left'],n,g['pairs'],g['jointly_successful'],fmt(None if g['success_difference'] is None else 100*g['success_difference']),fmt(g['post_addition_steps_difference'])] for g,n in zip(contrasts['h2'],[1,2,4]*2)])
    save_table(tables/'h4_paired.md',['Condition','Agents','Pairs','Joint success','Shared minus solo success (pp)','Paired seed SD (pp)','Move difference'],
        [[c,n,g['pairs'],g['jointly_successful'],fmt(100*g['success_difference']),fmt(100*g['seed_difference_std']),fmt(g['moves_difference'])] for g,(c,n) in zip(contrasts['h4'],[(c,n) for c in ('static','dynamic') for n in (1,2,4)])])
    save_table(tables/'runtime.md',['Method','Agents','Cases','Planning ms','Selection ms','Total ms','Expanded states'],
        [[g['method'],g['n_agents'],g['episodes'],fmt(g['mean_planning_ms']),fmt(g['mean_selection_ms']),fmt(g['mean_episode_ms']),
          fmt(average(float(r['expanded_nodes']) for r in rows if r['method']==g['method'] and int(r['n_agents'])==g['n_agents'] and r['expanded_nodes']!=''))] for g in timing_summary])
    plot(rows,groups,timing_summary,training_run,figures)
    provenance=dict(inputs={str(p.relative_to(ROOT)):digest(p) for p in (
        run/'raw_results.csv',run/'trajectories.jsonl',run/'map_bank.json',run/'config.json',
        audit_path,training_run/'summary.json',training_run/'training_episodes.csv')},
        generator_sha256=digest(Path(__file__)),outputs={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()})
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(f'Generated scientific analysis: {output}',flush=True)
    return output


def plot(rows,groups,timers,training_run,output):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    colors=dict(zip(MAIN,('#254b87','#3c906c','#bd6b29','#9370a7','#bc3f55')))
    def save(fig,name):
        for suffix in ('png','svg','pdf'): fig.savefig(output/f'{name}.{suffix}',dpi=180,bbox_inches='tight')
        plt.close(fig)
    from matplotlib.patches import FancyBboxPatch
    fig,ax=plt.subplots(figsize=(9,3.4)); ax.set(xlim=(0,9),ylim=(0,3.4)); ax.axis('off')
    boxes=[(.15,2,'Current graph\nand positions'),(3.15,2,'Local observations\n(17 features / agent)'),(6.15,2,'Frozen shared DQN\n(17–128–128–5)'),
        (6.15,.35,'Joint proposed\nactions'),(3.15,.35,'Movement referee\n(conflict rejection)'),(.15,.35,'Rewards and\nnext observation')]
    for x,y,label in boxes:
        ax.add_patch(FancyBboxPatch((x,y),2.55,1,boxstyle='round,pad=.06',facecolor='#e8edf3',edgecolor='#254b87'))
        ax.text(x+1.275,y+.5,label,ha='center',va='center',fontsize=10)
    for a,b in [((2.75,2.5),(3.05,2.5)),((5.75,2.5),(6.05,2.5)),((7.425,1.9),(7.425,1.45)),
        ((6.05,.85),(5.75,.85)),((3.05,.85),(2.75,.85)),((1.425,1.45),(1.425,1.9))]:
        ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':'#254b87','lw':1.5})
    save(fig,'workflow')
    for metric,name,label in [('success_rate','success_by_agents','Team success rate'),
        ('mean_successful_makespan','makespan_by_agents','Makespan (successful episodes only)')]:
        fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
        for ax,condition in zip(axes,('static','dynamic')):
            for method in MAIN:
                subset=sorted([g for g in groups['condition_agents'] if g['method']==method and g['condition']==condition],key=lambda g:int(g['n_agents']))
                y=[float('nan') if g[metric] is None else g[metric] for g in subset]
                ax.plot([1,2,4],y,'o-',color=colors[method],label=method)
                if metric=='success_rate' and method in ('solo','shared'):
                    ax.errorbar([1,2,4],y,yerr=[g['seed_std'] for g in subset],fmt='none',color=colors[method],capsize=3)
            ax.set(title=condition,xlabel='Agents',ylabel=label,xticks=[1,2,4]); ax.grid(alpha=.2)
            if metric=='success_rate': ax.set_ylim(-.02,1.02)
        axes[1].legend(fontsize=8); save(fig,name)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,condition in zip(axes,('static','dynamic')):
        for method in MAIN:
            selected=[r for r in rows if r['method']==method and r['condition']==condition]
            ax.plot([5,10,15],[summarize([r for r in selected if int(r['grid_size'])==s])['mean_successful_moves'] or float('nan') for s in (5,10,15)],'o-',color=colors[method],label=method)
        ax.set(title=condition,xlabel='Grid side length',ylabel='Executed moves (successes only)',xticks=[5,10,15]); ax.grid(alpha=.2)
    axes[1].legend(fontsize=8); save(fig,'moves_by_size')
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,condition in zip(axes,('static','dynamic')):
        for method in MAIN:
            subset=sorted([g for g in groups['density_condition'] if g['method']==method and g['condition']==condition],key=lambda g:float(g['density_requested']))
            ax.plot([.1,.2],[g['mean_attempts'] for g in subset],'o-',color=colors[method],label=method)
        ax.set(title=condition,xlabel='Requested wall probability',ylabel='Rejected-agent attempts / episode',xticks=[.1,.2]); ax.grid(alpha=.2)
    axes[1].legend(fontsize=8); save(fig,'attempts_by_density')
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for method in MAIN:
        subset=sorted([g for g in timers if g['method']==method],key=lambda g:g['n_agents'])
        ax.plot([1,2,4],[g['mean_planning_ms']+g['mean_selection_ms'] for g in subset],'o-',color=colors[method],label=method)
    ax.set(yscale='log',xlabel='Agents',ylabel='Planning + selection ms / episode',xticks=[1,2,4],title='Three fresh timing rollouts per case; static and dynamic pooled')
    ax.legend(fontsize=8); ax.grid(alpha=.2); save(fig,'runtime_by_agents')
    with (training_run/'training_episodes.csv').open(newline='') as f: training=list(csv.DictReader(f))
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,mode in zip(axes,('solo','shared')):
        for seed in range(5):
            by_cycle=defaultdict(list)
            for r in training:
                if r['mode']==mode and int(r['seed'])==seed: by_cycle[int(r['cycle'])].append(r)
            cycles=sorted(by_cycle)
            returns=[sum(float(r['episode_reward']) for r in by_cycle[c])/sum(int(r['agent_tasks']) for r in by_cycle[c]) for c in cycles]
            ax.plot(cycles,[mean(returns[max(0,i-99):i+1]) for i in range(len(returns))],label=f'Seed {seed}',lw=1)
        ax.set(title=mode,xlabel='Training cycle',ylabel='Return per assigned task (100-cycle mean)'); ax.grid(alpha=.2)
    axes[1].legend(fontsize=8); save(fig,'training_returns')


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('run',type=Path)
    parser.add_argument('--audit',type=Path,required=True); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); analyze(args.run,args.audit,args.output)


if __name__=='__main__': main()
