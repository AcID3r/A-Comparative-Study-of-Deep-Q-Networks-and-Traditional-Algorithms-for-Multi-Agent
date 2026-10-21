# Tasks and current checkpoint

Last updated: **2026-10-07**
Current completed checkpoint: **CP-09 complete: reviewed Word manuscript and native PDF**
Next checkpoint: **None in the authorized project plan**
Active state: **CP-01 through CP-09 complete; GitHub organization and data packaging complete**.
The authorized work through CP-08 is complete. The expanded 142-test suite passed,
and the latest three Word checks passed after preview corrections. Final run
`results/raw/final_transfer/20261006T212837810546Z_40b3d4c4` contains 120 new
geometries, 15,120 unique episodes and 45,360 fresh timed rollouts. Every saved
first trajectory and all 652,244 steps passed replay audit; 837 analysis groups
passed independent checks. Config/source/model/exclusion hashes remain sealed.
The full scientific manuscript is in `paper/paper.md`, `paper/paper.tex` and
the reviewed 17-page `paper/paper.pdf`, with seven figures, nine result tables,
nine verified primary references and confirmed author details: Madhav Joshi,
Marwadi University. The PDF uses ReportLab; no local TeX compilation is claimed.
QENN remains unchanged. `paper/Graph_Search_Research_Paper.docx` is now built
and structurally checked: 130 text blocks, ten tables, seven figures, two editable
equations and nine source links. Its independent 12-page preview is checked;
the user exported the final revision with Word 16.0: 11 pages. Every native
page was visually inspected, including numeric tables, figures and equations.
The long runtime values now fit intact. Native checks show zero out-of-page
text/images; structural checks verify all measured cells and original QENN.
CP-09 is complete. The 12-page preview remains an independent reconstruction;
the accepted native PDF is `paper/Graph_Search_Research_Paper.pdf`.

## Current repository layout

Working documents are now in `docs/`, paper-review guides in `docs/paper/`,
18 ordinary test modules in `tests/`, and the unchanged QENN reference in
`references/`. The root README introduces the project; AGENTS remains discoverable
at the root. Sealed `test_final_protocol.py` and immutable scientific/evidence
Markdown retain their original verified paths. Source packages and result paths
are unchanged. `docs/relocation.json` records 29 moves and their original hashes.
Current paper tools use the new reference path. Historical snapshots stay intact.

The prepared `dist/graph-search-large-data.zip` contains three large measured
traces (53,921,386 bytes, approximately 51.4 MiB), with exact content hashes checked.
The traces and dist are excluded from Git only, never deleted. Use
[GitHub instructions](GITHUB.md) for repository upload and companion Release assets.
No workspace Git repository, commit, remote or upload has been created.

## Current project state

- [x] Inspect workspace and existing paper.
- [x] Establish graph-search scope; preserve unrelated QENN Word document.
- [x] Write PRD, implementation strategy, technical design, and simple explainer.
- [x] Define iteration/checkpoint update rules in `AGENTS.md`.
- [x] Implement `environments/grid_graph.py`.
- [x] Implement `algorithms/bfs.py`, `dijkstra.py`, and `astar.py`.
- [x] Create `test_baselines.py` and execute real correctness tests.
- [x] Verify known path lengths and weighted optimal costs automatically.
- [x] Add baseline metadata, text/SVG visualization, and config-driven smoke runner.
- [x] Save and audit actual 30-map/90-measurement smoke output.
- [x] Implement and verify the single-agent episode environment.
- [x] Implement single-agent DQN and fixed-map training.
- [x] Implement replay, target networks, epsilon actions, checkpoints and plots.
- [x] Pass 68 tests and complete/audit the 20-episode DQN smoke run.
- [x] Finish/audit the five-seed, 2,000-episode development run and close CP-04.
- [x] Add random/unseen/dynamic maps.
- [x] Implement geometry-disjoint map banks and scheduled obstacle changes.
- [x] Verify replanning and frozen-path control; pass 82 tests.
- [x] Evaluate/audit fixed-model transfer on 50 held-out static/dynamic maps.
- [x] Finish/audit five-seed random-map training and final held-out comparison.
- [x] Add collision-safe static multi-agent environment and prioritized planning.
- [x] Train/evaluate static shared-policy DQN and compatible single-agent control.
- [x] Add changing obstacles and replanning for teams.
- [x] CP-07a: freeze the final protocol; audit the full pilot; save the final seal.
- [x] Run final seeded experiments and generate analysis.
- [x] Write the paper from completed experiments and verified sources.
- [x] CP-09: create and validate the complete Word manuscript in the QENN reference format.
- [x] CP-09: inspect reference format; create/check the separate complete DOCX.
- [x] CP-09: generate/check an independent preview, labeled as non-native.
- [x] CP-09: export from Word and inspect every native page before acceptance.

## Next concrete tasks, in order

No implementation checkpoint remains in the agreed scope.

1. Read the accepted Word manuscript and native PDF as the author.
2. Select a journal/conference and provide its required template, page limit and
   submission rules before any venue-specific formatting work.
3. Arrange supervisor/external review and any required independent reproduction.
   Publication acceptance and external review have not been completed or claimed.

## Checkpoint history

### Repository organization (2026-10-07): completed

**What/why:** Organized the working project for GitHub while preserving the
completed experiment seal, paper acceptance and historical evidence. Moved five
root working docs plus the old detailed README into `docs/`, four paper guides
into `docs/paper/`, 18 tests into `tests/`, and the original DOCX into `references/`.
Updated current Markdown links, AGENTS doc paths, one test helper import and four
paper-tool reference paths. Created a concise root README, `docs/GITHUB.md`,
`docs/relocation.json`, scripts, data manifest and Windows CI workflow. Updated
PRD/TDD/strategy/explainer. `.gitignore` keeps caches and three measured traces
above 50 MiB out of normal Git; smaller research evidence remains included.

**Exact main commands executed:**

```powershell
python -m unittest discover -v *> results/validation/repository-layout-tests.log
python scripts/build_data_bundle.py
python scripts/check_repository.py
python scripts/check_repository.py --allow-missing-large-data
python -m paper.check_word --output results/validation/repository-word-checks.json
```

Also ran Git ignore verification using a temporary bare repository, without
initializing the workspace repository. Its tested paths and outcome are recorded in `results/validation/repository-git-ignore.json`.

**Observed:** Full test discovery passed 142 tests in 46.351s, exit 0. Frozen
code/config/model/exclusion seal and manuscript inputs match. Accepted DOCX/PDF,
QENN bytes, final CSV and analysis unchanged. Current doc links resolve; no
ordinary Git candidate exceeds 100 MiB. Three traces compressed into a verified
53,921,386-byte ZIP; ZIP CRC checks and each uncompressed SHA256 match originals.
Git itself confirms exclusions and confirms README/docs/tests remain unignored.
No scientific results were edited, no training rerun, no native Word export needed.

**Evidence:** `results/validation/repository-layout-checks.json`,
`repository-layout-tests.log`, `repository-git-ignore.json`,
`repository-word-checks.json`, and `dist/large-data-bundle.json`.
Historical source paths are preserved in older checkpoint entries. The one-time
old archive helpers refer to their historical layout; use current scripts now.
GitHub CI is configured but has not executed remotely. No license selected.

**Next:** Choose an empty GitHub repository, follow `docs/GITHUB.md` Git commands,
and attach the prepared ZIP and its JSON fingerprint as Release assets. A fresh
clone can run tests/checks without those large traces; saved full-trajectory replay
requires extracting the companion bundle first. Author/venue review remains optional
next work outside the completed implementation scope.



### CP-09 (2026-10-07): completed after final native page review

**Evidence:** User ran `python -m paper.render_word`, `python -m paper.check_word`
and `python -m paper.review_word --native` successfully on the final DOCX.
Word 16.0 produced 11 pages, with zero out-of-page text/images. Agent inspected
all native page rasters 01-11 individually: title/author, column flow, all tables,
seven figures/captions, two editable numbered equations, sections and references.
Long Table X numeric values now fit intact. Multi-page tables repeat headers;
Table V starts with its caption/header at the end of page 7 and continues at the
top of the next column. This does not hide values. No further layout edit needed.

**Final fingerprints:** DOCX
`c77ec6f2fa852cf55588fdb138c4e64c3187589644d43da058bf42ec49626349`;
native PDF `e0e7a8e6b0e9e08613c61828303b71afae52060412b499ab6a67617695be0823`.

**Files:** Accepted existing final DOCX/PDF and native rasters. Updated task,
explainer, PRD/TDD/strategy, README and Word-review instructions. Added
`results/validation/accept_cp09.py`, acceptance JSON and final source snapshot.
Kept all earlier partial checkpoints and exports. No measured data or QENN edits.

**Agent commands:**

```powershell
python -m paper.check_word
python results/validation/accept_cp09.py
```

Structural check passed: 130 source text blocks, ten tables/all measured cells,
seven figure hashes, two numbered editable equations, nine reference links,
confirmed author and preserved reference. Latest relevant tests on this exact
DOCX passed earlier: three tests in 10.980s, including numeric-width regression.
The historical full suite passed 142 tests in 20.457s; it was not rerun for this
review/documentation-only completion. The acceptance helper verifies final
fingerprints, seal, unchanged data/analysis/reference, links and saved test evidence.

**Gate:** CP-09 complete; CP-01 through CP-09 are complete. Native activation
failed only in the agent session; user-terminal export provides real native
layout evidence. No venue-specific acceptance, external peer review or journal
submission is claimed. Next optional work is venue selection and author review.



### CP-09 numeric-width follow-up (2026-10-07): partial

Inspected all 11 pages of the user's second native PDF, SHA256
`ff33d3604a71232a6a1e0714e99ac45f3a3987df33b8b2e6de2fd9ce8ad04b72`.
Padding change fixed most digit wrapping, but Table X long runtime values
(e.g. 123.251) still wrapped. No missing figures, equations, sections or references
were detected. Preserved the export/source/proofs in
`results/validation/CP-09-native-padding-export/`; the old native PDF is also
`paper/Graph_Search_Research_Paper_padding_export.pdf`.

**Changed:** `paper/build_word.py` now measures each numeric string in 8pt Times
and allocates column minima with a four-point allowance for inset and tolerance.
Rebalances other columns while retaining the exact 4,869-twip table width.
`test_word_manuscript.py` independently checks every numeric cell's width against
its complete value; this catches the actual long-value regression. No scientific
values, fonts, graph code, training or data changed. Updated progress/design docs.

**Exact commands:**

```powershell
python -m paper.build_word
python -m paper.render_word
python -m paper.check_word
python -m unittest test_word_manuscript -v *> results/validation/CP-09-width-tests.log
python -m paper.preview_word
python -m paper.review_word
python results/validation/archive_cp09_widths.py
```

Builder and structural checks passed; all three focused tests passed in 10.980s,
including numeric widths, unchanged source/results, tamper rejection and preview
image bounds/equation labels. Native exporter failed in the agent session with
COM -2147023584. New DOCX SHA256:
`c77ec6f2fa852cf55588fdb138c4e64c3187589644d43da058bf42ec49626349`.
Native page acceptance stays pending. Next: user exports the newest version,
runs structural/native review, then all native pages are visually inspected.
Do not close CP-09 using either earlier export. No new full-suite run claimed;
the previous 142-test full run remains historical evidence.



### CP-09 native review follow-up (2026-10-07): partial

User ran `python -m paper.render_word`, `python -m paper.check_word` and
`python -m paper.review_word --native` successfully: 11 native pages, zero
out-of-page text/images. Inspected every page 01-11. Text, figures, equations and
references are present, but some table cells split decimal digits across lines.
The first export is preserved under `results/validation/CP-09-native-first-export/`
and `paper/Graph_Search_Research_Paper_first_export.pdf`.

Changed `paper/build_word.py` to reduce cell padding from default 108 to 20 twips;
rebuilt the DOCX without changing scientific content or measured table values.
Updated task, explainer, README, design/strategy and review documentation.

Exact commands:

```powershell
python -m paper.build_word
python -m paper.render_word
python -m paper.check_word
python -m unittest test_word_manuscript -v *> results/validation/CP-09-padding-tests.log
python -m paper.preview_word
python -m paper.review_word
python results/validation/archive_cp09_padding.py
```

Builder/content/preview checks passed. Three focused tests passed in 9.418s.
Revised preview automatic checks: 12 pages, no out-of-page text/images;
this iteration's preview visual inspection is not claimed. Word export failed
here with COM -2147023584. Revised DOCX SHA256:
`baf2e053877109b28b6592bfe84f24da53c9127dc227a32577063b6362c03426`.
First native PDF SHA256:
`c52f365eff093b5765ea00ff06fbd57f015dc5a71529d1a5d4f4cb14b98525b8`.
Next: rerun the three native commands in the user's terminal and inspect the
revised tables/pages. CP-09 remains partial. Research data and QENN unchanged.


### CP-09 — 2026-10-07 — partial: Word delivered, native layout pending

**Files:** Added `paper/build_word.py`, `word_figures.py`, `check_word.py`,
`render_word.py`, `preview_word.py`, `review_word.py`, `WORD_REVIEW.md`,
`test_word_manuscript.py`; generated DOCX, figure assets, format/provenance and
native-failure records, independent preview/raster/check outputs. Updated this
log, simple explainer, README, PRD, TDD, strategy and pinned existing DOCX packages.
Detailed evidence: [CP-09](../results/validation/CP-09.md).

**Exact commands:**

```powershell
python -m paper.build_word
python -m paper.render_word
python -m paper.check_word
python -m paper.preview_word
python -m paper.review_word
python -m unittest test_word_manuscript -v
python -m unittest discover -v *> results/validation/CP-09-tests.log
python -m unittest discover -v *> results/validation/CP-09-tests-final.log
python -m unittest test_word_manuscript -v *> results/validation/CP-09-focused-tests.log
python results/validation/archive_cp09.py
```

**Observed:** All creation/structural/preview/test commands exited 0; native Word
export returned nonzero with COM -2147023584 (no usable logon session). Native
active-instance lookup failed; LibreOffice absent and network download probe
unreachable. Actual Word pagination cannot be verified here. Structural checks
verify 130 blocks/all measured cells in ten tables/seven figure hashes/two native
equations/nine reference links and requested geometry/columns/headings.
Initial full suite 141/16.331s; expanded full suite 142/20.457s; final focused
three checks 3.609s, all OK. Rehashed measured-cell tampering is rejected.
Preview review found lazy-loaded equation scaling and number-label wrapping;
fixed both and added image-bound/intact-label regressions. Corrected independent
preview: 12 pages, no out-of-page text/images. Original QENN and data unchanged.
Body reference size is implicit: recorded explicit 11pt default assumption.
No final CP-09 acceptance until native export and all-page review succeed.
The archive helper checks document links, the experiment seal, raw results,
analysis and the preserved QENN file, then snapshots the new sources and binds
the delivered artifact hashes in `results/validation/CP-09-source/manifest.json`.

### CP-08 — 2026-10-07 — completed scientific manuscript/local review

**Files:** Added `paper/build_manuscript.py`, `render_manuscript.py`,
`check_manuscript.py`, `methods_source.md`, `references.json`,
`literature_review.md`, `author.json`, `REPRODUCING.md`, `SCIENTIFIC_REVIEW.md`,
`test_manuscript_tools.py`; generated Markdown/LaTeX/PDF, claim/provenance records,
equation images and rendered review pages. Pinned already-installed PDF packages.
Updated README, PRD, strategy, TDD and simple explanation. Evidence:
[CP-08](../results/validation/CP-08.md), `CP-08-checks.json`, `CP-08-tests.log`.

**Exact commands:**

```powershell
python -m paper.build_manuscript results/analysis/CP-07b
python -m paper.render_manuscript paper/paper.md --output paper/paper.pdf
python -m paper.check_manuscript results/analysis/CP-07b
python -m unittest test_manuscript_tools -v
python -m unittest discover -v *> results/validation/CP-08-tests.log
python results/validation/archive_cp08.py
```

**Observed:** All exited 0. Final full suite 139 tests/16.539s; regression suite
2 tests/0.920s. All required sections, nine result tables/seven figures/nine
references and claims match audited analysis; 17 pages have no out-of-page text.
Inspected all-page overview and critical pages/figures. Fixed literal bold
markers in A* captions, added a real rendered-PDF regression, regenerated and
rechecked. Author name/university explicitly confirmed. Original QENN unchanged.
No TeX engine, external peer review or venue acceptance is claimed. CP-09 remains.
The closure helper checks document links, preserved seal/QENN, manuscript hashes
and final test evidence, then snapshots new sources with a bound artifact manifest.
An initial ad-hoc metadata call omitted the seal-directory argument and failed
before writing anything; reran it with both required arguments successfully.

### CP-07b — 2026-10-07 — completed final experiment/analysis

**Files:** Added `evaluation/research_analysis.py`,
`evaluation/check_research_outputs.py`, `test_research_analysis.py`; saved final
raw run, `results/analysis/CP-07b-base`, extended `CP-07b` analysis, seven figures
in three formats, nine result tables, audit/check/test records and source archive.
Detailed evidence: [CP-07b](../results/validation/CP-07b.md).

**Exact commands:**

```powershell
python -m experiments.run_final --final
python -m evaluation.audit_final results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 --output results/validation/CP-07b-audit.json
python -m unittest discover -v
python -m evaluation.summarize_final results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 --output results/analysis/CP-07b-base
python -m evaluation.research_analysis results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 --audit results/validation/CP-07b-audit.json --output results/analysis/CP-07b
python -m evaluation.check_research_outputs results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 results/analysis/CP-07b --output results/validation/CP-07b-checks.json
python -m unittest test_research_analysis test_manuscript_tools -v
```

**Observed:** All exited 0. 120 fresh geometries, 15,120 unique episodes,
45,360 timed rollouts; all 652,244 saved steps replayed. Independent checks cover
837 groups, geometry exclusions, retained failures, gaps/pairing and hashes.
Full suite 139 tests/30.522s; later focused six tests/1.176s. Overall success:
BFS/Dijkstra 89.44%, A* 89.17%, solo 24.17%, shared 22.19%. These are measured
protocol-specific results, not universal rankings. All six mean paired static
policy/A* move differences are positive, often with ties. Shared success is
higher in two of six conditions, lower in four. No online training/tuning or
actual collisions. Local/full-map information, small-map transfer, conditional
metrics, fixed-priority planning and timer limitations are disclosed in the paper.
CP-08 writing/review followed; Word formatting is the remaining CP-09 work.

### CP-07b/CP-08 iteration — 2026-10-07 — execution in progress

Started `python -m experiments.run_final --final` using the unchanged CP-07a
seal. Added scientific analysis/pairing/plotting and independent output checking,
verified nine primary literature records, drafted the fixed scientific sections,
and prepared Markdown/LaTeX/PDF generation and PDF content/bounds review tools.
No final numbers or conclusions are written yet. New manuscript dependencies
ReportLab 4.4.10, pdfplumber 0.11.10 and pypdfium2 5.10.1 were already installed;
pinned them for reproducibility. No TeX engine is available, so PDF generation
uses ReportLab; the scientific LaTeX source will be supplied without a claim
that it was compiled. QENN remains untouched; CP-09 remains outside this turn.

Commands so far: `python -m unittest test_research_analysis -v` initially failed
one fixture missing `actual_collisions`; fixed the fixture and all four tests
passed (0.003s). Then `python -m unittest test_research_analysis test_manuscript_tools -v`
passed all six tests (6.781s), including an actual wrapped table/equation PDF,
PDF extraction/bounds checks, failure denominators and paired sample accounting.
The full experiment, final scientific analysis and manuscript are still pending.

### CP-07a — 2026-10-07 — completed protocol freeze and pilot audit

**Files:** Added `configs/final_experiment.json`, `configs/final_protocol.md`,
`evaluation/final_protocol.py`, `experiments/run_final.py`,
`evaluation/audit_final.py`, `evaluation/summarize_final.py`,
`test_final_protocol.py` and separate validation evidence/source/check scripts.
Updated README, PRD, implementation strategy, TDD and simple explainer.

**Decision:** Keep all ten final CP-06b v2 models without further training.
Evaluate transfer across sizes 5/10/15, .10/.20 wall probabilities, uniform/
crossing endpoint arrangements, 1/2/4 agents and static/dynamic conditions.
Crossing is an endpoint proxy with distance confounds, not guaranteed high
congestion. Horizons 30/60/90; final ten maps per size/density/arrangement =
120 geometries and 15,120 unique episodes. Three fresh timing rollouts provide
timer means, not extra independent outcomes. No pilot-based tuning/selection.

**Exact commands executed:**

```powershell
python -m unittest test_final_protocol -v
python -m unittest discover -v
python -m experiments.run_final
python -m evaluation.audit_final results/validation/protocol_pilot/20261006T210712802711Z_2c64fadb --output results/validation/CP-07a-audit.json
python -m evaluation.summarize_final results/validation/protocol_pilot/20261006T210712802711Z_2c64fadb --output results/validation/CP-07a-analysis
python -c "import json; from pathlib import Path; from evaluation.final_protocol import freeze; config=json.loads(Path('configs/final_experiment.json').read_text()); bank=json.loads(Path('results/validation/protocol_pilot/20261006T210712802711Z_2c64fadb/map_bank.json').read_text()); print(freeze(config,bank,Path('results/validation/CP-07a-freeze')))"
python results/validation/check_cp07a.py
```

**Observed:** Initially nine new tests passed (5.917s); then 132 full tests passed
(11.246s). The first pilot audit and added timing-path test failed because the
checker compared JSON coordinate lists with Python tuples. Corrected the
checker with JSON canonicalization; measured files were not edited. The final
ten-test protocol run passed (17.884s), followed by **133 full tests passed in
39.046s**. The timing integration used a pilot geometry/test-double seal, with
126 outcomes/three fresh rollouts each; real seal checks were tested separately.
It rejected a negative saved repeated timer. Final maps were not opened in tests.

**Pilot evidence:** `results/validation/protocol_pilot/20261006T210712802711Z_2c64fadb`.
Twelve geometries/strata, 1,512 unique episodes, 63,386 replayed steps, zero
empty schedules and zero actual collisions. All decisions, rewards, observations,
plans, CSV projections and common active-event prefixes matched. Source/model
digests passed and weights/update counters remained unchanged. Generated 648
stratified summary groups and matched/timing files under `CP-07a-analysis`.
Pilot data collection archived the pre-fix checker; the corrected validator is
preserved separately in CP-07a source evidence. This change affected validation
serialization only, not experiment outcomes. Previous runs were preserved.
Final evidence-check command exited 0: all summary denominators/means and
missing-value rules checked, matched sample counts 360/72/72/72, 280 excluded
geometries, 44 archived sealed source files, 27 local links checked and QENN hash
unchanged. Saved results in `results/validation/CP-07a-checks.json`.

**Gate:** CP-07a complete. Final config, sources, models, development-source
fingerprints and exclusions plus all pilot IDs are sealed under
`results/validation/CP-07a-freeze`. No final geometries/results or finished paper
exist yet. Next is CP-07b, then CP-08 and CP-09. Fixed priority/information gaps,
training-budget differences, crossing confounds, limited map counts and runtime
measurement limits remain explicit in the frozen protocol.

### Roadmap update — 2026-10-07 — CP-09 added; manuscript pending

User requested a complete separate graph-search Word paper in the same format
as `QENN_Research_Paper_Madhav_Joshi (1).docx` after CP-08. Added CP-09 to PRD,
strategy, technical design and simple explainer. Current completed checkpoint
remains CP-06c; next remains CP-07a. CP-09 is planned, not completed.

Read-only local inspection used Python `zipfile`/XML on the DOCX: A4 page size,
single-column title/author block followed by two-column body, Times New Roman
defaults, abstract/index terms, Roman-numbered sections, lettered subsections,
figure captions, Roman-numbered table captions and numbered equations. CP-09
must inspect precise run-level sizes/spacing and render its output for review.
Formatting is the reference; quantum text/results are not this study's content.
The original SHA-256 remains
`0EB7C34B6358DA752B52C38FD9AF9DAEAD8469C2DF2216DF1C272F07C47392F8`.
No implementation, training, measured results or Word source were changed.

### CP-06c — 2026-10-07 — completed dynamic team transfer

**Files:** Added `environments/dynamic_team_env.py`,
`evaluation/dynamic_team_protocol.py`, `experiments/run_dynamic_team.py`,
`evaluation/audit_dynamic_team.py`, `summarize_dynamic_team.py`,
`configs/dynamic_team.json`, `test_dynamic_team.py` and `test_dynamic_team_runner.py`.
Updated README and all five research documents. Added unique raw/source runs,
separate audit/regression JSONs, generated PNG/SVG analysis and
[CP-06c evidence](../results/validation/CP-06c.md). Prior source/core/model/data and
QENN document preserved; normalized the task document heading.

**Executed commands:**

```powershell
python -m unittest test_dynamic_team -v
python -m unittest test_dynamic_team test_dynamic_team_runner -v
python -m unittest discover -v
python -m experiments.run_dynamic_team --smoke
python -m evaluation.audit_dynamic_team results/raw/dynamic_team/20261006T201334953675Z_257e7353 --output results/validation/CP-06c-smoke-audit.json
python -m experiments.run_dynamic_team
python -m evaluation.audit_dynamic_team results/raw/dynamic_team/20261006T201424719291Z_678fc290 --output results/validation/CP-06c-audit.json
python -m evaluation.summarize_dynamic_team results/raw/dynamic_team/20261006T201424719291Z_678fc290 --output results/analysis/CP-06c
Get-FileHash -LiteralPath 'QENN_Research_Paper_Madhav_Joshi (1).docx' -Algorithm SHA256
```

**Checks:** Ten new unit tests passed in .010s; combined 12 tests in 8.420s.
Full **123 tests passed in 18.992s**, exit 0. Tests cover event visibility/version
timing, reset/idempotence, endpoint/occupied/no-op events, atomic validation,
termination/timeout, four-agent cascades, empty/default schedules, detours,
preserved arrival times, wait/recovery after failed plans, real saved-policy
pipeline and tampered-output detection. No dependencies installed.

**Runs/audits:** Smoke `20261006T201334953675Z_257e7353`: 168 episodes, 2,281
steps, two maps, audit exit 0. Full `20261006T201424719291Z_678fc290`: **1,680
episodes, 32,194 steps, 20 maps**, audit exit 0. No empty schedules in these banks.
Schedules protect all eight endpoints and are identical across methods/two-four
agent slices. Active event prefixes agree; completed episodes stop future events.
Model/source hashes match; in-memory weights/update counters stayed unchanged.
All decisions, planning outcomes, observations, rewards, counters and CSV rows
replayed; zero actual collisions. Plot visually inspected.

**Measured outcomes:** Dynamic replanners each succeed two/four: 18/20 (90%) and
16/20 (80%). Frozen controls two: 18/20; four: A* 13/20 (65%), BFS/Dijkstra 14/20
(70%). Dynamic shared: 58/100 and 25/100; solo: 61/100 and 28/100; untrained:
1/100 and 0/100. Tables generated from CSV. Shared DQN does not outperform the
main replanners in this development condition; no general significance/speed claim.

Inline Python regression compared 720 static rows against CP-06b for success,
makespan, moves/cost, attempts and actual collisions: all match. Word SHA-256
before/after matches `0EB7C34B6358DA752B52C38FD9AF9DAEAD8469C2DF2216DF1C272F07C47392F8`.
Evidence: `results/validation/CP-06c-regression.json`.
Final inline Python verification generated the report table from measured
analysis, archived 20 matching source/config/test files, checked all local links
in 16 Markdown files and counted 123 actual test definitions, exit 0. Both saved
audit records and the unchanged Word fingerprint were checked again.

**Decisions/limitations:** No training added. Policies transfer from static
two-agent training to dynamic two/four-agent episodes. Current-map planners do
not know future events; failed complete plans wait until graph changes. This
differs from CP-06b's immediate planning-failure return, so failure rewards/ticks
are not interchangeable with that earlier file. Frozen agents retry independently;
delays can break original reservations. Perturbations are mild and need not block
every route; early-goal cases may see fewer events. Twenty geometries were already
development test cases, not a fresh final blind test. Local DQN vs full-map planners,
fixed 5×5/.10/horizon30, priority sensitivity and successful-subset bias remain.
No dynamic/global optimality reference or completed paper. Next: CP-07a protocol.

### CP-06b — 2026-10-07 — completed static learning

**Files:** Extended `algorithms/dqn.py` with explicit v1/v2 layouts and versioned
transitions. Added `configs/dqn_team.json`, `evaluation/team_protocol.py`,
`training/train_team.py`, `experiments/run_team_comparison.py`,
`evaluation/audit_team_run.py`, `summarize_team.py`, and `test_team_learning.py`.
Updated all project documents/README. Saved new raw runs/source snapshots,
audit/legacy JSONs, generated PNG/SVG analysis and
[CP-06b evidence](../results/validation/CP-06b.md). Old measured data/QENN unchanged.

**Commands executed:**

```powershell
python -m unittest test_dqn test_training -v
python -m unittest test_team_learning -v
python -m unittest discover -v
python -m training.train_team --smoke
python -m evaluation.audit_team_run results/raw/dqn_team/20261006T193747713350Z_ac14d9ba --output results/validation/CP-06b-smoke-training-audit.json
python -m experiments.run_team_comparison results/raw/dqn_team/20261006T193747713350Z_ac14d9ba
python -m evaluation.audit_team_run results/raw/team_comparison/20261006T193809921031Z_cb313279 --output results/validation/CP-06b-smoke-evaluation-audit.json
python -m training.train_team
python -m evaluation.audit_team_run results/raw/dqn_team/20261006T193829020826Z_42837111 --output results/validation/CP-06b-training-audit.json
python -m experiments.run_team_comparison results/raw/dqn_team/20261006T193829020826Z_42837111
python -m evaluation.audit_team_run results/raw/team_comparison/20261006T194208884293Z_69d05e81 --output results/validation/CP-06b-evaluation-audit.json
python -m evaluation.summarize_team results/raw/team_comparison/20261006T194208884293Z_69d05e81 --output results/analysis/CP-06b --training-run results/raw/dqn_team/20261006T193829020826Z_42837111
```

**Observed checks:** Legacy unit/pipeline suite: 16 passed in 3.845s; eight new
tests passed in 2.784s. Full **111 tests passed in 5.903s**, exit 0. Tests cover
v2 predictions/reload, mixed-layout rejection, hand-calculated delayed rewards,
team termination/timeout targets, split exclusion, real tiny training/evaluation,
tampered training log rejection and failed/successful aggregation. Smoke training
saved 60 episodes/178 updates/six validation records; final validation solo 1/10,
shared 0/10. Smoke comparison has 240 episodes. Both audits passed.

An initial inline legacy probe imported an incorrect function name and failed;
the corrected probe used `evaluate_agent`. All five real v1 models then matched
saved success/move/arrival metrics and every action/observation/position exactly.
Evidence: `CP-06b-legacy-reload.json`, `CP-06b-legacy-trajectories.json`.

**Full run:** Ten final models (solo/shared × five seeds), 1,000 cycles each;
**15,000 episodes, 25,084 updates, 50 validation records, 20,000 agent tasks**.
Each mode/seed receives 2,000 tasks. Actual transitions and updates differ; see
the generated seed table. Geometry bank: train50/validation10/test20, excluding
CP-04 and all CP-05 maps; 45 duplicate candidates rejected. Initially individually
unreachable scenario counts for two agents: 0/1/2; for four: 2/1/2. None filtered.
Full training audit verifies every action/reward/counter, no test-map learning,
source snapshots, and final greedy reloads. Intermediate validation is replayed
for environment consistency; historical weights were not saved.

**Held-out results:** 720 episodes; all final decisions/observations/metrics replay
and checkpoint digests passed. Shared success two/four: **61/100, 25/100**; solo:
**64/100, 27/100**; untrained: **1/100, 0/100**. Each classical planner: **18/20,
16/20**. Shared mean rejected-agent attempts: 3.42/27.28, solo: 5.11/32.58.
Actual collisions zero due to the resolver. Shared training did not improve
success over the solo control here; no superiority/significance claim is made.
Success/return plots were visually inspected. Tables come from measured CSV.
Final inline Python verification generated the measured seed/budget tables,
archived 17 matching core/config/test files, verified all local links in 15
Markdown files and counted 111 actual test definitions, exit 0. Recorded totals:
solo 81,770 transitions/10,064 updates; shared 121,408 transitions/15,020 updates.

**Decisions/limits:** Replay all agents until team ending, forcing WAIT for arrived
agents so delayed bonuses enter learning. Keep every environment reward intact.
Task budgets match, not realized transitions/optimizer updates or bonus timing.
Control trains with zero occupancy; team deployment changes its inputs. Local DQN
information differs from full-map planners. Small static grids, fixed horizon,
five seeds and 20 shared test maps; successful-only averages use different subsets.
No four-agent training, dynamic teams, optimal team gaps or final paper yet.
Next: CP-06c before CP-07 final experiments.

### CP-06a — 2026-10-07 — completed foundation; CP-06 learning pending

**Files:** Added `environments/multi_agent_env.py`, `algorithms/prioritized.py`,
`experiments/run_team_episode.py`, `evaluation/audit_team_episode.py`,
`test_multi_agent_env.py`, `test_prioritized.py` and `test_team_episode.py`.
Updated README, PRD, technical design, strategy and both checkpoint explanations.
Saved correctness traces/audits and matching source snapshots under
`results/validation/`; no measured CP-04/05 output or QENN document changed.

**Commands executed:**

```powershell
python -m unittest test_multi_agent_env -v
python -m unittest test_multi_agent_env test_prioritized -v
python -m experiments.run_team_episode --output results/validation/CP-06a-episodes.json
python -m evaluation.audit_team_episode results/validation/CP-06a-episodes.json --output results/validation/CP-06a-audit.json
python -m unittest discover -v
python -m experiments.run_team_episode --output results/validation/CP-06a-final-episodes.json
python -m evaluation.audit_team_episode results/validation/CP-06a-final-episodes.json --output results/validation/CP-06a-final-audit.json
python -m unittest discover -v
```

**Observed outcomes:** First environment suite: 11 passed in .324s; combined
early suite: 18 passed in .199s. Adding priority sensitivity gave 101 full-suite
passes in 8.627s. After adding trace-tampering tests, a test fixture incorrectly
tried to mutate a tuple (103 tests, one error). Fixed the fixture to replace its
reward tuple; final **103 tests passed in 4.551s**, exit 0. Production traces and
audits exited 0: **16 cases, 26 replayed steps, nine successes, six planning
failures, one timeout, zero actual collisions**. The timeout records two rejected
agent conflict attempts. Exhaustive four-agent checks cover all 625 joint actions.

Wait example: makespan 2, total moves 3. Four lanes: makespan 3, total moves 12.
Default priority fails a selected two-agent case; reverse order succeeds in three
turns with four moves. Permanent occupied goals/horizon failures are explicit.
The initial five-file source snapshot matches initial traces; final sources are
archived separately. Full evidence: [CP-06a](../results/validation/CP-06a.md).
Final inline Python checks verified all local links in 13 Markdown documents,
103 actual test definitions and nine copied final source/test files, exit 0.

**Decisions:** Static unit-cost teams, absorbing goals, simultaneous conflict
resolution with cascading rejection, local 17-feature observation v2. Planning
optimizes arrival turns including waits; movement cost is separate. No partial
failed plan is executable. Team-completion bonus applies once, even to agents
that finished earlier; start-at-goal reset gives zero reward.

**Unresolved:** Shared learning, v2 model compatibility, dynamic teams, final
experiments and paper remain unfinished. Prioritized planning is order-sensitive
and not a complete or globally optimal team solver. Zero actual collisions here
demonstrate the movement referee, not learned coordination. Next: CP-06b.

### CP-05 — 2026-10-07 — completed

**Files:** Added `environments/dynamic_env.py`, `random_maps.py`,
`evaluation/navigation.py`, `varied_protocol.py`, `audit_varied.py`,
`summarize_transfer.py`, `training/train_varied.py`, `experiments/run_transfer.py`,
`configs/dqn_varied.json`, `test_dynamic_maps.py`, `test_navigation.py`, and
`test_varied_protocol.py`. Updated README and all five project documents. Saved
unique raw runs with matching source snapshots, audit JSONs, generated analysis
and [CP-05 validation](../results/validation/CP-05.md). CP-04 core/output and QENN
Word document were preserved.

**Why:** Test generalization and reactions to changing walls without leaking
held-out boards into learning or treating fixed paths as the main baseline.

**Commands executed:**

```powershell
python -m unittest test_dynamic_maps -v
python -m unittest test_dynamic_maps test_navigation -v
python -m unittest discover -v
python -m training.train_varied --smoke
python -m experiments.run_transfer --smoke
python -m evaluation.audit_varied results/raw/dqn_varied/20261006T190138076512Z_9b447057 --output results/validation/CP-05-smoke-training-audit.json
python -m training.train_varied
python -m experiments.run_transfer
python -m evaluation.audit_varied results/raw/transfer/20261006T190337779021Z_b2d1cdbd --output results/validation/CP-05-transfer-audit.json
python -m evaluation.summarize_transfer results/raw/transfer/20261006T190337779021Z_b2d1cdbd --output results/analysis/CP-05-transfer
python -m evaluation.audit_varied results/raw/dqn_varied/20261006T190337675250Z_18a4faf2 --output results/validation/CP-05-training-audit.json
python -m experiments.run_transfer --varied-run results/raw/dqn_varied/20261006T190337675250Z_18a4faf2
python -m evaluation.audit_varied results/raw/transfer/20261006T191215326993Z_19602118 --output results/validation/CP-05-final-audit.json
python -m evaluation.summarize_transfer results/raw/transfer/20261006T191215326993Z_19602118 --output results/analysis/CP-05-final
```

**Observed outcomes:** Initial missing-module test failed as expected before
implementation. Final suite: **82 tests passed in 8.731s**, exit 0. Static bank
contains 100 train/10 validation/50 test unique geometries; initially unreachable
counts 4/0/1, with seven duplicate candidates rejected. Full random training:
five seeds × 2,000 episodes, **10,000 episode rows, 74,961 updates, 105 validation
records**; final validation goals 9/10, 9/10, 9/10, 9/10 and 10/10. Training audit
verified selection seeds, no test-map learning, counters and model reloads.

The full initial transfer saved 1,400 episodes; final comparison saved **1,900**.
Both audits exited 0 and verified every action/observation, checkpoint digests
and identical realized obstacle histories. Generated
[comparison](../results/analysis/CP-05-final/comparison.md): varied DQN static
226/250 (90.4%), dynamic 221/250 (88.4%); fixed DQN 200/250 (80.0%) and 199/250
(79.6%); untrained 0/250 in both. Each classical replanner reached 49/50 (98%)
in both; the one initially unreachable map remains in every denominator.
Final comparison and training-success PNGs were visually inspected.
Final inline Python documentation check verified all local link targets in 13
Markdown files, counted 82 actual test definitions, and confirmed four saved
CP-05 audit records and the 1,900-episode final audit. It exited 0.

**Limitations/unresolved work:** Development grids are only 5×5 with fixed
corners and .15 obstacle probability. DQN sees local information, planners the
whole graph. Dynamic evaluation has no online learning; training maps were
static. BFS-route perturbations may leave another selected route unaffected;
frozen A* and replanning A* tied in this bank, so no adaptation-superiority claim
is supported. Successful-only path averages use different successful subsets;
seed variability is not a significance test. Dynamic optimality is not computed.
Multiple agents, larger final experiments and the paper remain unfinished.

**Next:** Begin CP-06 with a tested joint movement resolver, then reservation
planning. Do not begin shared training before these environment gates pass.

### CP-04 — 2026-10-06 — completed

**Files:** Added `algorithms/dqn.py`, `training/train_dqn.py` and initializer,
`configs/dqn_fixed.json`, `evaluation/evaluate_dqn.py`, `plot_learning.py`,
`audit_dqn_run.py`, `test_dqn.py`, and `test_training.py`. Pinned requirements,
ignored workspace plot cache, updated README/PRD/design/strategy and both logs.
Added actual smoke/full raw runs, audit JSONs, `results/validation/CP-04.md`,
and 27-file matching source/config/test snapshot with manifest. No prior measured
outputs or QENN document were changed.

**Why:** Complete real single-agent learning, verify inference checkpoint
compatibility, and measure actual outcomes before unseen/dynamic-map research.

**Commands executed:**

```powershell
python -m unittest test_dqn -v
python -m unittest discover -v
python -m training.train_dqn --smoke
python -m training.train_dqn
python -m evaluation.audit_dqn_run results/raw/dqn_fixed/20261006T103833572164Z_df572107 --output results/validation/CP-04-smoke-audit.json
python -m evaluation.audit_dqn_run results/raw/dqn_fixed/20261006T103855437859Z_d455330a --output results/validation/CP-04-audit.json
```

Initial DQN tests failed as expected before module creation. Then 11 DQN tests
passed in 7.865s; full **68 tests passed in 9.598s**, exit 0. Local imports verified
torch 2.11.0+cpu, numpy 1.26.4, matplotlib 3.10.0; no installation needed.

**Runs:** Smoke `20261006T103833572164Z_df572107`: 20 episodes, 164 updates,
final greedy timeout, no moves/return -50. Full `20261006T103855437859Z_d455330a`:
five seeds × 2,000 episodes, **10,000 episode rows, 63,887 updates, 115 greedy
evaluation rows**, five final models and PNG/SVG reward/success/loss curves.
All final policies succeeded on the training map: moves 12/8/12/8/12; arrival
ticks 12/9/15/14/14; classical optimum 8 moves. Both audits exited 0. Reloaded
Q-values/actions matched, and reward/epsilon/counter/timing/source checks passed.
Reward/success plots were visually inspected. The report's seed table is generated
from the actual summary, not manually filled.
Final documentation/archive audit passed: 68 test methods, 15 resolving local
links, 27 matching archived files, and CP-04 complete with CP-05 next.

**Limits/gate:** CP-04 complete. Fixed training map only, with intermediate
regressions and suboptimal final paths. No held-out/dynamic/multi-agent claim.
All final models retained; no hyperparameters changed in response to scores.
Checkpoints restore inference, not exact training resume. Next is CP-05.

### CP-03 — 2026-10-06 — completed

**Files:** Added `environments/single_agent_env.py`, `test_single_agent_env.py`,
`experiments/run_episode.py`, `results/validation/CP-03.md`, and actual trace
`results/validation/CP-03-episodes.json`. Updated README, PRD, design, strategy,
task log and simple explainer. Prior measured outputs/QENN document preserved.

**Why:** Verify movement, rewards, and episode boundaries before learning; freeze
the 13-feature local observation contract.

**Commands executed:**

```powershell
python -m unittest test_single_agent_env -v
python -m unittest discover -v
python -m experiments.run_episode --output results/validation/CP-03-episodes.json
```

First test run exited 1 (module absent, expected red). Initial implemented suite
passed 51 tests in 0.464s. Added reset-after-completion coverage; final full suite
exited 0: **52 tests passed in 0.504s**. Demo CLI exited 0: baseline arrival at
tick 8/8 moves/return 92; rejected-move/wait timeout at tick 3/0 moves/return -18;
start-at-goal success at tick 0/return 0. An inline Python saved-trace audit
checked all three outcomes, reward sums, feature count, and source hashes; exit 0.
Final inline Python audit passed: 52 parsed test methods, 10 resolving local
documentation links, correct CP-03/CP-04 status, and unchanged trace source hashes.

**Decisions:** Static unit-cost maps, deterministic reset, five actions, named
rewards, no single-agent team bonus. Last-turn goal arrival succeeds; start-at-goal
reset is done with zero reward. Steps before reset/after completion raise. CP-04
will mask both termination/truncation bootstrap for the finite-time objective,
with remaining-time fraction included in observation.

**Limits/gate:** CP-03 complete. Scripted correctness evidence only; no DQN,
random/dynamic environment, multiple agents, training or final paper results.
No packages installed. Next is CP-04 single-agent DQN.

### CP-02 — 2026-10-06 — completed

**Files changed:** Added `algorithms/search_result.py`; instrumented BFS,
Dijkstra, and A* while preserving path APIs. Added `evaluation/visualize.py`,
`experiments/run_static.py`, package initializers, `configs/static_smoke.json`,
`test_reporting.py`, and `test_static_runner.py`. Updated README, PRD, design,
strategy, task log, and simple explainer. Added `results/validation/CP-02.md`
and real smoke outputs. Existing Word document untouched.

**Why:** Make baseline paths inspectable and record real effort/time measurements
before learning. Use native SVG/JSON to stay dependency-free.

**Commands actually executed:**

```powershell
python -m unittest test_reporting -v
python -m unittest discover -v
python -m experiments.run_static --demo
python -m experiments.run_static
```

First reporting run: expected exit 1 with missing `bfs_result` import before
implementation. Full suite after implementation: exit 0, **31 tests passed in
0.563 seconds**. Both CLI commands exited 0. Demo methods each produced 8 moves,
cost 8, and 13 expansions; different equally good paths were allowed.

**Saved run:** `results/raw/static_smoke/20261006T095734387724Z_58f6ec4d/`.
There are **30 scenarios, 90 measured rows, and 90 SVGs**. An inline Python audit
loaded the saved maps, checked every row against the reference solver, parsed SVGs,
and verified source hashes. **84 rows succeeded and 6 unreachable rows remain**,
with missing moves/cost. All successful costs matched; timings were finite and
nonnegative. Details are in `results/validation/CP-02.md`.
Final documentation audit passed: all 8 local Markdown links resolve, the parsed
test-method count is 31, and both progress files show CP-02 with CP-03 next.

**Limits:** Static single-agent unit-cost smoke data; single timing sample and
fixed method order, so no speed conclusions. No DQN, dynamic maps, multi-agent
planner, or final paper results. No dependencies installed.

**Gate:** CP-02 complete; proceed to CP-03 environment transitions, rewards,
observations, and limits. CP-01 history is preserved below.

### CP-01 — 2026-10-06 — completed

**What changed:** Created `README.md`, `AGENTS.md`, `prd.md`,
`implementationstrategy.md`, `tdd.md`, `task.md`, `everythingtoknow.md`,
`requirements.txt`, `.gitignore`, the `environments` and `algorithms` packages,
and `test_baselines.py`. Recorded validation in
`results/validation/CP-01.md`. Existing DOCX unchanged.

**Why:** Establish a trustworthy classical baseline before learning experiments,
with understandable requirements and a durable record of progress.

**Verification actually performed:**

```powershell
python --version
python -m unittest discover -v
```

Observed Python **3.12.6**, Windows PowerShell. Test process exited **0**:
**15 tests passed in 0.083 seconds**, including 20 seeded uniform and 20 seeded
weighted maps, checked against a reference solver. Detailed coverage is in
`tdd.md`. Execution time is a test-suite duration, not an algorithm benchmark.
An additional Python file/link audit confirmed all required deliverables exist,
all relative Markdown links resolve, and the documented 15-method count matches
the parsed test file. The original DOCX remains present and untouched.

**Limitations:** No visualization, timing/expansion metadata, environment episode
interface, DQN, reservations, dynamic obstacles, experiment datasets, or paper
results yet. No third-party dependencies installed. Workspace is not initialized
as a Git repository; no commit or remote push performed.

**Gate decision:** CP-01 accepted because all implemented B01–B08 behaviors pass.
Week-one reporting/visualization work remains under CP-02.

## Required entry format for the next iteration

Keep this history and update the current state above. Record:
date/checkpoint; what changed and which files; why; exact validation commands;
observed pass/fail outcome; unresolved limitations; next ordered steps. Also
update `everythingtoknow.md`, and revise design docs when decisions change.
If a task is partly finished, leave its checkbox open and describe what remains.

Table-spacing sources and evidence are saved separately in
`results/validation/CP-09-padding-source/manifest.json` by the archive helper.
The helper checks links, preserved first-export source hashes and experiment seal.
