# Graph Search Research

A reproducible comparison of BFS, Dijkstra, A* and single/shared-policy DQN
navigation on static and changing grids.

Author: **Madhav Joshi, Marwadi University**. CP-01 through CP-09 are complete.
The final study used 120 new maps and 15,120 unique evaluation episodes. Results
include failures and limitations; no universal DQN superiority is claimed.

## Paper and documentation

- [Final Word paper](paper/Graph_Search_Research_Paper.docx)
- [Reviewed native Word PDF](paper/Graph_Search_Research_Paper.pdf)
- [Requirements](docs/prd.md), [technical design](docs/tdd.md) and
  [implementation strategy](docs/implementationstrategy.md)
- [Checkpoint history and next steps](docs/task.md)
- [Simple project explanation](docs/everythingtoknow.md)
- [Full usage guide](docs/usage.md)
- [Reproduction guide](docs/paper/REPRODUCING.md)
- [Repository layout and GitHub upload](docs/GITHUB.md)

## Quick start

Run from the repository root with Python 3.12:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -v
python -m experiments.run_static --demo
```

The reorganized project passed all 142 tests (46.351 seconds). Details are
recorded in `docs/task.md`. Install the pinned dependencies
before running DQN or manuscript checks. Word export requires Microsoft Word on
Windows; the accepted DOCX/PDF are already included.

## Layout

```text
docs/           Working documentation, design and paper review guides
tests/          Ordinary correctness and integration tests
algorithms/     Classical search and DQN implementations
environments/   Single-agent and multi-agent grid environments
training/       Training entry points
experiments/    Seeded experiment runners
evaluation/     Replay audits, metrics, analysis and visualization
configs/        Experiment settings and frozen protocol
paper/          Manuscripts, figures, rendering code and provenance
references/     Preserved original formatting reference
results/        Immutable raw data, generated analysis and checkpoint evidence
scripts/        Repository checks and large-data packaging tools
data/           Manifest for separately distributed large files
dist/           Generated data bundle (ignored by Git)
```

`README.md` and `AGENTS.md` stay at the root for repository discovery. The frozen
`test_final_protocol.py`, `configs/final_protocol.md`, scientific Markdown and
archived Markdown retain their verified paths. Moving those would invalidate
the completed study's seal or provenance; see [layout notes](docs/GITHUB.md).

Large trajectory files are preserved locally and packaged separately. The Git
repository contains their SHA256 manifest, metrics, models and smaller evidence.
Restore the data bundle before replaying the saved full trajectories.

No GitHub repository, remote upload or publication acceptance is claimed.
