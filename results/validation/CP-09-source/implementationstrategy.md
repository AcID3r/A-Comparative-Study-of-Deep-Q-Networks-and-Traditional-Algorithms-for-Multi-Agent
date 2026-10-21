# Implementation strategy

Version: 1.11 | Updated: 2026-10-07

## Working approach

Build one verified layer at a time. Use small deterministic examples before
random tests and learning runs. Keep each checkpoint runnable from the project
root. The six-week sequence below is an order of work, not a promised deadline.

## Checkpoint sequence

| Checkpoint | Work | Exit evidence |
|---|---|---|
| CP-01 | Grid, BFS, Dijkstra, A*, input contracts and path tests | 15 passing test methods; completed |
| CP-02 | Baseline result metadata, text/SVG visualization, reproducible smoke runner | Completed: 31 tests pass; 30 scenarios/90 measurements and SVGs verified |
| CP-03 | Single-agent environment with wait, observation, rewards, termination | Complete: 52 tests pass; baseline replay and timeout traces verified |
| CP-04 | Replay buffer, online/target networks, epsilon schedule, fixed 5×5 training | Complete: 68 tests; five seeds/10,000 episodes; model reloads and output audits pass |
| CP-05 | Random and dynamic maps; unseen-map evaluation | Complete: 82 tests; 10,000 random-map training episodes; 1,900 held-out episodes replay-audited |
| CP-06a | Joint movement resolver, two/four agents and reservation planners | Complete: 103 tests; 625 joint actions; 16 scripted cases replay-audited |
| CP-06b | Compatible v2 single-agent control and shared-policy training | Complete: 111 tests, ten models, 15,000 episodes and 720 test episodes audited |
| CP-06c | Dynamic team schedules, reservation replanning and frozen controls | Complete: 123 tests; 1,680 paired episodes/32,194 steps audited; prior static metrics match |
| CP-07a | Freeze larger experiment protocol and validate small complete matrix | Complete: 133 tests; 1,512 pilot episodes/63,386 steps audited; final source/model/config/exclusion seal |
| CP-07b | Full final seeded runs and generated analysis | Complete: 15,120 cases, 652,244 replayed steps, 837 independently checked summaries; preserved seal/models |
| CP-08 | Evidence-backed manuscript and scientific review | Complete: 139 tests, 17-page reviewed PDF/MD/LaTeX; seven figures/nine result tables/nine verified sources |
| CP-09 | Full Word manuscript matching QENN reference formatting | Partial: DOCX/content/independent preview checked; native Word export/page review unavailable; original unchanged |

This follows the supplied order: baselines → one-agent DQN → changing maps →
multiple agents → final experiments → writing. Do not begin DQN while CP-02's
baseline tooling is unfinished.

## Implementation choices

Use Python standard-library `unittest` now to avoid installation obstacles.
Add pinned ML, configuration, and plotting dependencies only as their phase
starts. CP-01 uses immutable grids; a future environment creates a new snapshot
when obstacles change rather than editing a planner's map midway through search.

Keep algorithms separate so each is understandable. Dijkstra and A* share only
path reconstruction with BFS. Tests use a separate Bellman-Ford reference, known
distances, and independent adjacency assertions; agreement alone is not enough.

For CP-02 retain simple path-returning functions for existing callers. Introduce
a documented result interface for path, path cost, moves, expanded nodes, and
elapsed time without silently changing return types.

CP-02 now exposes `bfs_result`, `dijkstra_result`, and `astar_result` and keeps
the original functions as path-returning wrappers. Text/SVG generation and JSON
config use the standard library, so no plotting or YAML dependency is needed.
Use a fresh timestamp/UUID run directory; save exact maps, settings, environment
metadata, source hashes, paths, and a last-written completion marker. Reject
invalid configs before creating output. Keep failures with missing moves/cost,
not fabricated zeros. Fixed algorithm order and single timing samples mean these
smoke runs cannot support speed claims; design repeated timing trials at CP-07.

The single-agent environment should expose `reset(seed=...)` and `step(action)`
with observation, reward, termination, truncation, and component diagnostics.
Local observations will need normalization, goal displacement, local obstacles,
and later local occupancy. Lock the exact feature layout before creating saved
models. Local views can hide information, so acknowledge partial observability.

Start DQN with two 128-unit hidden layers, learning rate 0.001, discount 0.99,
batch 64, replay capacity 50,000, epsilon 1.0 to 0.05, and target copies every
1,000 optimizer steps. These are proposed defaults. Set the epsilon schedule,
warm-up, evaluation horizon, episode budget, and gradient limits before training.
Begin with a small smoke run, then determine the full 2,000–10,000-episode budget
from validation learning curves and available compute, not held-out test scores.

Do not bootstrap genuine terminal transitions. Explicitly decide how time-limit
truncation is handled. Evaluate with exploration disabled and model gradients
disabled; save architecture, feature layout, config, seeds, and weights together.

For multiple agents share policy weights and replay transitions, while each
agent supplies its own observation and action. Resolve all proposals together;
sequentially moving agents changes the problem. Classical baselines need
space-time search and waits with vertex and edge reservations; repeatedly
running static per-agent paths is insufficient. Define planning horizon and
priority order, then test failure cases and order sensitivity.

## Data layout as the project grows

```text
configs/                 frozen run and training configuration
environments/            grid and single/team episode environments
algorithms/              classical search, reservations and DQN
training/                fixed/varied/team training entry points
evaluation/              shared metrics, replay audits and scientific analysis
experiments/             static/dynamic/final runners
results/validation/      correctness-check evidence
results/raw/             immutable measured runs and trained checkpoints
results/analysis/        generated summaries and their figures
results/figures/         development charts where applicable
paper/                   scientific manuscript, verified sources and review
```

Only directories with current content are created at CP-01. Do not create fake
CSV results or empty DQN modules that suggest unfinished features work.

## Single-agent checkpoint decisions

CP-03 implements a standalone API in `environments/single_agent_env.py` with
fixed unit-cost maps and recorded seeds; no randomized transitions. Observation
v1 has 13 local features including remaining time. Goal bonuses apply once, with
no team bonus. Last-turn arrival succeeds. Reset-at-goal ends with no reward;
stepping completed episodes requires reset.

For CP-04 use a finite-horizon objective matching the time budget. Store
`terminated` and `truncated` separately but mask bootstrap for either flag:
there is no continuation beyond the allowed turns. If later studying continuing
tasks with a collection cutoff, explicitly revise this convention. Use only the
observation tuple as policy input, not diagnostics. Future occupancy features
require a new observation version and compatible newly trained models.

## Risk handling

CP-05 adds new environment/protocol modules without changing the verified CP-04
core. Freeze .15 obstacle probability for small development grids, geometry-
disjoint train/validation/test banks, and matched five-seed training budgets
before transfer evaluation. Retain unreachable maps and failed models. Scheduled
additions target a BFS-path cell far enough away to avoid policy-dependent
occupancy rejection; the selected route of another method may be unaffected.
Classical replanning sees the whole current map while DQN retains local v1 input.
Do not interpret this information difference as an architecture-only comparison.
Keep static random training, validation, held-out static transfer and dynamic
transfer separately labeled. Archive matching sources with every CP-05 run and
replay saved trajectories before accepting the checkpoint.

CP-04 uses the installed CPU PyTorch/Matplotlib stack, pinned in requirements.
The five-seed, 2,000-episode fixed-map development protocol is frozen in JSON.
First verify a 20-episode smoke run and the test suite, then finish the full run
without changing hyperparameters based on interim scores. Retain unsuccessful
models and evaluations. Test inference checkpoint restoration, not training
resume; generate charts from logs and audit every saved run before accepting
the checkpoint. Training-map success does not establish generalization.

If training fails, record failures and diagnose before adding architectures.
If compute is insufficient, document a reduced experimental scope before final
runs. If random scenarios are disconnected, preserve failure reasons and disclose
generation/filtering rules. If the model knows less than planners, explain the
information difference when interpreting results. Avoid equating simulator
collision rejection with learned coordination.

## Final protocol decisions — CP-07a

Use the frozen [protocol](configs/final_protocol.md): retain the existing final
solo/shared models and all five seeds, instead of retraining after inspecting
development test outcomes. Define the final result as transfer from static 5×5
training. Cover 5/10/15, .10/.20, uniform/crossing endpoint arrangements, 1/2/4
agents and static/dynamic cases. Freeze horizons at 30/60/90, ten final geometries
per size/density/arrangement and three deterministic timing rollouts, with only
one outcome per unique case. Crossing is an explicit proxy with distance confounds,
not a promised measured high-congestion category.

Capture all recorded development geometries plus the twelve pilot geometries as
exclusions. Keep final geometry ungenerated until CP-07b; save source/config/model
hashes in an exclusive seal after checks. Run the complete small pilot under
`results/validation`, replay every decision, generate stratified summaries and
exercise the repeated-timing path on pilot geometry. Do not tune from pilot scores.
At CP-07b verify the seal, run the 15,120-case matrix, audit it, and generate final
figures, descriptive seed uncertainty and stratified/matched hypothesis analyses.
New analysis modules may be added; changing sealed files requires an explicit
amendment/revalidation. CP-08/09 consume audited final evidence only.

## Checkpoint process

After each iteration: change → relevant checks → evidence → `task.md` update →
simple explanation in `everythingtoknow.md`. Revise design requirements when
needed and preserve checkpoint history. Next checkpoint: **CP-09**. Keep dynamic
team transfer separate from any future dynamic training. The CP-06b
comparison does not support shared-policy success superiority; retain settings
and failed episodes rather than tuning from held-out results.

## CP-07b/CP-08 closure — 2026-10-07

The frozen final transfer experiment, replay audit, analysis and scientific
manuscript are complete. New analysis/paper modules were added without changing
sealed simulation/search/training code. Generated success, exact single-agent
gap, paired hypotheses and timing tables retain failure/subset denominators.
The renderer's A* bold-caption defect was found by page review and fixed with a
rendered-PDF regression. Complete checks and commands are in
`results/validation/CP-07b.md` and `CP-08.md`. No model retuning, external peer
review or local TeX compilation is claimed. Next implement the separate CP-09
Word format using this reviewed scientific content and confirmed author details.

## CP-09 partial delivery — 2026-10-07

The separate DOCX and source/profile/provenance checks are delivered. Replot
figures for narrow-column readability without changing measured values; use
editable numbered math and source-derived tables. Keep CP-08 artifacts and the
reference unchanged. Native Word activation failed; do not treat the independent
12-page reconstruction as native pagination evidence. Final suite 142 tests and
latest three focused checks passed. Next finish native export/all-page review in
an interactive Word-capable session, then close CP-09. No new model tuning is
authorized or necessary for this formatting checkpoint.
