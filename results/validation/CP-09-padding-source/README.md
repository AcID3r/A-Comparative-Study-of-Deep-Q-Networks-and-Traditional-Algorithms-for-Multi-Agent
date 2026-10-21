# Graph-search research project

**A Comparative Study of Deep Q-Networks and Traditional Algorithms for Multi-Agent Shortest-Path Search in Dynamic Graphs**

Current checkpoint: **CP-08 — final experiment, scientific paper and review complete**.
The expanded 142-test suite passed, followed by three focused Word-preview checks.
Final collection includes 120 new maps, 15,120 unique episodes
and 45,360 timed rollouts; all 652,244 saved steps replayed correctly. Independent
checks verified 837 analysis groups and the preserved seal/models.
Read the [17-page paper PDF](paper/paper.pdf), [editable manuscript](paper/paper.md),
[LaTeX source](paper/paper.tex) or [reproduction guide](paper/REPRODUCING.md).
Author: **Madhav Joshi, Marwadi University**. PDF uses ReportLab; LaTeX was not
compiled locally. The [Word manuscript](paper/Graph_Search_Research_Paper.docx)
is delivered with matching reference geometry/columns and checked content.
CP-09 remains partial: first native export reviewed; table padding corrected.
The revised native Word page layout still needs export and review. An [independent preview](paper/Graph_Search_Research_Paper_preview.pdf)
and [remaining review instructions](paper/WORD_REVIEW.md) are provided.
The original document stays unchanged.

## Start here

The final experiment rules are in [configs/final_protocol.md](configs/final_protocol.md).
CP-07a checks and artifacts are recorded in
[results/validation/CP-07a.md](results/validation/CP-07a.md).
Final evidence: [CP-07b experiment](results/validation/CP-07b.md),
[CP-08 manuscript review](results/validation/CP-08.md), and
[scientific review](paper/SCIENTIFIC_REVIEW.md).
Word evidence: [CP-09 partial delivery](results/validation/CP-09.md).

1. Read [prd.md](prd.md) for the research scope and acceptance requirements.
2. Read [implementationstrategy.md](implementationstrategy.md) for the build order.
3. Read [tdd.md](tdd.md) for interfaces, design decisions, and test cases.
4. Read [task.md](task.md) for the current checkpoint and next actions.
5. Read [everythingtoknow.md](everythingtoknow.md) for a simple explanation.

Here TDD means **Technical Design Document**; it also describes our test-driven
development process.

## Run the actual tests

From this folder, with Python 3.12 (verified with 3.12.6):

```powershell
python -m unittest discover -v
```

The baseline and episode modules use only the standard library. DQN tests and
training use PyTorch, and learning curves use Matplotlib/NumPy, pinned in
`requirements.txt`. These packages were already installed for CP-04.
All **142 test methods** passed, including final protocol/seal/repeated-timer checks,
dynamic team changes/replanning,
versioned models, delayed team rewards,
training/evaluation audits, aggregation, joint conflict resolution, reservations,
priority sensitivity, trace replay, dynamic schedules, split isolation,
replanning, replay/targets/checkpoints, tiny real training pipeline tests,
paired analysis denominators, actual PDF equation/table/caption rendering,
DOCX content/geometry checks, rehashed measured-cell tampering and preview image bounds.
If setting up a new Python environment:

```powershell
python -m pip install -r requirements.txt
```

These correctness checks are not final research experiments.

## Single-agent environment

```powershell
python -m experiments.run_episode
```

This scripted demo checks goal arrival, rejected moves/timeouts, and starting at
the goal. See [CP-03 validation](results/validation/CP-03.md). To save a new trace,
add `--output results/validation/my-episode-trace.json`; existing files are not overwritten.

```python
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action, SingleAgentEnv

env = SingleAgentEnv(GridGraph(3, 3), (0, 0), (2, 2), max_steps=20)
observation, info = env.reset(seed=42)
observation, reward, terminated, truncated, info = env.step(Action.DOWN)
print(info["position"], reward, info["reward_components"])
```

Actions: 0=up, 1=down, 2=left, 3=right, 4=wait. Reset before the first step and
after completion. Waiting/rejected moves consume time but do not increase moves
or cost. Active turns cost -1; boundary attempts add -5, obstacles add -10,
arrival adds +100 once. No team bonus in the single-agent phase.

Observations are 13-float tuples: normalized position, signed goal direction,
four adjacent wall flags, four boundary flags, remaining-time fraction. The
feature names/version are exported by the module. Maps are fixed and unit-cost;
reset seeds are recorded without randomizing maps. This is a standalone API,
not a Gymnasium class. Single-agent DQN uses this observation/action contract.

## DQN training and evaluation

CP-04: 68 tests passed and 10,000 practice episodes were recorded across five
training seeds. Every final model reached the goal on the training map, using
8 or 12 moves versus the classical optimum of 8. This is not unseen-map evidence.
See [CP-04 validation](results/validation/CP-04.md) for the measured seed table,
artifact links, command history and matching code snapshot.

```powershell
python -m training.train_dqn --smoke
python -m training.train_dqn
```

The smoke run is explicitly one seed/20 episodes. The default development run
trains seeds 0–4 for 2,000 episodes each on the same fixed 5×5 map. It records
greedy evaluations before training, every 100 episodes, at the final model, and
after reload. These are training-map checks, not held-out performance evidence.
Exploration is disabled for greedy evaluation and gradients are disabled for
action selection. Invalid moves are not masked; the policy must learn from penalties.

Each unique directory under `results/raw/dqn_fixed/` stores config/environment/
source metadata, `training_episodes.csv`, `optimizer_updates.csv`,
`evaluations.csv`, `baselines.csv`, seed-specific models/trajectories, PNG/SVG
learning curves, `summary.json`, and a last-written `COMPLETE.json`.
Reward/success/loss curves use exploratory training episodes; greedy results
are recorded separately. Training, inference and total run times are separated.

Run a saved model on its recorded fixed map, or audit all its output:

```powershell
python -m evaluation.audit_dqn_run results/raw/dqn_fixed/YOUR_RUN_DIRECTORY
```

The auditor loads each model and reproduces its final greedy rollout. It checks
source hashes against the current code; after future code changes, use the matching
code version to repeat this audit. Checkpoints support inference restoration,
not exact training resume. CPU is used, with one torch thread and deterministic
operations. New runs preserve previous outputs. Hyperparameters are documented
in `configs/dqn_fixed.json` and `tdd.md`.

## Static multi-agent environment and planning

```powershell
python -m experiments.run_team_episode
python -m evaluation.audit_team_episode results/validation/CP-06a-final-episodes.json
```

To save another trace, add `--output results/validation/my-team-trace.json` to
the first command; existing files cannot be overwritten. These are scripted
correctness examples, not team research measurements. See
[CP-06a validation](results/validation/CP-06a.md).

```python
from algorithms.prioritized import prioritized_plan, plan_actions
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv

graph = GridGraph(2, 3)
starts, goals = ((0, 0), (1, 1)), ((0, 2), (0, 1))
plan = prioritized_plan(graph, starts, goals, method='astar', max_steps=5)
env = MultiAgentEnv(graph, starts, goals, max_steps=5)
observations, info = env.reset()
if plan.success:
    for tick in range(5):
        if info['success']:
            break
        observations, rewards, terminated, truncated, info = env.step(plan_actions(plan.paths, tick))
    print(info['makespan'], info['total_moves'])  # 2 turns, 3 moves
```

All actions are proposed together. Same-cell moves, edge swaps and cascading
blocked moves are rejected; valid following and larger rotations are allowed.
Arrived agents occupy their goals permanently. Local observation v2 has 17 floats
including four adjacent occupancy flags; v1 saved DQN models cannot consume it.
Per-agent rewards and attempts are separate from team done flags/actual collisions.
Prioritized BFS/Dijkstra/A* search cells and ticks, reserve vertices/edges/goals,
and optimize arrival turns including waits. Failures have no executable joint
plan. Priority order matters; global optimality/completeness is not guaranteed.
Unit-cost teams and shared learning are implemented; CP-06c adds dynamic teams.

## Shared-policy learning and comparison

```powershell
python -m training.train_team --smoke
python -m training.train_team
python -m experiments.run_team_comparison results/raw/dqn_team/20261006T193829020826Z_42837111
python -m evaluation.audit_team_run results/raw/dqn_team/20261006T193829020826Z_42837111
python -m evaluation.audit_team_run results/raw/team_comparison/20261006T194208884293Z_69d05e81
```

Training prints a new run directory. Replace the example training path to compare
a new run. The frozen config `configs/dqn_team.json` trains solo/shared policies
for five seeds and 1,000 cycles. Each cycle is one two-agent game for shared or
two separate route games for solo: 2,000 assigned navigation tasks per seed/mode.
Transitions/updates and bonus timing differ; actual budgets are recorded. Finished
agents contribute WAIT transitions until team end, retaining delayed team rewards.
No held-out maps or four-agent teams enter training. Final weights are retained.

Map bank: 50 train/10 validation/20 test unique geometries; 5×5 unit-cost grids,
.10 wall probability and seeded distinct endpoints. Old CP-04/05 geometries are
excluded, initially unreachable tasks retained. Test comparison includes two/four
agents, three prioritized planners and five seeds of solo/shared/untrained v2
policies: 720 episodes. DQN uses local inputs, planners the full map. No online
updates during greedy tests. v1 models remain loadable with their original inputs.

Full training/evaluation audits passed. Shared success was 61%/25% (two/four),
solo 64%/27%, classical planners 90%/80%; no shared success-superiority claim.
See [CP-06b validation](results/validation/CP-06b.md) and
[generated comparison](results/analysis/CP-06b/comparison.md).

```powershell
python -m evaluation.summarize_team results/raw/team_comparison/20261006T194208884293Z_69d05e81 --output results/analysis/my-new-team-comparison --training-run results/raw/dqn_team/20261006T193829020826Z_42837111
```

Use a new output path. The generator creates a measured comparison table,
success bars and training-return PNG/SVG plots. Raw runs save exact config/banks,
matching source copies/hashes, CSV metrics, JSONL actions/trajectories and completion
markers. Training checkpoints support inference restoration, not exact resume.

## Dynamic team evaluation

```powershell
python -m experiments.run_dynamic_team --smoke
python -m experiments.run_dynamic_team
python -m evaluation.audit_dynamic_team results/raw/dynamic_team/20261006T201424719291Z_678fc290
python -m evaluation.summarize_dynamic_team results/raw/dynamic_team/20261006T201424719291Z_678fc290 --output results/analysis/my-new-dynamic-comparison
```

The frozen profile `configs/dynamic_team.json` references completed CP-06b models.
Smoke uses two maps (168 episodes); full uses 20 (1,680). Every map is evaluated
with two/four agents, static/dynamic pairs, BFS/Dijkstra/A* replanning, labeled
frozen controls, and five seeds of solo/shared/untrained policies. Output paths
are unique; existing results/analysis cannot be overwritten. No online training.

Scheduled walls add at tick 2, remove at 8, protecting all endpoints and choosing
a distant cell to prevent method-dependent occupancy rejection. Empty schedules
and early completion exposure are recorded. Planners replan using the current
map/current positions and remaining horizon; failed plans wait until graph changes.
This is different from CP-06b's immediate failed-plan return; old data is preserved.
Frozen routes retry independently, so their original reservations can become
invalid after delays. Collision rejection and observation v2 stay unchanged.

Full audit passed for 32,194 steps and identical active event prefixes. All 720
comparable static metric rows match CP-06b. Dynamic main replanners succeed
90%/80% for two/four agents; shared policy 58%/25%, solo 61%/28%. These are small
development comparisons with static-trained models, local vs full-map information,
and previously evaluated test geometries. Final experiments need fresh banks.
See [CP-06c evidence](results/validation/CP-06c.md) and
[generated table](results/analysis/CP-06c/comparison.md).

## Single-agent random maps and changing obstacles

CP-05 trained five final models on 100 static training boards (2,000 episodes
each), with 10 separate validation boards and 50 held-out test boards. Banks are
geometry-disjoint and exclude CP-04's fixed board; unreachable maps are retained.
All boards here are 5×5 with .15 obstacle probability and fixed corner endpoints.
See [CP-05 validation](results/validation/CP-05.md) and the generated
[comparison](results/analysis/CP-05-final/comparison.md).

```powershell
python -m training.train_varied --smoke
python -m training.train_varied
python -m experiments.run_transfer --smoke
python -m experiments.run_transfer
python -m experiments.run_transfer --varied-run results/raw/dqn_varied/20261006T190337675250Z_18a4faf2
```

The last command uses the completed random-map run in this workspace. To compare
a new compatible run, replace its path with the training command's printed path.
Transfer also uses the fixed-map run specified in `configs/dqn_varied.json`.
The default transfer has 1,400 episodes; adding five varied-map models gives
1,900. Smoke transfer uses two held-out boards. Configs are frozen JSON.

Dynamic tests add a distant BFS-route wall before turn 3 and remove it before
turn 8. Planners replan on graph changes; frozen A* retries its original route.
DQN uses local observations, classical search the full map. Test-time learning
and exploration are disabled. Wall changes need not block every selected route.

```powershell
python -m evaluation.audit_varied results/raw/dqn_varied/20261006T190337675250Z_18a4faf2
python -m evaluation.audit_varied results/raw/transfer/20261006T191215326993Z_19602118
python -m evaluation.summarize_transfer results/raw/transfer/20261006T191215326993Z_19602118 --output results/analysis/my-new-comparison
```

Use a new analysis output path; existing folders are protected. Training runs
save per-episode/update CSV, validation JSONL, final models and PNG/SVG learning
curves. Evaluation runs save raw CSV, full trajectory JSONL and model digests.
Both save exact config, map banks, source copies/hashes and a last-written
completion marker. The auditor checks source copies and replays recorded routes.
These are small development comparisons, not completed multi-agent research.

## Classical baseline displays and measurements

```powershell
python -m experiments.run_static --demo
python -m experiments.run_static
```

The demo prints a fixed detour map and measurements for all three algorithms.
The smoke runner reads `configs/static_smoke.json`: 5×5, 10×10, and 15×15 grids,
obstacle probabilities 0.1 and 0.2, and map seeds 0–4. That makes 30 maps and 90
algorithm measurements. It protects start/goal cells and retains unreachable maps.

Each new directory under `results/raw/static_smoke/` contains:

- `raw_results.csv`: moves, cost, expanded nodes, measured planning seconds,
  success/failure, and returned paths.
- `scenarios.json`, `config.json`, `metadata.json`: exact maps/settings,
  environment information, metric definitions, and source-code hashes.
- `paths.txt` and `paths/*.svg`: text displays and standalone vector pictures.
  Open SVGs in a browser to inspect routes.
- `COMPLETE.json`: written last to mark successful output completion.

Existing runs are preserved. Timing varies; maps and non-time results repeat.
One timing sample per method per map is a smoke check, not a speed benchmark.
These are map seeds, not ML training seeds.

Optional CLI arguments:

```powershell
python -m experiments.run_static --config configs/static_smoke.json --output-root results/raw/static_smoke
```

See [CP-02 validation](results/validation/CP-02.md) for the recorded run.

## Use a baseline

```python
from environments.grid_graph import GridGraph
from algorithms.astar import astar

graph = GridGraph(3, 5, obstacles={(0, 2), (1, 2)})
path = astar(graph, (0, 0), (0, 4))
if path is None:
    print("No route exists")
else:
    print(path)
    print("Moves:", len(path) - 1)
    print("Cost:", graph.path_cost(path))
```

Coordinates are `(row, column)`. All searches include the start and goal in the
returned path. Invalid endpoints raise `ValueError`; unreachable goals return
`None`. BFS rejects graphs with unequal movement costs.

For measurements, use `bfs_result`, `dijkstra_result`, or `astar_result` from the
corresponding module. They return a `SearchResult` with `path`, `moves`,
`path_cost`, `expanded_nodes`, `planning_time_seconds`, `failure_reason`, and a
`success` property. Original functions still return paths. Expanded nodes count
processed nodes including the goal, excluding stale heap entries. Timing includes
validation, setup, search, and reconstruction; reporting and file I/O are excluded.

## Existing source file

`QENN_Research_Paper_Madhav_Joshi (1).docx` was already here. It describes a quantum
neural-network study, not this graph-search project. It remains untouched and is
not the specification for the current implementation. The supplied graph-search
brief is the current scope. This folder was not a Git repository at CP-01;
no remote repository or commit was created.

## Updating progress

Follow [AGENTS.md](AGENTS.md). Every project-changing iteration must update
`task.md` and `everythingtoknow.md`, record real verification evidence, and revise
the design documents when behavior or scope changes. Documentation does not
update itself; whoever makes the next change must update it.
