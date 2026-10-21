# Repository layout and GitHub upload

Run all commands from the project root. This reorganization changes file
locations and repository packaging; it does not change experimental results.

## Where files belong

| Folder | Contents |
|---|---|
| `docs/` | Requirements, design, strategy, tasks, simple explanation and usage |
| `docs/paper/` | Reproduction, literature and paper-review guides |
| `tests/` | Ordinary correctness and integration tests |
| `algorithms/`, `environments/` | Search/learning methods and grid rules |
| `training/`, `experiments/`, `evaluation/` | Training, runs, replay and analysis |
| `configs/` | Fixed experiment settings |
| `paper/` | Accepted paper, scientific sources, figures and provenance |
| `references/` | Original QENN document, preserved byte-for-byte |
| `results/raw/` | Immutable measurements, models and recorded actions |
| `results/analysis/` | Generated tables, figures and reports |
| `results/validation/` | Checkpoint evidence, historical source snapshots and tools |
| `scripts/` | Current repository verification and data packaging |
| `data/` | Paths, sizes and hashes for large separately distributed artifacts |
| `dist/` | Generated data bundle; ignored by Git |

The root `README.md` is GitHub's entry page. `AGENTS.md` remains at the root so
coding tools find the project instructions. One test, `test_final_protocol.py`,
stays at its original root path because it is covered by the immutable CP-07a
source seal. Root unittest discovery runs it and the tests package once each.

Scientific Markdown (`paper/paper.md`, `paper/methods_source.md`), the frozen
`configs/final_protocol.md`, generated result tables and archived Markdown keep
their verified paths. They are scientific artifacts or historical snapshots,
not working documentation. Moving or rewriting them would break recorded
provenance or the seal. All ordinary project documentation is under `docs/`.
`docs/relocation.json` records original/new paths and byte hashes at each move.

Historical checkpoint entries describe the layout at their original date. Older
archive helpers were one-time evidence tools and may refer to the old paths;
do not rerun them against a reorganized project. Use the current scripts below.
Original builder source fingerprints remain historical provenance; the working
paper tools now locate the unchanged formatting reference in `references/`.

## Check before upload

```powershell
python -m unittest discover -v
python scripts/check_repository.py
```

The checker verifies the frozen code/config/model seal, manuscript inputs, final
paper acceptance hashes, current Markdown links, moved files and measured data.
It also checks the large-artifact exclusions. A fresh clone without the separate
data bundle can run:

```powershell
python scripts/check_repository.py --allow-missing-large-data
```

That option reports missing large traces accurately. It does not claim they were
audited locally. Models, settings and metrics stay in the normal repository.
The automated Windows workflow runs correctness tests and this clone-safe check.
That workflow has not been executed on GitHub yet.

## Large research data

GitHub blocks ordinary Git files larger than 100 MiB. Release assets or Git LFS
can distribute larger data. See [GitHub's large-file guidance](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

Three measured traces above 50 MiB are excluded from Git, retained locally and
listed in `data/large-artifacts.json`. The file-specific ignore rules do not
discard smaller CSVs, models, JSON metadata, analysis or audit evidence.
Build the companion archive with:

```powershell
python scripts/build_data_bundle.py
```

This refuses to overwrite an existing bundle, verifies source hashes, compresses
the exact files and checks the archived contents. The prepared bundle is
`dist/graph-search-large-data.zip`; its fingerprint is in
`dist/large-data-bundle.json`. Upload both separately as assets on a GitHub
Release after creating the repository. No assets have been uploaded yet.

After cloning, download the bundle and extract it from the repository root:

```powershell
python -m zipfile -e graph-search-large-data.zip .
python scripts/check_repository.py
```

The bundle restores the original measured paths. Full replay of saved final and
pilot trajectories requires these files; new experiments generate their own
traces. Never replace missing traces with invented or empty data.

## Upload with Git

Create an empty GitHub repository, then run these commands. Replace the remote
URL with your own repository URL; inspect staged files before committing.

```powershell
git init
git add .
git status --short
git commit -m "Add reproducible graph-search research project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

If your folder is already a Git repository or has an `origin`, use its existing
setup instead of adding it again. No Git repository, commit or remote push was
created by the reorganization. No license was selected on the author's behalf;
choose a license before inviting others to reuse the code.
