"""Preserve the numeric-width iteration without accepting unreviewed Word pages."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.final_protocol import check_freeze, digest


def main():
    check_freeze(json.loads((ROOT/'configs/final_experiment.json').read_text()),
                 ROOT/'results/validation/CP-07a-freeze')
    checks = json.loads((ROOT/'results/validation/CP-09-checks.json').read_text())
    assert checks['all_measured_cells_match'] and checks['reference_unchanged']
    assert checks['docx_sha256'] == digest(ROOT/'paper/Graph_Search_Research_Paper.docx')
    assert not checks['native_render']['native_render_complete']
    log = (ROOT/'results/validation/CP-09-width-tests.log').read_text(encoding='utf-16')
    assert 'Ran 3 tests in 10.980s' in log and '\nOK\n' in log
    preview = json.loads((ROOT/'results/validation/CP-09-preview-pages.json').read_text())
    assert preview['docx_sha256'] == checks['docx_sha256']
    assert preview['pdf_sha256'] == digest(ROOT/'paper/Graph_Search_Research_Paper_preview.pdf')
    assert preview['text_outside_page'] == preview['images_outside_page'] == 0
    previous = json.loads((ROOT/'results/validation/CP-09-source/manifest.json').read_text())
    for name in ('paper/Graph_Search_Research_Paper.docx', 'paper/build_word.py'):
        assert digest(ROOT/'results/validation/CP-09-native-first-export'/name) == (
            previous['artifacts'][name] if name.endswith('.docx') else previous['source_files'][name])
    assert digest(ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx') == '0eb7c34b6358da752b52c38fd9af9daead8469c2df2216df1c272f07c47392f8'
    docs = ['README.md', 'task.md', 'prd.md', 'tdd.md', 'implementationstrategy.md',
            'everythingtoknow.md', 'paper/WORD_REVIEW.md', 'results/validation/CP-09.md']
    for name in docs:
        path = ROOT/name
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if target.startswith(('https://', 'http://', '#')):
                continue
            assert (path.parent/target.split('#')[0]).exists(), (name, target)
    sources = docs + ['paper/build_word.py', 'test_word_manuscript.py', 'results/validation/archive_cp09_widths.py']
    destination = ROOT/'results/validation/CP-09-width-source'
    destination.mkdir(exist_ok=False)
    for name in sources:
        output = destination/name
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, output)
    artifacts = ['paper/Graph_Search_Research_Paper.docx', 'paper/word_provenance.json',
                 'paper/word_native_render.json', 'results/validation/CP-09-checks.json',
                 'results/validation/CP-09-native-pages.json',
                 'results/validation/CP-09-preview-pages.json',
                 'paper/Graph_Search_Research_Paper_preview.pdf',
                 'results/validation/CP-09-width-tests.log']
    result = dict(checkpoint='CP-09 partial', native_revised_review_pending=True,
                  focused_tests=3, elapsed_seconds=10.980, final_seal_matches=True,
                  original_qenn_unchanged=True, document_links_match=True,
                  sources={name: digest(destination/name) for name in sources},
                  artifacts={name: digest(ROOT/name) for name in artifacts})
    (destination/'manifest.json').write_text(json.dumps(result, indent=2)+'\n')
    print('Archived numeric-width sources and evidence; three focused tests passed; CP-09 partial.')


if __name__ == '__main__':
    main()
