"""Verify delivered CP-09 artifacts and snapshot sources without claiming closure."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from evaluation.final_protocol import check_freeze,digest


def main():
    check_freeze(json.loads((ROOT/'configs/final_experiment.json').read_text()),
                 ROOT/'results/validation/CP-07a-freeze')
    proof=json.loads((ROOT/'results/validation/CP-09-checks.json').read_text())
    provenance=json.loads((ROOT/'paper/word_provenance.json').read_text(encoding='utf-8'))
    assert proof['docx_sha256']==provenance['docx_sha256']==digest(ROOT/'paper/Graph_Search_Research_Paper.docx')
    assert proof['all_measured_cells_match'] and proof['figure_hashes_checked']==7
    assert not proof['native_render']['native_render_complete']
    preview=json.loads((ROOT/'results/validation/CP-09-preview-pages.json').read_text())
    assert preview['visual_review'].startswith('completed for independent preview')
    assert preview['page_count']==12 and preview['images_outside_page']==0
    assert preview['docx_sha256']==proof['docx_sha256']
    assert preview['pdf_sha256']==digest(ROOT/'paper/Graph_Search_Research_Paper_preview.pdf')
    tests=json.loads((ROOT/'results/validation/CP-09-tests.json').read_text())
    for name,count,seconds in [('CP-09-tests-final.log',142,20.457),('CP-09-focused-tests.log',3,3.609)]:
        log=(ROOT/'results/validation'/name).read_text(encoding='utf-16')
        assert f'Ran {count} tests in {seconds:.3f}s' in log and '\nOK\n' in log
    raw=json.loads((ROOT/'results/validation/CP-07b-checks.json').read_text())
    assert digest(ROOT/'results/raw/final_transfer/20261006T212837810546Z_40b3d4c4/raw_results.csv')==raw['raw_csv_sha256']
    assert digest(ROOT/'results/analysis/CP-07b/report.json')==raw['report_sha256']
    qenn=ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx'
    assert digest(qenn)=='0eb7c34b6358da752b52c38fd9af9daead8469c2df2216df1c272f07c47392f8'
    docs=['README.md','task.md','prd.md','tdd.md','implementationstrategy.md','everythingtoknow.md','AGENTS.md']
    for name in docs+['paper/WORD_REVIEW.md']:
        path=ROOT/name
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if target.startswith(('https://','http://','#')): continue
            assert (path.parent/target.split('#')[0]).exists(),(name,target)
    sources=docs+['requirements.txt','paper/build_word.py','paper/word_figures.py',
        'paper/check_word.py','paper/render_word.py','paper/preview_word.py','paper/review_word.py',
        'paper/WORD_REVIEW.md','test_word_manuscript.py','results/validation/archive_cp09.py',
        'results/validation/CP-09.md']
    destination=ROOT/'results/validation/CP-09-source'; destination.mkdir(exist_ok=False)
    hashes={}
    for name in sources:
        output=destination/name; output.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/name,output); hashes[name]=digest(output)
        assert hashes[name]==digest(ROOT/name)
    artifacts=['paper/Graph_Search_Research_Paper.docx','paper/Graph_Search_Research_Paper_preview.pdf',
        'paper/word_provenance.json','paper/word_reference_profile.json','paper/word_native_render.json',
        'paper/word_preview_provenance.json','results/validation/CP-09-checks.json',
        'results/validation/CP-09-preview-pages.json','results/validation/CP-09-tests.json',
        'results/validation/CP-09-tests-final.log','results/validation/CP-09-focused-tests.log']
    result=dict(date='2026-10-07',checkpoint='CP-09 partial',native_word_page_review_pending=True,
        source_files=hashes,artifacts={name:digest(ROOT/name) for name in artifacts},
        final_seal_matches=True,final_csv_unchanged=True,analysis_unchanged=True,
        original_qenn_unchanged=True,document_links_match=True)
    (destination/'manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(source_files=len(hashes),bound_artifacts=len(artifacts),
        final_seal_matches=True,raw_and_analysis_unchanged=True,original_qenn_unchanged=True,
        document_links_match=True,checkpoint='CP-09 partial; native page review pending'),indent=2))


if __name__=='__main__': main()
