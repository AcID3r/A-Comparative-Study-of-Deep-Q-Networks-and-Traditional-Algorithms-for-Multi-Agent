"""Independent final table/sample/reference checks and immutable artifact fingerprints."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from evaluation.team_protocol import ROOT
from evaluation.final_protocol import check_freeze,digest


def check(run,analysis,output):
    run,analysis,output=Path(run),Path(analysis),Path(output)
    config=json.loads((run/'config.json').read_text())
    exclusions=check_freeze(config,ROOT/'results/validation/CP-07a-freeze')
    bank=json.loads((run/'map_bank.json').read_text()); report=json.loads((analysis/'report.json').read_text())
    with (run/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==15120 and len(bank['scenarios'])==120
    ids={s['map_id'] for s in bank['scenarios']}
    assert len(ids)==120 and not ids & set(exclusions['excluded_ids'])
    assert Counter(s['stratum'] for s in bank['scenarios'])=={n:10 for n in range(12)}
    expected_methods={'bfs','dijkstra','astar','bfs_frozen','dijkstra_frozen','astar_frozen','solo','shared','untrained'}
    assert set(r['method'] for r in rows)==expected_methods
    assert Counter(r['method'] for r in rows)=={m:3600 if m in ('solo','shared','untrained') else 720 for m in expected_methods}
    seen=set()
    for r in rows:
        key=(r['map_id'],r['n_agents'],r['condition'],r['method'],r['seed'])
        assert key not in seen; seen.add(key)
        assert int(r['actual_collisions'])==0
        if int(r['initially_unreachable_agents'])>0: assert r['success']=='0'
        if r['success']=='0': assert r['makespan']==r['sum_arrival_times']==''
        if r['static_single_agent_gap']!='':
            assert r['condition']=='static' and r['n_agents']=='1' and r['success']=='1'
            bound=float(r['initial_independent_lower_bound'])
            assert float(r['static_single_agent_gap'])==(float(r['total_moves'])-bound)/bound
            if r['method'] in ('astar','bfs','dijkstra'): assert float(r['static_single_agent_gap'])==0
        else: assert r['gap_undefined_reason']!=''
    fields={'overall':('method',),'condition_agents':('method','condition','n_agents'),
        'size_condition':('method','condition','grid_size'),'density_condition':('method','condition','density_requested'),
        'arrangement_condition':('method','condition','arrangement'),
        'full_strata':('method','grid_size','density_requested','arrangement','n_agents','condition')}
    group_count=0
    for name,groups in report['groups'].items():
        assert sum(g['episodes'] for g in groups)==15120
        for g in groups:
            subset=[r for r in rows if all(r[k]==g[k] for k in fields[name])]
            good=[r for r in subset if r['success']=='1']
            assert len(subset)==g['episodes'] and len(good)==g['successes']
            assert g['success_rate']==len(good)/len(subset)
            assert g['mean_successful_makespan']==(mean(float(r['makespan']) for r in good) if good else None)
            assert g['mean_attempts']==mean(float(r['conflict_attempts']) for r in subset)
            group_count+=1
    for g in report['contrasts']['h4']:
        assert g['pairs']==600
        assert sum(g['seed_success_differences'].values())/5==g['success_difference'] or abs(sum(g['seed_success_differences'].values())/5-g['success_difference'])<1e-14
    provenance=json.loads((analysis/'provenance.json').read_text())
    for path,value in provenance['inputs'].items(): assert digest(ROOT/path)==value
    for path,value in provenance['outputs'].items(): assert digest(analysis/path)==value
    assert all((analysis/'figures'/f'{name}.{suffix}').exists() for name in
        ('workflow','success_by_agents','makespan_by_agents','moves_by_size','attempts_by_density','runtime_by_agents','training_returns') for suffix in ('png','svg','pdf'))
    assert digest(ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx')=='0eb7c34b6358da752b52c38fd9af9daead8469c2df2216df1c272f07c47392f8'
    proof=dict(episodes=len(rows),unique_geometries=120,groups_independently_checked=group_count,
        final_seal_matches=True,geometry_exclusions_match=True,all_failures_retained=True,
        exact_single_agent_gaps_checked=True,source_input_output_hashes_match=True,actual_collisions=0,
        qenn_unchanged=True,raw_csv_sha256=digest(run/'raw_results.csv'),
        raw_trace_sha256=digest(run/'trajectories.jsonl'),report_sha256=digest(analysis/'report.json'))
    with output.open('x') as f: json.dump(proof,f,indent=2); f.write('\n')
    print(json.dumps(proof,indent=2))
    return proof


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path); parser.add_argument('analysis',type=Path); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); check(args.run,args.analysis,args.output)


if __name__=='__main__': main()
