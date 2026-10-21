"""Check CP-08 closure and save a separate snapshot of newly added sources."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.final_protocol import check_freeze


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    check_freeze(json.loads((ROOT/'configs/final_experiment.json').read_text()),
                 ROOT/'results/validation/CP-07a-freeze')
    proof = json.loads((ROOT/'results/validation/CP-08-checks.json').read_text())
    provenance = json.loads((ROOT/'paper/manuscript_provenance.json').read_text())
    tests = json.loads((ROOT/'results/validation/CP-08-tests.json').read_text())
    assert proof['visual_review'].startswith('completed:')
    assert proof['page_count'] == 17 and proof['text_outside_page'] == 0
    assert proof['table_count'] == 9 and proof['figure_count'] == 7
    assert tests['tests_run'] == 139 and tests['exit_code'] == 0
    assert 'Ran 139 tests in 16.539s' in (ROOT/tests['log']).read_text(encoding='utf-16')
    qenn = ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx'
    assert sha(qenn) == '0eb7c34b6358da752b52c38fd9af9daead8469c2df2216df1c272f07c47392f8'
    for key, name in [('manuscript_sha256','paper.md'),('latex_sha256','paper.tex'),
                      ('claims_sha256','claims.json'),('pdf_sha256','paper.pdf')]:
        assert provenance[key] == sha(ROOT/'paper'/name)
    for name, value in provenance['input_sha256'].items():
        assert sha(ROOT/name) == value, name
    assert proof['pdf_sha256'] == provenance['pdf_sha256']
    docs = ['README.md','task.md','prd.md','tdd.md','implementationstrategy.md',
            'everythingtoknow.md','AGENTS.md']
    broken = []
    for name in docs+['paper/REPRODUCING.md','paper/paper.md']:
        path = ROOT/name
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if target.startswith(('https://','http://','#')):
                continue
            target = target.split('#',1)[0]
            if target and not (path.parent/target).exists():
                broken.append((name,target))
    assert not broken, broken
    source_names = docs+['requirements.txt','evaluation/research_analysis.py',
        'evaluation/check_research_outputs.py','test_research_analysis.py',
        'test_manuscript_tools.py','paper/build_manuscript.py',
        'paper/render_manuscript.py','paper/check_manuscript.py',
        'paper/methods_source.md','paper/references.json','paper/literature_review.md',
        'paper/author.json','paper/REPRODUCING.md','paper/SCIENTIFIC_REVIEW.md',
        'results/validation/archive_cp08.py']
    destination = ROOT/'results/validation/CP-07b-08-source'
    destination.mkdir(exist_ok=False)
    sources = {}
    for name in source_names:
        copied = destination/name
        copied.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,copied)
        sources[name] = sha(copied)
        assert sources[name] == sha(ROOT/name)
    artifacts = ['paper/paper.md','paper/paper.tex','paper/paper.pdf','paper/claims.json',
        'paper/manuscript_provenance.json','results/validation/CP-07b-audit.json',
        'results/validation/CP-07b-checks.json','results/validation/CP-07b-tests.json',
        'results/validation/CP-08-checks.json','results/validation/CP-08-tests.json',
        'results/validation/CP-08-tests.log','results/validation/CP-07b.md',
        'results/validation/CP-08.md','results/analysis/CP-07b/report.json',
        'results/analysis/CP-07b/provenance.json']
    result = dict(date='2026-10-07',checkpoint='CP-08 complete; CP-09 pending',
        source_files=sources,artifact_files={name:sha(ROOT/name) for name in artifacts},
        original_qenn_sha256=sha(qenn),final_seal_matches=True,
        document_links_checked=True,visual_review_complete=True,
        external_peer_review=False,word_format_deliverable_complete=False)
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(source_files=len(sources),bound_artifacts=len(artifacts),
        document_links_checked=True,final_seal_matches=True,qenn_unchanged=True,
        checkpoint='CP-08 complete; CP-09 pending'),indent=2))


if __name__ == '__main__':
    main()
