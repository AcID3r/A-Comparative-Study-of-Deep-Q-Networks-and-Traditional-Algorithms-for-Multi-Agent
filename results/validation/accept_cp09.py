"""Bind the completed manual native-page review to the exact reviewed files."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evaluation.final_protocol import check_freeze, digest

DOCX = 'c77ec6f2fa852cf55588fdb138c4e64c3187589644d43da058bf42ec49626349'
PDF = 'e0e7a8e6b0e9e08613c61828303b71afae52060412b499ab6a67617695be0823'


def main():
    # These fixed fingerprints restrict acceptance to pages actually inspected.
    assert digest(ROOT/'paper/Graph_Search_Research_Paper.docx') == DOCX
    assert digest(ROOT/'paper/Graph_Search_Research_Paper.pdf') == PDF
    native = json.loads((ROOT/'paper/word_native_render.json').read_text())
    assert native['native_render_complete'] and native['source_sha256'] == DOCX
    assert native['pdf_sha256'] == PDF and native['pages'] == 11
    checks = json.loads((ROOT/'results/validation/CP-09-checks.json').read_text())
    assert checks['docx_sha256'] == DOCX and checks['all_measured_cells_match']
    assert checks['reference_unchanged'] and checks['tables_checked'] == 10
    provenance = json.loads((ROOT/'paper/word_provenance.json').read_text())
    assert provenance['docx_sha256'] == DOCX
    assert provenance['builder_sha256'] == digest(ROOT/'paper/build_word.py')
    review_path = ROOT/'results/validation/CP-09-native-pages.json'
    review = json.loads(review_path.read_text())
    assert review['docx_sha256'] == DOCX and review['pdf_sha256'] == PDF
    assert review['native_word_render'] and review['page_count'] == 11
    assert review['text_outside_page'] == review['images_outside_page'] == 0
    assert review['required_sections_and_main_rates_present']
    assert all((ROOT/review['review_directory']/f'page_{i:02d}.png').exists()
               for i in range(1, 12))
    check_freeze(json.loads((ROOT/'configs/final_experiment.json').read_text()),
                 ROOT/'results/validation/CP-07a-freeze')
    final = json.loads((ROOT/'results/validation/CP-07b-checks.json').read_text())
    assert digest(ROOT/'results/raw/final_transfer/20261006T212837810546Z_40b3d4c4/raw_results.csv') == final['raw_csv_sha256']
    assert digest(ROOT/'results/analysis/CP-07b/report.json') == final['report_sha256']
    assert digest(ROOT/'QENN_Research_Paper_Madhav_Joshi (1).docx') == '0eb7c34b6358da752b52c38fd9af9daead8469c2df2216df1c272f07c47392f8'
    log = (ROOT/'results/validation/CP-09-width-tests.log').read_text(encoding='utf-16')
    assert 'Ran 3 tests in 10.980s' in log and '\nOK\n' in log
    docs = ['README.md', 'task.md', 'prd.md', 'tdd.md', 'implementationstrategy.md',
            'everythingtoknow.md', 'paper/WORD_REVIEW.md', 'results/validation/CP-09.md']
    for name in docs:
        path = ROOT/name
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if not target.startswith(('https://', 'http://', '#')):
                assert (path.parent/target.split('#')[0]).exists(), (name, target)
    destination = ROOT/'results/validation/CP-09-completed-source'
    destination.mkdir(exist_ok=False)
    review['visual_review'] = 'Completed: all 11 native pages inspected individually; numeric values, tables, figures, equations, captions, columns and references readable.'
    review['review_date'] = '2026-10-07'
    review['checkpoint_complete'] = True
    review_path.write_text(json.dumps(review, indent=2)+'\n')
    acceptance = dict(date='2026-10-07', checkpoint='CP-09 complete',
                      docx_sha256=DOCX, native_pdf_sha256=PDF, native_pages=11,
                      manual_visual_review=review['visual_review'],
                      structural_checks_passed=True, focused_tests=3,
                      focused_test_seconds=10.980, previous_full_suite_tests=142,
                      final_seal_matches=True, raw_results_unchanged=True,
                      analysis_unchanged=True, original_qenn_unchanged=True,
                      venue_acceptance_claimed=False,
                      page_flow_note='Table V caption/header at end of page 7; repeated header and complete body continue in the next column.')
    (ROOT/'results/validation/CP-09-acceptance.json').write_text(json.dumps(acceptance, indent=2)+'\n')
    sources = docs + ['paper/build_word.py', 'test_word_manuscript.py',
                      'results/validation/accept_cp09.py']
    for name in sources:
        output = destination/name
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/name, output)
    artifacts = ['paper/Graph_Search_Research_Paper.docx', 'paper/Graph_Search_Research_Paper.pdf',
                 'paper/word_provenance.json', 'paper/word_native_render.json',
                 'results/validation/CP-09-checks.json',
                 'results/validation/CP-09-native-pages.json',
                 'results/validation/CP-09-acceptance.json',
                 'results/validation/CP-09-width-tests.log']
    manifest = dict(acceptance=acceptance,
                    sources={name: digest(destination/name) for name in sources},
                    artifacts={name: digest(ROOT/name) for name in artifacts},
                    rendered_pages={f'page_{i:02d}.png': digest(ROOT/review['review_directory']/f'page_{i:02d}.png') for i in range(1,12)})
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(acceptance, indent=2))


if __name__ == '__main__':
    main()
