"""Package large measured traces without editing them or publishing anything."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'dist/graph-search-large-data.zip')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'data/large-artifacts.json').read_text())
    output = args.output.resolve()
    if not output.is_relative_to(ROOT):
        raise ValueError('Write the data bundle inside this workspace')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        archive.write(ROOT/'data/large-artifacts.json', 'data/large-artifacts.json')
        for item in manifest['files']:
            source = ROOT/item['path']
            if source.stat().st_size != item['bytes'] or sha256(source) != item['sha256']:
                raise ValueError(f'Measured artifact changed: {item["path"]}')
            archive.write(source, item['path'])
            print(f'Packaged {item["path"]}', flush=True)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('Bundle integrity check failed')
        for item in manifest['files']:
            hasher = hashlib.sha256()
            with archive.open(item['path']) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    hasher.update(chunk)
            if hasher.hexdigest() != item['sha256']:
                raise ValueError('Archived content differs from measured source')
    proof = dict(bundle=output.relative_to(ROOT).as_posix(), bytes=output.stat().st_size,
                 sha256=sha256(output), files=len(manifest['files']), all_content_hashes_match=True)
    (output.parent/'large-data-bundle.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    main()
