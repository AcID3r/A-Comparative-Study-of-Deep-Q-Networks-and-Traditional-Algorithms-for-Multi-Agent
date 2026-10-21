"""Verify reorganized paths, preserved evidence and normal-Git file sizes."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.final_protocol import check_freeze


def digest(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify(allow_missing=False):
    relocation = json.loads((ROOT/'docs/relocation.json').read_text())
    for old, entry in relocation.items():
        path = ROOT/entry['new_path']
        assert path.is_file(), entry['new_path']
        if old != 'README.md':
            assert not (ROOT/old).exists(), old
        if path.suffix != '.md' and old != 'test_static_runner.py':
            assert digest(path) == entry['sha256_at_move'], entry['new_path']
    check_freeze(json.loads((ROOT/'configs/final_experiment.json').read_text()),
                 ROOT/'results/validation/CP-07a-freeze')
    provenance = json.loads((ROOT/'paper/manuscript_provenance.json').read_text())
    for name, fingerprint in provenance['input_sha256'].items():
        assert digest(ROOT/name) == fingerprint, name
    assert digest(ROOT/'paper/paper.md') == provenance['manuscript_sha256']
    assert digest(ROOT/'references/QENN_Research_Paper_Madhav_Joshi (1).docx') == provenance['qenn_sha256']
    accepted = json.loads((ROOT/'results/validation/CP-09-acceptance.json').read_text())
    assert digest(ROOT/'paper/Graph_Search_Research_Paper.docx') == accepted['docx_sha256']
    assert digest(ROOT/'paper/Graph_Search_Research_Paper.pdf') == accepted['native_pdf_sha256']
    final = json.loads((ROOT/'results/validation/CP-07b-checks.json').read_text())
    assert digest(ROOT/'results/analysis/CP-07b/report.json') == final['report_sha256']
    assert digest(ROOT/'results/raw/final_transfer/20261006T212837810546Z_40b3d4c4/raw_results.csv') == final['raw_csv_sha256']
    links = 0
    for path in [ROOT/'README.md', ROOT/'AGENTS.md', *sorted((ROOT/'docs').rglob('*.md'))]:
        for target in re.findall(r'(?<!!)\[[^]]+\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if target.startswith(('http://', 'https://', '#')):
                continue
            assert (path.parent/target.split('#')[0]).exists(), (str(path), target)
            links += 1
    large = json.loads((ROOT/'data/large-artifacts.json').read_text())
    ignores = (ROOT/'.gitignore').read_text().splitlines()
    missing = []
    for item in large['files']:
        assert '/'+item['path'] in ignores, item['path']
        path = ROOT/item['path']
        if not path.exists():
            assert allow_missing, f'Restore the separate data bundle: {item["path"]}'
            missing.append(item['path'])
        else:
            assert path.stat().st_size == item['bytes'] and digest(path) == item['sha256'], item['path']
    excluded = {item['path'] for item in large['files']}
    oversized = []
    for path in ROOT.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if set(relative.parts) & {'.git', '.venv', 'venv', '.cache', '__pycache__', 'dist'}:
            continue
        if relative.as_posix() not in excluded and path.stat().st_size > 100*1024*1024:
            oversized.append(relative.as_posix())
    assert not oversized, oversized
    return dict(reorganized_files=len(relocation), local_markdown_links=links,
                frozen_seal_matches=True, measured_inputs_unchanged=True,
                accepted_word_and_pdf_unchanged=True, qenn_unchanged=True,
                large_files_excluded=len(excluded), missing_large_files=missing,
                ordinary_git_files_over_100_mib=oversized)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-missing-large-data', action='store_true')
    args = parser.parse_args()
    print(json.dumps(verify(args.allow_missing_large_data), indent=2))
