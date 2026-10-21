# CP-06b: static team DQN validation

Date: 2026-10-07 local | Python 3.12.6 | Windows CPU
Raw directory timestamps are UTC (October 6 UTC).

## Commands actually executed

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

Legacy unit/pipeline tests: 16 passed in 3.845s. Eight new learning tests passed
in 2.784s. Full **111 tests passed in 5.903s**, exit 0. All listed run/audit/
analysis commands exited 0. No packages installed. CPU with one torch thread and
deterministic operations; versions recorded in each metadata file and requirements.

New tests check v2 predictions/checkpoints, unchanged v1 defaults, mixed-layout
rejection without updates, hand-calculated delayed team rewards, team timeout
masking, split/endpoint generation, real tiny training/evaluation with audits,
tampered action-log rejection, invalid config before output, and successful-only
aggregation with failure denominators and empty success sets.

An initial inline legacy probe imported the wrong function name (`evaluate`) and
failed before running; corrected to `evaluate_agent`. Five real CP-04 models then
reproduced all saved success/move/arrival metrics and every action/observation/
position in historical trajectories. See [legacy metrics](CP-06b-legacy-reload.json)
and [complete trace check](CP-06b-legacy-trajectories.json). No old raw outputs were
changed. Earlier source snapshots remain usable for their historical auditors.

## Actual saved runs and audits

- [Smoke training](../raw/dqn_team/20261006T193747713350Z_ac14d9ba/) and [audit](CP-06b-smoke-training-audit.json): 60 episodes, 178 updates, six validation records. Final validation solo 1/10, shared 0/10; failures retained.
- [Smoke evaluation](../raw/team_comparison/20261006T193809921031Z_cb313279/) and [audit](CP-06b-smoke-evaluation-audit.json): 240 episodes, every decision replayed.
- [Full training](../raw/dqn_team/20261006T193829020826Z_42837111/) and [audit](CP-06b-training-audit.json): 15,000 episodes, 25,084 updates, 50 validation records, ten final models, 20,000 assigned agent tasks.
- [Full evaluation](../raw/team_comparison/20261006T194208884293Z_69d05e81/) and [audit](CP-06b-evaluation-audit.json): 720 episodes, source/model digests and all final decisions replayed, zero actual collisions.
- [Generated comparison](../analysis/CP-06b/comparison.md), [success PNG](../analysis/CP-06b/success_comparison.png) and [training-return PNG](../analysis/CP-06b/training_returns.png). Both PNGs visually inspected; SVG counterparts also saved.
- [Matching core/config/test archive](CP-06b-source/manifest.json); each raw run also includes all producer sources and hashes.

Correctness evidence is separate from research CSV; previous raw files and the
unrelated QENN Word document were not edited. Source snapshots preserve the
version that made each run. Final weights support inference, not exact resume.

## Frozen protocol

Static 5×5 unit-cost boards, .10 obstacle probability, horizon 30. Each map uses
eight seeded distinct free endpoints; two-agent tasks are a subset of four-agent
tasks. Banks contain 50 train/10 validation/20 test unique geometries, excluding
CP-04's fixed board and all CP-05 banks. Forty-five duplicate candidates rejected;
unique/excluded geometry conditioning changes the initial Bernoulli distribution.
Initially individually unreachable two-agent scenario counts: 0/1/2; four-agent
counts: 2/1/2. No reachability filtering. Four-agent training never occurs.

Five seeds for each mode, 1,000 cycles, two assigned tasks per cycle. Shared trains
one two-agent episode; solo trains the same two routes separately using the same
v2 inputs with zero neighboring occupancy. Replay/architecture settings are frozen
in config. All agents remain in replay until team end, with forced WAIT after own
arrival. Thus the later team bonus is kept in learning. Both team termination and
finite-horizon truncation mask bootstrap; own arrival alone does not.

Validation monitors progress at 0/250/500/750/1000 cycles. Final weights retained,
with no selection or retuning based on test maps. Exact endpoint/map/replay/
exploration seeds, sources, versions and counters saved. Training audit replays
every training action and intermediate validation environment step, verifies map
choices/rewards/epsilon/update counters and final greedy reloads. Intermediate
policy weights are not archived; historical greedy optimality of their choices
is not an audit claim. Final held-out decisions are reproduced from final weights.

## Interpretation and remaining work

Shared success is lower than solo control here (two agents 61% vs 64%, four 25%
vs 27%). Shared mean rejected-agent attempts are lower (3.42/27.28 vs 5.11/32.58),
but that does not establish better goal completion. Classical planners reached
90%/80%. Successful-only path/makespan averages use different successful subsets:
do not infer DQN path superiority from them. Zero actual collisions are guaranteed
by the referee, not evidence of learned collision avoidance. Four-agent planners
have four failed cases per method, including two with individually unreachable
routes; planner priority/horizon can cause additional failure in reachable cases.

Budgets match assigned tasks, not realized transitions or optimizer updates.
Solo bonuses arrive at each route completion; shared bonuses wait for the team.
Control sees new occupancy inputs at team deployment; DQN local views differ from
planners' full maps. Twenty held-out maps are reused by five model seeds, not 100
independent maps. Seed variation is descriptive, not statistical significance.
No dynamic team conclusions, speed benchmark, globally optimal team gaps or
completed paper claims. CP-06c adds changing obstacles and team replanning before
larger frozen experiments. Keep this run and its unsuccessful results intact.

Final inline Python verification exited 0: generated tables directly from saved
summaries, archived 17 matching files with SHA-256 manifest, counted 111 actual
test definitions and verified all local links across 15 Markdown documents.

## Generated measured tables

The following tables are populated directly from saved summaries and raw CSV.

| Mode | Seed | Episodes | Assigned tasks | Transitions | Updates | Final two-agent validation | Training seconds |
|---|---|---|---|---|---|---|---|
| solo | 0 | 2000 | 2000 | 16447 | 2024 | 7/10 | 9.899 |
| solo | 1 | 2000 | 2000 | 16276 | 2003 | 7/10 | 10.013 |
| solo | 2 | 2000 | 2000 | 16035 | 1973 | 7/10 | 10.325 |
| solo | 3 | 2000 | 2000 | 16505 | 2032 | 7/10 | 10.198 |
| solo | 4 | 2000 | 2000 | 16507 | 2032 | 8/10 | 11.677 |
| shared | 0 | 1000 | 2000 | 23488 | 2905 | 6/10 | 18.324 |
| shared | 1 | 1000 | 2000 | 23480 | 2904 | 6/10 | 15.752 |
| shared | 2 | 1000 | 2000 | 26010 | 3220 | 7/10 | 16.305 |
| shared | 3 | 1000 | 2000 | 24336 | 3011 | 6/10 | 18.251 |
| shared | 4 | 1000 | 2000 | 24094 | 2980 | 7/10 | 11.955 |

| Mode | Total tasks | Transitions | Updates |
|---|---|---|---|
| solo | 10000 | 81770 | 10064 |
| shared | 10000 | 121408 | 15020 |

### Held-out outcomes

Generated from raw CSV. All maps and planning/time-limit failures are included in success denominators. Makespan/moves means include successes only. Seed std describes variation across five models, not independent map uncertainty. Attempts are rejected agents per tick; actual collisions are checked separately.

| Method | Agents | Successes / episodes | Success rate | Seed std | Successful makespan | Successful moves | Mean attempts | Planning failures | Actual collisions |
|---|---|---|---|---|---|---|---|---|---|
| astar | 2 | 18 / 20 | 90.0% | n/a | 4.389 | 7.167 | 0.000 | 2 | 0 |
| astar | 4 | 16 / 20 | 80.0% | n/a | 6.125 | 15.438 | 0.000 | 4 | 0 |
| bfs | 2 | 18 / 20 | 90.0% | n/a | 4.389 | 7.167 | 0.000 | 2 | 0 |
| bfs | 4 | 16 / 20 | 80.0% | n/a | 6.125 | 15.312 | 0.000 | 4 | 0 |
| dijkstra | 2 | 18 / 20 | 90.0% | n/a | 4.389 | 7.167 | 0.000 | 2 | 0 |
| dijkstra | 4 | 16 / 20 | 80.0% | n/a | 6.125 | 15.312 | 0.000 | 4 | 0 |
| shared | 2 | 61 / 100 | 61.0% | 0.065 | 3.836 | 5.934 | 3.420 | 0 | 0 |
| shared | 4 | 25 / 100 | 25.0% | 0.035 | 6.760 | 12.680 | 27.280 | 0 | 0 |
| solo | 2 | 64 / 100 | 64.0% | 0.042 | 3.719 | 5.875 | 5.110 | 0 | 0 |
| solo | 4 | 27 / 100 | 27.0% | 0.027 | 5.148 | 12.630 | 32.580 | 0 | 0 |
| untrained | 2 | 1 / 100 | 1.0% | 0.022 | 1.000 | 2.000 | 0.740 | 0 | 0 |
| untrained | 4 | 0 / 100 | 0.0% | 0.000 | n/a | n/a | 13.800 | 0 | 0 |
