"""Verify saved CP-07a evidence, document links and source/QENN fingerprints."""
import ast
import csv
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from evaluation.final_protocol import check_freeze, digest


def main():
    config=json.loads((ROOT/'configs/final_experiment.json').read_text())
    sealed=ROOT/'results/validation/CP-07a-freeze'
    exclusions=check_freeze(config,sealed)
    manifest=json.loads((sealed/'manifest.json').read_text())
    assert not manifest['final_maps_generated']
    run=ROOT/'results/validation/protocol_pilot/20261006T210712802711Z_2c64fadb'
    with (run/'raw_results.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    report=json.loads((ROOT/'results/validation/CP-07a-audit.json').read_text())
    summary=json.loads((ROOT/'results/validation/CP-07a-analysis/summary.json').read_text())
    assert len(rows)==report['episodes']==1512 and report['steps_replayed']==63386
    assert report['all_decisions_replayed'] and report['active_event_prefixes_match']
    assert len(summary)==648
    for group in summary:
        cases=[r for r in rows if (int(r['grid_size']),float(r['density_requested']),r['arrangement'],int(r['n_agents']),r['condition'],r['method'])==
            (group['grid_size'],group['density'],group['arrangement'],group['n_agents'],group['condition'],group['method'])]
        good=[r for r in cases if r['success']=='1']
        assert group['episodes']==len(cases) and group['successes']==len(good)
        assert group['success_rate']==len(good)/len(cases)
        assert group['successful_mean_makespan']==(mean(float(r['makespan']) for r in good) if good else None)
    for row in rows:
        if row['success']=='0': assert row['makespan']==row['sum_arrival_times']==''
        if row['condition']=='dynamic' or row['n_agents']!='1': assert row['static_single_agent_gap']==''
        if row['static_single_agent_gap']=='': assert row['gap_undefined_reason']!=''
    timers=json.loads((ROOT/'results/validation/CP-07a-analysis/repeated_timing.json').read_text())
    assert len(timers)==1512
    contrasts=json.loads((ROOT/'results/validation/CP-07a-analysis/matched_cases.json').read_text())
    assert [g['pairs'] for g in contrasts]==[360,72,72,72]
    test_count=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_')
        for p in ROOT.glob('test_*.py') for n in ast.walk(ast.parse(p.read_text())))
    assert test_count==133
    links=0
    for name in ('task.md','prd.md','implementationstrategy.md','tdd.md','everythingtoknow.md','README.md'):
        for link in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'): continue
            path=link.split('#')[0].strip('<>')
            assert (ROOT/path).exists(),(name,path)
            links+=1
    qenn=ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx'
    assert digest(qenn)=='0eb7c34b6358da752b52c38fd9af9daeaD8469c2df2216df1c272f07c47392f8'.lower()
    archive=ROOT/'results/validation/CP-07a-source'
    archive.mkdir(exist_ok=True)
    hashes={}
    for relative,expected in manifest['source_sha256'].items():
        destination=archive/relative; destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists(): assert digest(destination)==expected
        else: shutil.copyfile(ROOT/relative,destination)
        assert digest(destination)==expected
        hashes[relative]=expected
    (archive/'manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
    proof=dict(test_methods=test_count,pilot_episodes=len(rows),pilot_steps=report['steps_replayed'],
        summary_groups=len(summary),matched_pair_counts=[g['pairs'] for g in contrasts],
        excluded_geometries=len(exclusions['excluded_ids']),source_files=len(hashes),local_links_checked=links,
        sealed_sources_match=True,final_maps_generated=False,qenn_unchanged=True,
        artifact_sha256={str(p.relative_to(ROOT)):digest(p) for p in (
            run/'raw_results.csv',run/'trajectories.jsonl',run/'config.json',run/'map_bank.json',
            ROOT/'results/validation/CP-07a-audit.json')})
    (ROOT/'results/validation/CP-07a-checks.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__=='__main__': main()
