# Product Requirements Document

Version: 1.13 | Date: 2026-10-07 | Active completed checkpoint: CP-08; CP-09 partial

## Purpose

Build a small, reproducible research project comparing classical search with
DQN navigation, then shared-policy DQN for several agents on static and changing
grids. The deliverables are working code, verified behavior, measured experiment
data, generated figures, and a paper whose claims match the evidence.

Paper title: **A Comparative Study of Deep Q-Networks and Traditional Algorithms
for Multi-Agent Shortest-Path Search in Dynamic Graphs**.

The researcher is the main user: they must be able to run tests, reproduce an
experiment, understand a failure, and explain every design decision.

## Current delivery and future scope

| Phase | Required capability | Current status |
|---|---|---|
| Baselines | Static four-direction grid; BFS, Dijkstra, A*; automatic path checks | Implemented and tested |
| Baseline reporting | Visualization, expanded nodes, elapsed planning time | Implemented and tested; text/SVG exports and seeded smoke CSV |
| Single-agent environment | reset/step, local observations, five actions, rewards/limits | Implemented and tested |
| Single-agent learning | Replay buffer, target network, DQN training | Implemented/tested; frozen five-seed run and audit complete |
| Changing maps | Random maps, unseen-map evaluation, scheduled obstacle changes | Implemented/tested; five-seed random training and held-out replay audits complete |
| Multiple agents | Simultaneous actions, collision handling, shared-policy DQN, prioritized baselines | Static learning and dynamic team transfer/replanning implemented/tested/audited |
| Experiments | Fixed configs, shared scenarios, seeds, raw data, generated analysis | Complete: 120 new geometries, 15,120 unique cases, 652,244 steps replayed; independent summaries/hashes checked |
| Paper | Methodology, measured results, discussion, limitations, verified references | CP-08 complete: full Markdown/LaTeX source and reviewed PDF, seven figures/nine result tables/nine references |
| Word deliverable | Separate full manuscript in QENN reference formatting | DOCX built/content checked; two native exports reviewed, numeric widths revised; fresh native acceptance pending, CP-09 partial |

No quantum learning, real robot hardware, GNNs, agent communication, or advanced
MARL methods are required. Those are outside the current implementation scope.

## Research questions and hypotheses

Main question: How does shared-policy DQN compare with BFS, Dijkstra, and A* for
multi-agent pathfinding under static and changing graph conditions?

Supporting questions address static performance, changing obstacles, collision
attempts, and scaling from one to two to four agents.

| Hypothesis | Planned operational test |
|---|---|
| H1: A* produces shorter paths than DQN in static settings | Compare successful runs on identical unit-cost maps; also report success rates and failures. Ties or contrary evidence can reject the hypothesis. |
| H2: DQN adapts more quickly than fixed precomputed paths after changes | Compare time and steps to completion after a scheduled change. Include replanning classical search as the main fair baseline; label frozen paths as a separate control. |
| H3: More agents reduce success and increase conflict attempts | Compare 1, 2, and 4 agents on matched conditions; rejection of conflicts can keep actual collisions at zero. |
| H4: Shared multi-agent training outperforms independently acting single-agent DQN | Evaluate a single-agent-trained policy deployed independently against a shared policy trained with multiple agents. Match observation/action formats and disclose training budgets. |

None of these is a result. Shared weights alone are not agent communication.
Classical methods receive the current full map; DQN is planned to receive a local
observation. Report this information difference explicitly, and later consider
an information-matched ablation if resources allow.

## Baseline requirements and acceptance criteria

| ID | Requirement | Acceptance evidence |
|---|---|---|
| B01 | Positive rectangular grid, free cells, fixed obstacles, orthogonal moves | Dimension, obstacle, boundary, and neighbor tests |
| B02 | BFS for equal costs | Known minimum move counts; non-unit equal costs supported; unequal costs rejected |
| B03 | Dijkstra for positive movement costs | Weighted detour and independent oracle checks |
| B04 | A* with an admissible grid heuristic | Same minimum costs as oracle, including costs below one |
| B05 | Common return contract | Path includes endpoints; unreachable returns `None`; invalid endpoints raise `ValueError` |
| B06 | Automatic path validity | Free, in-bounds cells and adjacent moves verified on returned paths |
| B07 | Deterministic repeatability | Fixed neighbor order, stable heap tie-breaking, fixed random test seeds |
| B08 | Protect map inputs | Caller mutation cannot change the constructed graph |

**CP-01 gate:** All B01–B08 checks pass. This gate is complete. Baseline timing,
visualization, and expansion reporting were separate remaining tasks at CP-01.

**CP-02 gate:** Measured-result APIs preserve path-only APIs; expansion counts
include non-stale processed nodes and the popped goal; known examples verify
counts. Text/SVG displays preserve walls and endpoints. A config-driven runner
uses identical maps across methods, retains failures, saves exact scenarios and
measurements, and preserves previous runs. This gate is complete. The 90-row
static single-agent smoke output verifies engineering behavior, not final findings.

**CP-03 gate:** Fixed unit-cost environment with five actions, versioned local
observations, named rewards, deterministic reset, movement/time metrics,
separate goal termination and timeout truncation, and start-at-goal/completed-step
rules. Baseline replay succeeds; unreachable maps time out without fake success.
This gate is complete. Weighted classical searches remain supported; this episode
environment currently rejects weighted maps. Recorded reset seeds do not randomize
its map or transitions.

## CP-04 acceptance requirements

**Gate complete:** 68 tests passed; five final models, 10,000 training episodes,
learning curves and saved-output audits are available. All final greedy models
reached the training-map goal, with 8 or 12 moves; the classical optimum is 8.
This measured development outcome does not answer the full research questions.

- Replay bounded and seeded; targets checked by hand, including both ending flags.
- Two hidden 128-unit layers and five action outputs; epsilon schedule, frozen
  target updates, MSE loss, gradient clipping, and no hidden map inputs.
- Inference checkpoint restores Q-values/actions and rejects incompatible inputs.
- Fixed 5×5 map protocol with independent training seeds 0–4, 2,000 episodes each;
  greedy evaluation uses the same map and is explicitly development evidence.
- Measured training/evaluation/update logs, version/config/source records, separate
  training and inference times, and charts generated from raw training CSV.
- Preserve failures and all final models even if an earlier checkpoint was better.
  Do not change settings or select a best model after examining these evaluations.
- Complete/audit saved outputs before accepting CP-04. Learning success is an
  observed outcome, not something to invent or make a correctness gate assume.

## CP-05 acceptance requirements

**Gate complete:** 82 tests pass. Five models finished 2,000 random-map episodes
each; training and 1,900 held-out evaluation episodes passed saved-output audits.
The development protocol uses 5×5 unit-cost grids, fixed corner endpoints, .15
obstacle probability, a 50-turn horizon, and geometry-disjoint banks of 100 train,
10 validation and 50 test maps. Keep initially unreachable maps and duplicates'
rejection records. This small gate does not replace the final experiment matrix.

- Schedule add/remove events before observations/actions; deterministic reset,
  protected endpoints, occupied additions rejected and explicit graph versions.
- Main classical methods replan after graph changes; frozen A* is a control.
- Train only on static training maps; observe validation without selecting best
  weights. Evaluate final weights on held-out static/dynamic maps with learning
  and exploration disabled. Dynamic transfer is not online adaptation training.
- Save exact maps, schedules, model/source fingerprints, counters and trajectories.
  Replay all held-out decisions and verify identical realized changes by method.
- Generate tables/figures from CSV; retain failures, report success denominators
  and successful-only path means. Do not invent dynamic optimality references.

## Remaining environment requirements

- Five actions for DQN and multi-agent planners: up, down, left, right, wait.
  CP-01 static searches have four movement edges and no wait action.
- Goals are absorbing for multi-agent evaluation: an arrived agent remains at
  its goal and occupies that cell. Reserve this occupancy in classical planning.
- Reject vertex conflicts and edge swaps. Movement into a cell vacated in the
  same tick is allowed if the joint move has no vertex conflict or swap; chain
  rejection must preserve occupancy. Test cascading rejection explicitly.
- Log collision **attempts** separately from actual overlapping occupancy.
- Obstacle changes occur before observations/actions for a tick; never add an
  obstacle to an occupied cell, start, or goal. Use reproducible schedules shared
  by all evaluated methods. Reachability filtering and unsolvable cases must be
  documented, rather than silently dropping failures.
- Begin dynamic work with obstacle addition/removal. Changing costs and moving
  obstacles are optional later extensions, not required for the first dynamic gate.

## Reward rules

Implemented single-agent rules: every active turn costs -1; an obstacle attempt
adds -10, a boundary attempt adds -5, first arrival adds +100. Arrival therefore
earns 99 on that turn. No separate team bonus applies. Invalid action encodings
raise without consuming time; wait/rejected moves consume turns but no moves.
Start-at-goal reset is a zero-turn, zero-reward success. Last-turn arrival wins
over timeout. Otherwise horizon exhaustion is failed truncation. Steps before
reset or after completion raise without altering state.

For the implemented static multi-agent environment, each active agent receives -1, plus -10 for an obstacle attempt,
-5 for an out-of-bounds attempt, -25 for a conflict attempt, +100 once on first
arrival, and +100 once per agent on team completion. Waiting has the active step
cost. Already finished agents receive no step cost. The obstacle and boundary
penalties are mutually exclusive; count rewards by named component. This is a
verified static multi-agent design before training. Finished agents receive the
one-time team bonus when the last agent arrives; reset-at-goal gives no bonus.
Collision and team reward components do not apply to the single-agent environment.

## CP-06 foundation gate

CP-06 is split into CP-06a (environment/planners), CP-06b (learning), and CP-06c
(dynamic teams), so a
verified foundation is not mistaken for completed multi-agent learning.
**CP-06a complete:** 103 tests pass; static unit-cost two/four-agent episodes,
joint vertex/swap/cascade rejection, absorbing goals, separate attempts/collisions,
named rewards and v2 local occupancy observations are implemented. Prioritized
BFS/Dijkstra/A* use waits and space-time vertex/edge/goal reservations, minimize
arrival turns, and explicitly report priority/horizon failures. Saved scripted
traces pass replay audit. Dynamic team scheduling/replanning is added at CP-06c;
v1 checkpoint weights are preserved and accept v1 observations, while new v2
models accept the team's 17 features.

**CP-06b complete:** 111 tests pass; ten final models across five seeds, task-
matched static two-agent/solo training, and 720 held-out two/four-agent episodes
are saved and audited. Every agent remains in replay until team end, with forced
WAIT after own arrival; all named rewards, including delayed team bonuses, are
retained. No bootstrap beyond team termination or finite-horizon truncation.
Train/validation/test geometries are disjoint and exclude prior fixed/varied maps.
Keep final weights without test-based selection; count unsuccessful episodes.
Generated comparisons report realized training budgets and shared-policy success
below solo control here. These measured development outcomes do not establish
H4 or complete dynamic multi-agent research. CP-06c adds the dynamic team gate.

**CP-06c complete:** 123 tests pass; scheduled team changes prepare before action
observations, protect endpoints/occupancy, restore on reset and stop after episode
completion. Replanners use current positions/current graph and remaining horizon,
including arrived agents' reserved goals. No complete plan means joint WAIT until
graph changes; frozen routes are separate controls. Saved static-trained policies
receive no online updates. Full 1,680-episode static/dynamic comparison and event
prefix/model/source audits pass. Empty schedules and early completion exposure
are recorded. Development cases remain distinct from a new final blinded matrix.

## Experiment requirements

Planned grid sizes: 5×5, 10×10, 15×15. Planned agent counts: 1, 2, 4.
Start with obstacle densities 0.10 and 0.20; define congestion through explicit
scenario generation before claiming low/high congestion comparisons.
Use at least five independent training seeds and held-out evaluation maps with
recorded scenario seeds. Freeze hyperparameters before final evaluation.

Every method runs on the same initial scenarios and obstacle schedules.
Distinguish training seeds, map seeds, training maps, validation maps, and held-out
test maps. Classical planners replan on graph changes from current positions.
BFS is evaluated only for uniform costs; weighted comparisons use Dijkstra/A*.
Prioritized planning is neither complete nor globally optimal.

Metrics must have fixed definitions:

- Success: all agents arrive within the declared episode horizon.
- Total moves: sum of non-wait executed moves across agents.
- Sum of arrival times: sum of first-arrival ticks, including pre-arrival waits.
- Makespan: last first-arrival tick. Report successful cases separately from
  timeout/censored failures; never report a timeout as a completed makespan.
- Path cost: sum of executed destination-cell costs; waits tracked separately.
- Conflict attempts: vertex/swap conflicts proposed, using a documented counting
  rule; actual collisions are separately checked as a safety invariant.
- Gap: compare with an exact static single-agent optimum where available. For
  multi-agent or dynamic settings, label a reference/bound explicitly. Independent
  shortest paths are a lower bound, not a guaranteed feasible team solution.
  A zero reference gives an undefined ratio; report it as missing with a reason.
- Time: training wall time, action-selection time, planning/replanning time, and
  complete episode time separately. Record CPU/GPU and library versions.
- Expanded nodes: defined and instrumented for classical search before collection.

Report failures and sample counts alongside successful-path averages to avoid
making an unreliable method look good by excluding failed episodes. Aggregate
uncertainty across independent training seeds rather than treating all episodes
from one model as independent training runs.

Raw logs are immutable experiment outputs. Tables and figures must be generated
from them. Never fill a paper result with a guess. References in the supplied
brief need source verification during the literature-review phase.

### Frozen CP-07 protocol

The accepted final design is recorded in [final protocol](configs/final_protocol.md)
and `configs/final_experiment.json`. Use all ten final CP-06b v2 models unchanged;
no additional training or test-based selection. This is static-small-map training
followed by size/agent/dynamic transfer, not models optimized per final condition.
One-agent final evaluation also uses the v2 team environment. Preserve v1 work
as separate development evidence.

The final matrix contains 120 fresh geometries: ten for each size/density/
endpoint-arrangement stratum, crossed with 1/2/4 agents, static/dynamic conditions
and 21 method/model combinations = 15,120 unique episodes. Three fresh timing
rollouts per episode do not increase outcome denominators. Horizons are 30/60/90.
Pilot geometry is separate; final geometry excludes it and all recorded
development cases. Keep unreachable cases and log generation rejections.

Uniform and opposing-boundary crossing endpoints operationalize congestion
proxies; they do not guarantee low/high congestion, and endpoint distance is
a confound. Record initial independent BFS-route overlaps. This explicit proxy
replaces an undefined low/high label, without claiming a new congestion metric
measures actual collisions. Retain route-independent event safety and missing
dynamic/team optimum gaps. Report success-conditioned path means, exposed-event
completion denominators, five-seed descriptive variability and matched cases.
Prioritized planning/information/timing/sample-size limitations remain explicit.

CP-07a closure requires tests, full pilot replay audit, generated denominator
checks, QENN preservation and a hash seal before final case generation. CP-07b
requires the sealed full run, audit and final generated analyses/figures.

## Completion criteria

### CP-09 submission manuscript

After CP-08's reviewed graph-search manuscript, deliver a separate full Word
document at `paper/Graph_Search_Research_Paper.docx` using the existing QENN DOCX
as a formatting reference. Preserve the reference unchanged; copy layout/style,
not its quantum methodology, claims, results or citations. Use the graph-search
paper title and all sections required by this PRD, with verified author details,
audited final results, generated figures/tables, readable equations, verified
references and explicit limitations. No placeholders or invented findings.

Match page geometry, fonts, title/author layout, columns, heading hierarchy,
caption/equation/citation conventions. Check the generated DOCX contents and
rendered layout for clipping, overflow and missing figures. Link all measured
claims to final raw/analysis artifacts in a separate provenance record. An
explicit submission venue/template, if later supplied, takes precedence over
the reference's general layout. Delivering the manuscript does not imply acceptance.

The project is complete only after the planned methods, required tests, seeded
evaluation, generated analysis, reviewed manuscript (CP-08) and validated full
Word deliverable (CP-09) are delivered.
Passing baseline tests alone completes the first milestone, not the research.
