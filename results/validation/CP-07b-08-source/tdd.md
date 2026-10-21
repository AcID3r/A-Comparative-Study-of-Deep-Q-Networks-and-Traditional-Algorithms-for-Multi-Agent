# Technical Design Document and test plan

Version: 1.10 | Updated: 2026-10-07 | CP-08 complete; CP-09 Word deliverable next

## Implemented components

```text
test_baselines.py
    → GridGraph in environments/grid_graph.py
    → bfs / dijkstra / astar in algorithms/
    → independent reference solver in the test file
```

`GridGraph(rows, cols, obstacles, cell_costs)` stores a fixed graph snapshot.
Positions are integer `(row, column)` tuples. Obstacles are copied into a
`frozenset`; cost mappings are copied and exposed read-only. Dimensions must be
positive integers; Boolean dimensions and coordinates are rejected.

Each free cell is a node. Valid edges connect orthogonal free neighbors. Neighbor
order is up, down, left, right. Entering a destination costs its configured value,
otherwise 1. The starting cell costs nothing. Costs must be finite and strictly
positive; obstacle costs are rejected. Because costs depend on destination,
opposite directions can have different costs. This is not an arbitrary-edge
weighted graph implementation.

## Public contracts

| API | Contract |
|---|---|
| `in_bounds(position)` | Whether the position is a well-formed in-grid coordinate |
| `is_free(position)` | In bounds and not blocked |
| `neighbors(position)` | Fixed-order free neighbors; invalid source raises `ValueError` |
| `cost(destination)` | Positive cost to enter a free cell; invalid cell raises `ValueError` |
| `path_cost(path)` | Validate adjacency and sum destination costs; singleton costs zero; empty/invalid raises `ValueError` |
| `bfs(graph, start, goal)` | Minimum-move path for equal costs; unequal costs raise `ValueError` |
| `dijkstra(graph, start, goal)` | Minimum-cost path for accepted positive costs |
| `astar(graph, start, goal)` | Minimum-cost path with scaled Manhattan heuristic |

All planners return `list[Position]` including both endpoints, or `None` when no
path exists. Invalid/blocked endpoints raise `ValueError`. A valid equal start
and goal returns a singleton. Different algorithms may choose different paths
with equal optimal cost; tests must not require identical paths.

The documented input types are the API boundary; no support is promised for
arbitrary malformed containers or third-party graph classes.

## CP-02 reporting APIs

`bfs_result`, `dijkstra_result`, and `astar_result` return `SearchResult` from
`algorithms/search_result.py`. Original functions delegate and return its path.
Fields: `path`, `moves`, `path_cost`, `expanded_nodes`, `planning_time_seconds`,
`failure_reason`; `success` is a property. Unreachable paths have `None` for
path/moves/cost and reason `unreachable`. Invalid inputs still raise errors.
The dataclass is frozen, but its path retains the original mutable-list contract.

Expansion means a non-stale node taken from the frontier and processed, including
the goal, not a discovered node. A three-cell corridor requires three expansions;
an already-at-goal search requires one. Start `perf_counter()` before validation;
stop after search and reconstruction, before reporting-only path-cost validation.
Include initial frontier and heuristic preparation; exclude rendering and I/O.
External timings of path wrappers also include report construction.

## CP-02 displays and smoke runner

`evaluation/visualize.py` validates supplied paths. Text uses S/G/B/#/*/., with B
for a shared start/goal. Standalone SVG includes escaped titles, descriptive labels,
route colors, and moves/cost. Weighted text explains configured costs; SVG shows
non-unit costs on non-endpoint cells, where endpoint labels take precedence.

`python -m experiments.run_static --demo` displays the fixed 3×5 detour.
The default runner reads `configs/static_smoke.json`. Strict config keys are
`schema_version`, `purpose`, `grid_sizes`, `obstacle_densities`, `seeds`, and
`algorithms`. Lists must be nonempty with no duplicates; dimensions/seeds valid
integers; probabilities finite in [0,1]; algorithms known. Only static single-agent
unit-cost smoke scenarios are supported.

Default product: 3 sizes × 2 densities × 5 map seeds = 30 scenarios, each shared
across three algorithms. Obstacles use independent Bernoulli draws for non-endpoint
cells in row-major order with `random.Random(seed)`; no reachability filtering.
Actual density divides obstacle count by all cells. Requested probability is
distinct from actual density. Method order follows config order.

Each fresh directory saves exact scenarios, config, source hashes/environment
metadata, CSV, text paths, and one SVG per measurement. `COMPLETE.json` is written
last. Failed/interrupted runs can leave partial directories without this marker;
do not treat them as completed datasets.

CSV v1 field order (`experiments/run_static.py:FIELDS`):

```text
schema_version, run_id, scenario_id, seed, rows, cols, agents, condition,
obstacle_density_requested, obstacle_density_actual, algorithm, success,
failure_reason, moves, path_cost, expanded_nodes, planning_time_seconds, path_json
```

Success is 1/0; missing scalar metrics are empty fields; failed paths are JSON
`null`; successful paths are coordinate arrays. Exact obstacles/endpoints are
in `scenarios.json`, joined by scenario ID. This is not the final training schema.

## Actual CP-02 test additions

`test_reporting.py`: six methods for corridor/singleton expansion counts,
unreachable metadata, old API compatibility, weighted moves versus cost, and
endpoint errors. The first run failed because new APIs did not exist yet.

`test_static_runner.py`: ten methods covering text walls/endpoints/routes,
unreachable and shared endpoints, SVG XML and title escaping, bad-path rejection,
cost displays, seeded maps, invalid configs, matched CSV/scenarios and retained
failures, repeatability without overwrites, and 1×1 scenarios. Integration outputs
use temporary directories. Saved paths are checked against the independent oracle.

Full suite: **31 test methods passed**. The actual smoke run was additionally
audited: 30 scenarios, 90 rows, 90 parseable SVGs, matching source hashes, optimal
costs for all successful routes, and finite nonnegative timing. There were 84
successful rows and 6 unreachable rows; these are smoke counts, not general findings.
See `results/validation/CP-02.md`.

## Algorithms and correctness decisions

BFS uses a FIFO queue and discovers each cell once. Dijkstra uses a priority heap
of accumulated cost. A* uses accumulated cost plus:

`h(position) = Manhattan(position, goal) × minimum traversable destination cost`.

The cost scale is necessary when costs are below one: an unscaled Manhattan
heuristic could overestimate. Every orthogonal move costs at least that minimum,
so this heuristic is a lower bound. On unit-cost grids it is ordinary Manhattan
distance. Dijkstra and A* discard stale heap entries and update parents only for
strict cost improvements. Both check for the goal after taking the best current
entry from the heap. Tuple ordering provides deterministic heap ties.

Path length in moves is `len(path) - 1`; node count is `len(path)`. Weighted
optimality uses `graph.path_cost(path)`, not the number of nodes or moves.

## Actual CP-01 test cases

| Test method | Input and expected evidence |
|---|---|
| `test_open_grid_known_distance` | Empty 5×5 corner-to-corner; 8 valid moves for every method |
| `test_obstacle_detour_known_distance` | 3×5 partial vertical wall; 8 moves instead of 4 |
| `test_unreachable_goal` | Full separating wall; `None` for every method |
| `test_start_equals_goal` | 1×1 free grid; singleton path |
| `test_invalid_endpoints` | Blocked/out-of-bounds starts and goals; `ValueError` |
| `test_weighted_detour` | Direct route costs 31; detour costs 6; Dijkstra/A* take detour; BFS rejects |
| `test_fractional_costs_preserve_astar_optimality` | Four-move route costs 0.4; direct two-move route costs 1.1 |
| `test_non_unit_uniform_costs` | All cells cost 2; BFS/Dijkstra/A* accept and report cost 4 |
| `test_seeded_uniform_maps_against_oracle` | 20 seeds; check validity, reachability, and shortest move count |
| `test_seeded_weighted_maps_against_oracle` | 20 seeds; fractional/integer costs; check minimum total cost |
| `test_invalid_dimensions` | Zero, negative, noninteger, Boolean sizes rejected |
| `test_invalid_obstacles_and_costs` | Out-of-grid cells, blocked costs, zero/negative/nonfinite/nonnumeric/Boolean costs rejected |
| `test_neighbors_are_deterministic_and_orthogonal` | Corners and blocked neighbors; fixed order; invalid source rejected |
| `test_input_data_is_copied` | Mutating caller inputs leaves graph unchanged; cost map is read-only |
| `test_path_cost_contract` | Start cost excluded; singleton zero; empty/diagonal/out-of-bounds paths rejected |

Returned-path validation independently checks bounds, obstacle exclusion, correct
endpoints, Manhattan adjacency of each step, and absence of repeated cells.
The reference solver relaxes all edges in Bellman-Ford style without using either
production heap algorithm. It shares the graph model, so hand-calculated examples
and independent path checks also verify model behavior.

The suite contains 15 methods with additional subcases; it is not 15 research
episodes and not a five-training-seed experiment. It verifies a useful sample of
behavior, not a proof that all possible inputs are correct.

## CP-03 single-agent design

`SingleAgentEnv(graph, start, goal, max_steps=100)` requires a `GridGraph`, free
endpoints, unit movement costs and a positive integer horizon. Public graph,
start, goal, max_steps and position properties are read-only. This is a standalone
standard-library API, not a Gymnasium class.

- `reset(seed=None)` returns `(observation, info)` and clears counters/flags.
- `step(action)` returns `(observation, reward, terminated, truncated, info)`.
- `observe()` returns the current immutable 13-float tuple, even after completion.

Action IDs: UP=0, DOWN=1, LEFT=2, RIGHT=3, WAIT=4. Accept Python integer or Action;
reject Boolean, noninteger and out-of-range values without state changes. Observe
and step require reset. Completed episodes require reset before stepping again.
Seed is None or nonnegative integer, recorded only; fixed maps/transitions have
no stochastic behavior and reset does not alter process-wide random state.

Observation v1 exports `OBSERVATION_FEATURES` in exact order:

| Indices | Features | Encoding |
|---|---|---|
| 0–1 | Current row/column | Divide by max(dimension - 1, 1); [0,1] |
| 2–3 | Goal minus current row/column | Same dimension scale; [-1,1] |
| 4–7 | Adjacent walls: up/down/left/right | 1 for obstacle, else 0 |
| 8–11 | Adjacent boundaries: same order | 1 outside grid; separate from wall |
| 12 | Remaining time | (max_steps - elapsed_steps) / max_steps |

No full map/route is supplied to the model. Local views remain partially
observable; raw-coordinate diagnostics are not additional policy features.
Degenerate dimensions avoid division by zero. Future occupancy features need a
new observation version and compatible newly trained models.

All accepted action encodings consume a tick, including wait/rejected movement.
Boundary and obstacle penalties are exclusive. Executed movement increments
moves and unit path cost; wait/rejected moves do neither. Named reward components
are `step=-1`, `obstacle=-10` on attempt, `boundary=-5` on attempt, and `goal=100`
once on arrival. Reward is their sum; single-agent arrival earns 99. No team or
collision bonus exists. Info/reward dictionaries are fresh copies.

Info includes position/start/goal, seed/feature version, elapsed steps, moves,
path cost, cumulative reward, arrival tick, boundary/obstacle attempts,
terminated/truncated/success, failure reason, event/action name, requested
position, executed-move flag, and latest reward components.

Goal arrival sets terminated and records arrival tick even on the final allowed
turn. Otherwise exhausted horizon sets truncated, success false, failure reason
`time_limit`, arrival None. Start-at-goal reset is terminated success at tick zero,
with zero reward and no allowed steps. Reset clears all counters and flags.

CP-04 uses a finite-horizon objective: goal arrival within this time budget.
Replay stores termination/truncation separately but masks bootstrapping for
either. This differs from a continuing task with an artificial collection cutoff.

## Actual CP-03 evidence

`test_single_agent_env.py` adds 21 methods checking reset requirements/replay,
restart after success or timeout, four moves, wait, wall/boundary scores, single
goal reward, horizon failure, last-tick success, start-at-goal, exact local feature
order, degenerate dimensions, invalid inputs, diagnostic isolation, reward sums,
baseline replay, unreachable maps, waiting versus moves, and 10 seeded action
sequences with occupancy/metric invariants. Full suite: **52 tests passed**.

`experiments/run_episode.py` offers three scripted demonstrations and optional
exclusive-create JSON traces: baseline route takes 8 ticks/8 moves/return 92;
boundary-wall-wait times out at tick 3/0 moves/return -18; start-at-goal takes
zero turns/return zero. Exact trace, reward sums and source hashes were audited.
See `results/validation/CP-03.md`. These are correctness checks, not learning.

## Test-driven workflow for future work

1. Add a behavior-based test with a hand-checkable expected result.
2. Run it and confirm it fails for the intended missing behavior.
3. Implement the smallest correct feature.
4. Run the relevant suite and refactor without changing the contract.
5. Record the exact outcome in the checkpoint files.

CP-01 code and tests were created together and executed successfully. No claim
is made that an initial failing/red run was recorded for this first delivery.

## CP-04 DQN implementation

`algorithms/dqn.py` implements a CPU 13→128→128→5 feed-forward network, two
ReLU hidden layers, online and frozen target networks, Adam, replay, epsilon-greedy
actions, squared Bellman error, and gradient-norm clipping at 10. No action mask,
demonstration paths, reward shaping, or full-map inputs are used by the policy.
Greedy ties select the first maximum action. Target parameters have gradients
disabled; Bellman targets use no-grad. Both episode-ending flags mask bootstrap
for this finite-horizon task. Target copies occur every 500 optimizer updates,
which differs from 500 environment steps.

`Transition` copies and validates two 13-feature observations, action, reward,
and separate terminal/timeout flags. `ReplayBuffer` is a bounded ring list and
samples without replacement with a dedicated seed. Agent initialization uses a
local torch RNG context, and exploration uses its own Python RNG. Evaluation
epsilon zero does not consume exploration randomness. Training uses deterministic
CPU operations and one torch thread; reproducibility is verified on this machine,
not guaranteed across hardware/library versions.

The default config `configs/dqn_fixed.json` freezes a 5×5 unit-cost map with
obstacles (1,1), (1,3), (2,3), (3,1); start (0,0), goal (4,4), horizon 50. The
classical optimum is 8 moves. Seeds 0–4 train independently for 2,000 episodes.
Replay capacity 50,000; batch 64; warm-up 256 environment steps; optimize every
4 environment steps; epsilon decreases linearly from 1.0 to .05 over episode
indices 0–1,200 then stays .05; discount .99; learning rate .001. Greedy checks
are one deterministic rollout before training, every 100 episodes, at the final
weights, and after model reload. The same training map is used: no held-out claim.

`training.train_dqn` creates unique output directories with exact config, source
hashes, dependency/device details, immutable measured CSVs, model weights, final
trajectories, charts, summaries and a last-written completion marker. `--smoke`
explicitly snapshots a one-seed/20-episode override; no defaults silently change.

Per-episode CSV includes seed/episode/epsilon, success/failure, return, executed
moves/cost, elapsed/arrival times, penalties, reward component sums, cumulative
environment/update counts, episode mean loss and training wall time. Per-update
CSV records loss, pre-clip gradient norm, update count, and target sync. Greedy
evaluation CSV separately records episode outcomes, action-only inference time,
episode wall time, actions/positions and static optimum/gap. Failed evaluations
have no arrival time or gap; executed failure moves remain diagnostic counts.

Training wall time is summed over episode loops (including transitions, updates,
and update-log writes), excluding greedy evaluation, initialization, plotting and
model saving. Total run wall time is separate. Inference time sums greedy action
calls, excluding environment stepping. These are development measurements with
single trials, not robust speed benchmarks.

Checkpoint v1 stores online/target weights, architecture/optimizer hyperparameters,
seed/update count, exact observation names/version, actions, and training metadata.
Loading rejects incompatible feature/action layouts, uses CPU and weights-only
loading, and restores predictions/greedy actions. This supports inference, not
exact training resume: optimizer state, replay and RNG state are not saved.

`evaluation.plot_learning` generates PNG and SVG reward/success/MSE charts from
the training CSV, using a trailing window of at most 100 recorded episodes and
separate lines per seed. Success here is exploratory training episode success;
greedy checks are in the separate evaluation CSV. No manually supplied chart
scores. `evaluation.audit_dqn_run` verifies source hashes, reward/counter/epsilon
consistency, finite losses/timings, target synchronization, saved-model rollouts,
and figure file validity. It reads raw outputs and can save a separate audit file.

Dependencies verified locally: PyTorch 2.11.0+cpu (distribution pin 2.11.0), NumPy
1.26.4, Matplotlib 3.10.0; Python 3.12.6. No installation was needed.

`test_dqn.py` adds 11 tests for hand-calculated targets, replay capacity/sampling,
transition validation/copying, epsilon schedule, network outputs/seeds, greedy
and exploratory behavior, online updates/target sync, saved predictions and
overwrite refusal, feature compatibility, and bad configs. `test_training.py`
adds 5 tests for timeout/start-at-goal evaluation, real tiny training logs/plots/
reload, repeatable training preserving prior files, and invalid-config rejection.
Full suite: 68 tests passed. Full-run audit passed for 10,000 training rows,
63,887 optimizer updates and 115 greedy evaluation records. All five final
policies reached the training-map goal, with move counts 12/8/12/8/12 and arrival
ticks 12/9/15/14/14. The exact static optimum is 8 moves. Every reloaded model
reproduced its predictions and final rollout. Reward/success figures were visually
inspected. The 20-episode smoke final policy failed; it remains recorded.
Actual results and a generated seed table are in `results/validation/CP-04.md`.
Matching code/config/tests are archived under `results/validation/CP-04-source/`,
with a hash manifest, because this workspace has no Git history to restore them.

## CP-05 map and schedule design

New modules preserve all CP-04 core files and observation/model v1 compatibility.
`random_maps.build_bank` draws Bernoulli obstacles at probability .15 on 5×5 grids,
protecting corner endpoints. A SHA-256 geometry identity includes dimensions and
sorted walls. The CP-04 training geometry and all previously accepted bank
geometries are excluded, so seed-disjoint partitions are also geometry-disjoint.
Rejected duplicate seeds are recorded; reachability is never a rejection reason.
Unique-geometry conditioning changes the raw Bernoulli distribution and is disclosed.

Frozen config: 100 train maps from candidate seeds 1000–1999, 10 validation maps
from 2000–2999, 50 test maps from 3000–3999. Search each range until enough unique
maps are found; insufficient diversity or overlapping used seed ranges fails
explicitly. Endpoints remain (0,0) and (4,4); horizon 50. Initially unreachable
maps are retained and marked. No varying starts/goals or larger grids at this gate.

`DynamicSingleAgentEnv` applies scheduled changes before an action's observation.
Reset prepares tick 1; each nonfinal step prepares the next action's graph before
returning its observation. Repeated observe calls are idempotent. Thus returned
info can include changes for the upcoming tick. `action_graph_version` identifies
the graph actually used for movement, while `graph_version` identifies the returned
observation snapshot. Goal/timeout completion stops future events. Reset restores
the initial map and clears history. Each changed graph is a new immutable snapshot.

Schedules accept add/remove only, protect start/goal, validate bounds/horizon,
and forbid conflicting same-cell/same-tick events. An occupied-cell addition is
rejected and logged, not silently moved elsewhere. No-op changes are logged.
Default comparison schedule adds a free cell on the initial BFS path at tick 3,
then removes it at tick 8. Choose a cell with start Manhattan distance >=3:
no method can occupy it after only two preceding actions. For unreachable maps,
use a distant free cell instead. All methods therefore receive identical realized
events; replay audit verifies this. A BFS-path event need not block another
method's selected route, so these cases are not guaranteed hard adaptation tests.

`SearchController` caches routes and replans from its current position after graph
version changes, allowing wait when no route exists. Frozen A* computes once on
the initial map and retries a blocked next edge without advancing its route index;
it can resume when that edge reopens. Frozen A* is a separately labeled control.
Planning seconds and non-stale expanded nodes accumulate across all plan calls.

`navigation.rollout` gives every controller the same reset/step contract. DQN
uses only 13 local features; classical search sees the current entire graph.
This information difference is a stated experimental condition, not a matched
information claim. No online updates or exploration during evaluation.

## CP-05 training and evaluation protocol

`train_varied` independently trains seeds 0–4 for 2,000 static random-map episodes
each. Map selection uses a dedicated RNG at seed+20000, replay at seed+10000.
Architecture, rewards, horizon, epsilon, optimizer, target-copy and replay settings
match CP-04. Every episode's map ID/seed is logged. Validation uses all 10 distinct
validation maps every 100 episodes; final weights are kept without best-model
selection or tuning from these checks. Test maps never enter replay or gradients.
Dynamic evaluation is transfer from static training, not dynamic training.

`run_transfer` first evaluates fixed CP-04 models and corresponding untrained
controls, then evaluates those same policies alongside final varied-map models.
One static and one dynamic episode per held-out map/model are recorded. Classical
BFS/Dijkstra/A* replanning and frozen A* add four methods per map/condition.
Five model seeds give 14 methods before varied models and 19 afterward: 1,400 and
1,900 episodes respectively. All use identical bank geometries and schedules.

Raw CSV includes model/map identity, reachability, status/failure, elapsed/arrival
ticks, executed moves/cost, reward and attempts, initial static optimum, static
gap when defined, decision/episode/inference/planning times, expansions/plan calls,
and applied/rejected event counts. Dynamic optimum gaps remain missing: a static
reference is not a dynamic optimum. Failed episodes keep executed moves as
diagnostics, with missing arrival/gap. JSONL stores observations, actions, rewards,
positions, graph versions and final histories for replay. Model paths/hashes,
configs, banks and matching source snapshots accompany each unique run.

The summary generator uses all maps as the success denominator, with a reachable
subset rate separately in raw-run summaries. Successful-only move/arrival averages
are accompanied by success counts. DQN seed standard deviations describe model
variability; repeated maps across policies are not independent experiments.
No hypothesis test, general speed claim, or global dynamic optimality claim here.

`audit_varied` checks split fingerprints and initial BFS reachability, source
snapshot hashes, seeded training-map choices, reward/update/epsilon counters,
target-copy flags, model reload validation routes, and every held-out action and
observation by replay. Model digests and identical realized schedules are verified.
Generated comparisons and PNG/SVG success bars come from recorded CSV only.

Tests: seven map/schedule tests, four replanning/control tests, three tiny random-
training/evaluation integration tests. Total **82 tests passed in 8.731s**, exit 0.
The five-seed run saved 10,000 episodes and 74,961 optimizer updates. Final
validation successes were 9/10, 9/10, 9/10, 9/10 and 10/10. Training and the
1,900-episode final held-out comparison passed their replay audits. See
[CP-05 evidence](results/validation/CP-05.md) for generated measured comparisons.

## Checkpoint test requirements and remaining work

| Area | Tests before checkpoint completion |
|---|---|
| Baseline metadata | Completed at CP-02: known counts, timing nonnegative, original API preserved |
| Single-agent environment | Complete at CP-03: reset, actions, scores, local features, goal and horizon rules |
| DQN | Implemented/tested at CP-04: replay, targets, schedule, actions, reload, tiny pipeline |
| Dynamics | Complete at CP-05: schedules/reset/rejections, replanning controls, split isolation, training and held-out replay audits |
| Joint resolver | Completed at CP-06a: vertex/swap/cascade/goal/following rules; 625 joint choices preserve occupancy |
| Prioritized planning | Completed at CP-06a: waits, vertex/edge/goal reservations, priority/horizon failure and replay |
| Evaluation | Same scenario IDs across methods; timeout counts as failure; arrival times and moves differ when waiting; training time excluded from inference |
| Analysis | Known tiny CSV produces expected aggregates; no manual numbers; undefined gaps and empty success sets handled |

## Future training and evaluation design

### CP-06c implemented dynamic-team decisions

Extend teams through a separate environment module; preserve observation v2,
rewards and all static CP-06b artifacts. Events prepare the next action's graph
before observations, using immutable snapshots, idempotent observe, reset history,
occupied-add rejection and protection of every team start/goal. Diagnostics
distinguish returned observation graph version from last movement graph version.
Stop future events after team termination or truncation.

Evaluate final CP-06b models without training on their existing 20 test geometries,
two/four agents, static/dynamic pairs, three replanning methods and three frozen
controls plus five seeds each of solo/shared/untrained policies: 1,680 episodes.
Default add at tick 2, remove at tick 8. Choose a free non-endpoint cell at Manhattan
distance >=2 from all four initial starts, preferring an initial independent BFS
route interior; otherwise a free cell in row order. Use the same cell for two/four
agents and all methods. If none exists, explicitly log an empty schedule.
No agent can occupy the chosen cell after just one preceding action. Thus event
statuses agree whenever episodes are still active; shorter episodes legitimately
stop before later events. Audits compare shared active prefixes, not pretend
every completed episode experienced the entire schedule. Perturbations are not
guaranteed to affect every selected route.

Replanners search the current graph from current joint positions after graph
version changes, preserving arrived agents' occupied goals and remaining horizon.
They do not know future events. If no complete plan exists, all agents wait until
a graph change permits another attempt; record each planning failure. Execution
deviation also triggers replanning. Frozen controls plan once on the initial map,
then independently retry each agent's next route edge; waits consume route entries,
blocked moves do not. Delays invalidate original reservations, so the simulator
still rejects resulting conflicts. Initial planning failure waits to timeout.
This differs from CP-06b's immediate planning-failure return; log the distinction
and retain the earlier data unchanged. Dynamic team optimality is not computed.

`DynamicTeamEnv` replaces only the current graph snapshot. Reset restores the
initial graph; observe prepares elapsed+1 once; completed episodes stop preparation.
Returned info carries `graph_version`, `action_graph_version`, `prepared_tick` and
copied event history. The base simultaneous resolver, arrival ticks and reward
components are reused. Invalid joint actions/seeds do not alter diagnostics.

`TeamController` accumulates planning calls with current positions, elapsed tick,
remaining horizon, success/failure, expanded nodes and measured seconds. Cached
plans track expected next positions. Graph changes or execution deviation cause
current-map replanning; absorbed goals are preserved by the existing reservation
planner. Frozen controls have one planning call and per-agent route cursors.
Planning time is separate from action selection; no inference-time training.

The runner saves the exact CP-06b bank/training config, dynamic profile, schedules,
model paths/hashes, matching sources, CSV and full trajectory JSONL. Each row records
scheduled/seen/applied/rejected events, plan calls/failures, and standard team
metrics. Empty schedules and early completion exposure are explicit. In-memory
weights/update counters are checked unchanged before writing completion. Auditor
reproduces every final-policy/controller decision and planning outcome, compares
all observations/rewards/positions/diagnostics and checks each CSV projection.

Twelve new checks pass; full **123 tests passed in 18.992s**. Smoke audit: 168
episodes/2,281 steps. Full audit: 1,680 episodes/32,194 steps, 20 maps, no empty
schedules, identical active event prefixes, unchanged policy weights/digests and
zero actual collisions. A separate regression confirms 720 static metric rows
match CP-06b; the original QENN file SHA-256 is unchanged. Dynamic shared success
two/four is 58%/25%, solo 61%/28%, main replanners 90%/80%. Frozen four-agent
success falls to 65% (A*) or 70% (BFS/Dijkstra); no generalized claim follows.
See [CP-06c evidence](results/validation/CP-06c.md) and generated measured tables.

### CP-06b implemented frozen learning decisions

DQN accepts explicit observation versions 1 (13) and 2 (17); legacy construction
defaults to v1. Transitions carry a version and mixed layouts are rejected by
training. Checkpoints retain exact feature names/version, with legacy loads intact.
Team replay includes every agent at every tick. Own arrival does not end its
transition: arrived agents issue forced WAIT and continue zero-reward transitions
until the team's one-time bonus or timeout. Mask bootstrap only on team termination
or finite-horizon truncation. All environment rewards enter replay unchanged.

Static development: 5×5, wall probability .10, horizon 30; unique banks of 50 train,
10 validation and 20 test geometries exclude all CP-05 banks and CP-04's fixed map.
Each map has eight seeded distinct free endpoints; two-agent routes are a subset
of four-agent routes. Unreachable tasks remain. Five seeds and 1,000 training
cycles per method are fixed before runs. Shared learns one two-agent episode per
cycle; control learns the same two routes separately, so both face 2,000 navigation
tasks per seed. Actual transitions, ticks and optimizer updates can differ and
must be reported. A common replay counter triggers one update per eight inserted
transitions after 256 warm-up transitions; batch 64. Epsilon decays by cycle over
600 cycles from 1 to .05. Other architecture/optimizer settings match CP-05.
Validation at cycles 0/250/500/750/1000; keep final weights without selection.
No training on four-agent teams or held-out maps. Test both policies greedily on
the same two/four-agent scenarios against prioritized BFS/Dijkstra/A* and untrained
v2 controls. This is static scaling transfer, not dynamic multi-agent evaluation.

`DQNAgent(observation_version=2)` creates a 17-input model; omitted versions
still create 13-input models. `Transition.observation_version` defaults to 1.
`train_batch` rejects a mixed layout before optimizer changes. Checkpoint format
version stays 1, with exact observation names/version selecting input dimensions.
This extends supported layouts without silently padding or converting old weights.

`evaluation.team_protocol` uses endpoint RNG map_seed+70000, eight distinct free
cells sampled in row order. Training-map selection uses seed+20000 independently
for each mode, exploration uses seed, replay uses seed+10000. Training logs cycle,
route, map identity, epsilon, steps, tasks, transitions, updates, rewards and timing.
`training_actions.jsonl` saves every joint action and final diagnostics; an auditor
replays them to check rewards/counters/episode endings. No historical model
snapshots are saved during training: intermediate validation actions are replayed
for environment consistency, while only final validation decisions can be checked
against their saved weights. Final models are greedy-reloaded before completion.

`run_team_comparison` evaluates final solo/shared and seeded untrained policies on
20 maps each with two and four agents. Three prioritized planners add 120 cases;
15 learned/untrained policies add 600, for 720 total. Planner failure has no
executed episode, empty makespan/arrival/elapsed fields, zero executed moves and
attempts, and explicit `planning_failure`. Failed DQN episodes keep executed
moves/attempts but missing makespan and sum of arrivals. Both failure types remain
in success denominators. No global team optimality gap is claimed. CSV separates
decision/inference/planning/episode times and source/model digests. Audits verify
every test decision against its final policy or planner, replay all observations,
rewards/positions/diagnostics, and verify row-to-scenario uniqueness.

Generated success bars and successful-only makespan/move tables use raw CSV.
Training return curves show recorded environment return per assigned task with
separate solo/shared panels and a trailing 100-cycle mean. Solo team bonuses
arrive after each independent trip; shared team bonuses wait for both agents.
These different reward timings and realized update budgets must be disclosed.

Eight new learning/aggregation tests pass; full **111 tests passed in 5.903s**.
Smoke/full runs and evaluations passed audits. Full outputs: 15,000 training
episodes, 25,084 updates, 50 validation records, ten final models and 720 held-out
episodes. Five historical v1 models still reproduce complete action/observation/
position traces. Shared success two/four: 61%/25%; solo: 64%/27%; planners:
90%/80%. This development bank does not support improved shared-policy success.
Generated tables/plots and detailed limits: [CP-06b evidence](results/validation/CP-06b.md).

### CP-06a implemented foundation contract

This iteration implements static unit-cost teams and reservation planners before
shared learning. `MultiAgentEnv.reset` returns a tuple of per-agent observations
and independent diagnostics. `step` validates the entire joint action first and
returns observations, per-agent rewards, team termination/truncation and info.
Starts and goals must each be unique free cells. Arrived agents stay at goals.
Observation v2 is the existing 13 features plus four adjacent other-agent
occupancy flags (up/down/left/right); old v1 model weights are incompatible.

Proposals are simultaneous. Reject moving proposals sharing a destination and
opposite edge swaps; then repeatedly reject movement into cells whose occupants
now stay. Legal following and cycles longer than two remain allowed. Only active
agents attempting rejected movement receive a conflict penalty. Record unique
vertex pairs, swap pairs, rejected-agent counts and actual collisions separately.
Finished agents have no step penalty; the one-time team completion bonus reaches
all agents, including those finished earlier. Reset-at-goal gives no free bonuses.

Prioritized planning searches (cell,tick) with wait edges, unit turn cost, reserved
vertices and opposite edges. Each arrived higher-priority agent reserves its goal
through the horizon; a new arrival must be safe for that whole remaining interval.
Already-at-goal agents are reserved before any search regardless of priority.
BFS/Dijkstra/A* minimize arrival turns, not movement-only cost. Priority defaults
to agent index; failure returns no executable joint plan and retains diagnostics.
Static plans are not a dynamic multi-agent replanning implementation.

`algorithms.prioritized.prioritized_plan` returns immutable `TeamPlan`: executable
paths only when all agents have paths, partial diagnostic paths on failure,
priority order, failed agent/reason, expanded states and planning seconds.
BFS uses a FIFO deque; Dijkstra/A* use stable heaps. Every edge including wait
costs one turn; A* uses Manhattan distance. Goal states unsafe for later reserved
ticks are discarded, not allowed to leave their own absorbing goal.

`MultiAgentEnv` observations and rewards are agent-indexed tuples. Team done
flags are booleans, with per-agent arrival ticks in fresh diagnostics. All joint
actions are validated before counters change. Finished agents ignore valid moves.
Conflict attempts count rejected moving agents per tick; vertex/swap counts are
unique agent-pair events per tick, including newly blocked pairs during cascades.
Waiting/finished occupants are not penalized for another agent approaching them.
Actual collision count is checked from final occupancy/edges separately.

Eleven environment tests include all 625 joint actions for four agents on 2×2;
eight planner tests include waits, swaps, permanent goals, horizon failures,
single-agent optimality across 16 obstacle patterns and priority sensitivity.
Two trace tests reproduce saved episodes and detect reward/failure tampering.
Full **103 tests passed in 4.551s**. The 16-case correctness artifact includes
nine successes, six planning failures and one timeout; all 26 steps replayed.
No team learning or final experiment inference is claimed. See
[CP-06a evidence](results/validation/CP-06a.md).

Shared DQN input: fixed local feature vector per agent; output: five Q-values.
Implemented finite-horizon target: `reward + gamma * (1 - done) * max(target_Q(next_obs))`,
where `done = terminated or truncated`.
Train the online network using replay mini-batches and a periodically copied
target network. Single-agent DQN is implemented at CP-04; shared multi-agent
training is implemented at CP-06b and dynamic team transfer at CP-06c. Larger
final experiment configuration and final blind scenarios are next.

Future per-episode raw schema should include run ID, config/model identity,
training/map/schedule seeds, scenario ID, algorithm, size, agents, density,
condition, horizon, success, failure reason, per-agent arrival ticks, total moves,
path cost, makespan, vertex/swap attempts, actual collisions, planning/inference/
episode times, expansions, and model checkpoint. Store training episode rewards
and named reward components separately. Use explicit missing values for metrics
that do not apply. Freeze the schema before final experiment collection.

## CP-07a frozen protocol interfaces

`evaluation/final_protocol.py` validates the accepted JSON, loads final v2 model
contracts, captures recorded development geometry/source exclusions, generates
pilot/final cases deterministically and defines metric applicability. Geometry
identity ignores endpoints, costs and seeds. Wall sampling includes all cells;
endpoint sampling follows wall sampling. Log geometry/free-cell/boundary-endpoint
rejections but retain unreachable tasks. Nested 1/2/4-agent endpoint subsets and
the same safe schedule match conditions. Independent distances and route-overlap
pair counts are initial descriptive references, not global team optima.

`freeze` writes an exclusive new directory containing immutable exclusion and
manifest JSONs. Seal the config, implementation, models and development inputs;
exclude pilot geometry and do not create final geometry. `check_freeze` rejects
changed source/config/model/exclusion hashes before creating a final run.

`experiments/run_final.py` saves existing CP-06c fields plus size, requested/
realized density, endpoint arrangement, horizon, initial reachability/lower bound,
route overlap, static single-agent gap and missing-value reason, addition
exposure and successful post-addition completion steps. Missing fields remain
blank in CSV and null in JSON. The finite-horizon reward/collision/environment
interfaces are unchanged. The pilot uses one rollout; final uses three fresh
rollouts with identical non-time outcomes and retains only repeat-zero outcomes
for research sample counts. Store all timer repetitions alongside the first trace.
Clone/check model parameters and optimizer-update counters after evaluation.

`evaluation/audit_final.py` regenerates the bank, verifies archived source/model
digests and coverage, re-executes all recorded policy/planner decisions, and checks
observations, rewards, diagnostics, plans, projections and shared active-event
prefixes. Canonicalize tuple/list JSON serialization before comparing histories.
Do not compare elapsed timers across executions; check saved timers finite and
nonnegative, plan-time sums, repetition counts and repeat-zero projections.

`evaluation/summarize_final.py` groups by every scientific condition and method;
success denominators include failures. Path means use successes, zero successes
give null means. Seed variability is sample standard deviation of rates from
five models on shared maps. Matched shared/solo and replanned/frozen contrasts
require identical case keys and disclose jointly successful subsets. Timing
repetitions are summarized per case and never counted as extra episodes.
Final figures and more detailed hypothesis analysis remain CP-07b deliverables.

`test_final_protocol.py` covers 12-stratum pilot reproducibility/separation,
endpoint rules, safe events for nested teams, exact and undefined gap arithmetic,
post-addition failure censoring, denominator/seed-variance arithmetic, matching,
seal/tamper behavior and invalid-run rejection. Its three-repeat integration
uses one pilot geometry and a test-double seal, avoiding final case generation;
real seal checks are tested separately. It audits actual saved model rollouts
and rejects a negative saved repeated timer.
Ten protocol tests and the full 133-test suite passed. Complete twelve-stratum
pilot replay passed: 1,512 episodes/63,386 steps, zero actual collisions/empty
schedules. Generated denominator/missing-value checks and all sealed hashes
passed; 280 development/pilot geometries are excluded. See
[CP-07a evidence](results/validation/CP-07a.md). Final geometries are not generated.

## CP-07b/CP-08 analysis and manuscript tools (completed)

New analysis modules are added without changing any CP-07a sealed source.
`evaluation/research_analysis.py` requires a completed final run and successful
final replay evidence, then computes success-conditioned summaries, seed rates/
sample standard deviations, full-stratum tables, repeated timer means and
matched H1/H2/H3/H4 contrasts. Learned/classical comparisons reuse one reference
per scenario; they do not manufacture classical training seeds. H2 requires both
cases exposed and reports success separately from jointly successful completion.
H3 matches nested endpoint sets; H4 retains each of 72 detailed strata. Seven
figures are generated with Matplotlib as PNG/SVG/PDF, including the workflow and
historical CP-06b training curves. Raw logs are never changed by analysis.

`evaluation/check_research_outputs.py` independently checks final geometry/
case counts, exclusion/seal hashes, initially unreachable failures, missing
metrics, exact static single-agent gaps, summary denominators/means, paired
seed differences and provenance hashes. Correctness outputs remain separate.

CP-08 sources: `paper/references.json` and `literature_review.md` record nine
primary verified records and bibliographic caveats. `methods_source.md` describes
actual code/protocol. `build_manuscript.py` generates complete Markdown/LaTeX,
all result tables and a measured-claim/provenance record from audited analysis.
`render_manuscript.py` uses installed ReportLab 4.4.10 for a readable PDF;
no local TeX engine is present, so no compiled-LaTeX claim is made.
`check_manuscript.py` checks sections, numeric claim/table hashes, references,
figure paths, original Word fingerprint and PDF text/bounds, then uses installed
pypdfium2 to rasterize all pages for visual inspection. pdfplumber 0.11.10 and
pypdfium2 5.10.1 are pinned. Word reference formatting remains CP-09.
Four analysis and two manuscript-tool tests passed. The final 139-test suite
passed after fixing bold captions containing A* and adding a real PDF regression.
Final collection has 15,120 unique episodes/45,360 timed rollouts; all 652,244
first-trajectory steps replayed, and 837 groups were independently checked.
The generated paper includes nine result tables; exact static single-agent gaps
have a separate table and unsuccessful gaps remain missing. Seven figures were
inspected. All 17 PDF pages were rasterized, checked for text bounds and reviewed
through an all-page overview and critical full-size pages. Author metadata is
explicitly confirmed as Madhav Joshi, Marwadi University. See CP-07b/08 evidence
for exact commands and provenance. Scientific self-review is complete; Word
reference-format validation and external peer review are separate matters.

## CP-09 Word manuscript design and acceptance checks

Input: reviewed CP-08 manuscript, audited CP-07b final outputs, verified bibliography
and read-only `QENN_Research_Paper_Madhav_Joshi (1).docx` formatting reference.
Output: separate `paper/Graph_Search_Research_Paper.docx` plus a manuscript
provenance/validation record. Never overwrite the reference or manually change
measured table values. Generate final tables/figures from final analysis artifacts.

Reference inspection verified A4 (11906×16838 twips), margins top/bottom1008 and
left/right864 twips, single-column opening followed by two columns with 440-twip
gap, Times New Roman defaults, abstract/index terms, Roman-numbered main headings,
lettered subsections, numbered equations and figure/table captions. Most paragraphs
use direct formatting rather than named styles. At CP-09 inspect precise title,
body, caption and reference run sizes/spacing, along with headers/footers/tables,
before implementing a repeatable formatting generator. Keep scientific section
content aligned with the graph-search outline rather than copying quantum text.

Checks: inspect DOCX XML/text for complete required sections, tables/images,
equations/citation links and absence of placeholders/old quantum content. Verify
every reported result against audited final artifacts, bibliography against
verified primary sources, and source DOCX fingerprint unchanged. Render/review all
pages for column flow, caption readability, clipping and missing content; any
unavailable rendering check remains explicitly unresolved. CP-09 is complete
only after the separate full document and its required checks are delivered.
