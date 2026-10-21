# CP-06c: dynamic team transfer validation

Date: 2026-10-07 local | Python 3.12.6 | Windows CPU
Raw directory timestamps use UTC (October 6 UTC).

## Commands actually executed

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

Ten new unit tests passed in .010s; combined 12 checks passed in 8.420s.
Full **123 tests passed in 18.992s**, exit 0. All listed run/audit/analysis commands
exited 0. Installed CPU stack reused; no dependency installation or new training.
Tests verify observation/event timing and versions, idempotence/reset, copied
histories, occupied/no-op/protected/invalid events, atomic actions/seeds, early
termination/timeout, four-agent cascades, default/empty schedules, preserved
arrivals/remaining horizons, replanning detours, failed-plan recovery, a real
saved-policy pipeline and detection of changed records.

## Saved artifacts and audit findings

- [Smoke run](../raw/dynamic_team/20261006T201334953675Z_257e7353/) and [audit](CP-06c-smoke-audit.json): 168 episodes, 2,281 replayed steps, two maps.
- [Full run](../raw/dynamic_team/20261006T201424719291Z_678fc290/) and [audit](CP-06c-audit.json): 1,680 episodes, 32,194 replayed steps, 20 maps.
- [Static regression and QENN fingerprint](CP-06c-regression.json).
- [Generated table](../analysis/CP-06c/comparison.md), [success PNG](../analysis/CP-06c/success_comparison.png) and [SVG](../analysis/CP-06c/success_comparison.svg). PNG visually inspected.
- [Matching source/config/test archive](CP-06c-source/manifest.json); each raw run also contains complete producer source copies and digests.

All decisions were reproduced using saved final models or the corresponding
current-map/frozen controller. Planning calls/outcomes, graph versions, observations,
rewards/components, positions, arrivals, counters and CSV projections replayed.
Model digests and source copies match. Active event prefixes are identical across
methods and agent-count slices. No empty schedules occurred in these 20 maps.
The producer verifies in-memory model weights/update counters unchanged before
writing completion. Zero actual collisions; attempted conflicts remain in data.

Inline Python compared 720 corresponding static rows with CP-06b: success,
makespan, executed moves/cost, rejected attempts and actual collisions all match.
Failure-time/reward semantics are deliberately different: CP-06c waits through
failed plans rather than immediately stopping before execution. Do not substitute
one checkpoint's failure rewards/ticks for the other's.

QENN SHA-256 before and after this iteration:
`0EB7C34B6358DA752B52C38FD9AF9DAEAD8469C2DF2216DF1C272F07C47392F8`.
It was not edited. No CP-04/05/06b model or measured result was rewritten.

## Frozen dynamic protocol

Use the completed CP-06b bank/models without training or tuning. Twenty 5×5
unit-cost .10-density maps, horizon 30, two/four agents, static/dynamic pairs.
Three replanners plus three frozen controls and 15 solo/shared/untrained policies
give 21 methods per scenario and 1,680 episodes. These geometries were previously
evaluated development cases; they are held out from training, not a fresh final
blind test. Five policy seeds reuse the same 20 maps.

Add a wall before tick 2 and remove it before tick 8. Choose a free square not
among any of the eight endpoints, at Manhattan distance >=2 from all four starts;
prefer an independent initial BFS route interior, then row-order free cells.
This prevents any policy occupying it after just one preceding action. If no
cell qualifies, record an empty schedule. No reachable-route filtering.

Changes prepare before action observations, update immutable graph snapshots,
and distinguish movement versus next-observation versions. Every reset restores
the initial board/history. Occupied additions are rejected and logged in custom
tests. Early team completion stops future events: compare shared active event
prefixes, not all scheduled events as if every team remained active. The output
records scheduled/seen/applied/rejected counts, making exposure differences clear.

Replanners see only the current full graph, not future schedules. Replan from
current joint positions after a graph change or execution deviation, preserving
arrived agents and remaining horizon. Failed full plans issue WAIT until another
graph change. Frozen controls plan once on the initial map and independently
retry each blocked edge; waits consume path entries. Delays can invalidate their
old space-time reservations, so the common resolver still prevents collisions.
DQN reads its unchanged local v2 observations, with exploration/learning disabled.

## Interpretation and next step

Dynamic replanners each reach 18/20 two-agent and 16/20 four-agent goals (90%/80%).
Frozen four-agent controls reach 13/20 for A* or 14/20 for BFS/Dijkstra (65%/70%).
Shared DQN reaches 58/100 and 25/100; solo control 61/100 and 28/100. No DQN
success superiority or general adaptation advantage is supported here. Route
changes and waiting can improve individual cases without establishing superiority.

Perturbations need not block every selected route. Information differs between
local policies and full-map planners; prior static-training budgets differ in
realized updates, with no new training here. Priorities are incomplete/order-
sensitive. Successful-only means use different successful subsets; full success
denominators retain failures. No dynamic/global team optimality reference, robust
speed comparison or statistical significance claim. Collision rejection is the
simulator's rule, not learned coordination.

CP-06c is complete. Next CP-07a freezes larger 5/10/15 grids, 1/2/4 agents,
densities, horizons, congestion rules, models/budgets and fresh final scenarios
before collecting the final paper results. Preserve these development runs.

Final inline Python verification exited 0: generated the table from measured
analysis, archived 20 matching files with SHA-256 manifest, verified 123 actual
test definitions and all local links in 16 Markdown files, checked both saved
audit records and confirmed the QENN fingerprint again.

## Generated measured comparison

The table below is copied programmatically from analysis generated from raw CSV.

Generated from measured CSV. All failures/empty schedules are retained. Path/time means include successes only. Five model seeds reuse the same 20 geometries. Frozen controls retry independent original routes. Early completion stops later events. The static-trained policies receive no online updates.

| Method | Agents | Condition | Successes / episodes | Success | Successful makespan | Successful moves | Mean attempts | Mean plan calls | Mean plan failures | Episodes seeing addition |
|---|---|---|---|---|---|---|---|---|---|---|
| astar | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| astar | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.438 | 0.000 | 1.000 | 0.200 | 0 |
| astar_frozen | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| astar_frozen | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.438 | 0.000 | 1.000 | 0.200 | 0 |
| bfs | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| bfs | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| bfs_frozen | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| bfs_frozen | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| dijkstra | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| dijkstra | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| dijkstra_frozen | 2 | static | 18 / 20 | 90.0% | 4.389 | 7.167 | 0.000 | 1.000 | 0.100 | 0 |
| dijkstra_frozen | 4 | static | 16 / 20 | 80.0% | 6.125 | 15.312 | 0.000 | 1.000 | 0.200 | 0 |
| shared | 2 | static | 61 / 100 | 61.0% | 3.836 | 5.934 | 3.420 | 0.000 | 0.000 | 0 |
| shared | 4 | static | 25 / 100 | 25.0% | 6.760 | 12.680 | 27.280 | 0.000 | 0.000 | 0 |
| solo | 2 | static | 64 / 100 | 64.0% | 3.719 | 5.875 | 5.110 | 0.000 | 0.000 | 0 |
| solo | 4 | static | 27 / 100 | 27.0% | 5.148 | 12.630 | 32.580 | 0.000 | 0.000 | 0 |
| untrained | 2 | static | 1 / 100 | 1.0% | 1.000 | 2.000 | 0.740 | 0.000 | 0.000 | 0 |
| untrained | 4 | static | 0 / 100 | 0.0% | n/a | n/a | 13.800 | 0.000 | 0.000 | 0 |
| astar | 2 | dynamic | 18 / 20 | 90.0% | 5.833 | 8.611 | 0.000 | 2.250 | 0.350 | 19 |
| astar | 4 | dynamic | 16 / 20 | 80.0% | 7.562 | 18.812 | 0.000 | 2.600 | 0.600 | 20 |
| astar_frozen | 2 | dynamic | 18 / 20 | 90.0% | 7.722 | 7.167 | 0.650 | 1.000 | 0.100 | 19 |
| astar_frozen | 4 | dynamic | 13 / 20 | 65.0% | 10.308 | 14.615 | 9.600 | 1.000 | 0.200 | 20 |
| bfs | 2 | dynamic | 18 / 20 | 90.0% | 5.833 | 8.611 | 0.000 | 2.250 | 0.350 | 19 |
| bfs | 4 | dynamic | 16 / 20 | 80.0% | 7.688 | 18.812 | 0.000 | 2.600 | 0.600 | 20 |
| bfs_frozen | 2 | dynamic | 18 / 20 | 90.0% | 7.722 | 7.167 | 0.650 | 1.000 | 0.100 | 19 |
| bfs_frozen | 4 | dynamic | 14 / 20 | 70.0% | 10.286 | 14.857 | 7.350 | 1.000 | 0.200 | 20 |
| dijkstra | 2 | dynamic | 18 / 20 | 90.0% | 5.833 | 8.611 | 0.000 | 2.250 | 0.350 | 19 |
| dijkstra | 4 | dynamic | 16 / 20 | 80.0% | 7.688 | 18.812 | 0.000 | 2.600 | 0.600 | 20 |
| dijkstra_frozen | 2 | dynamic | 18 / 20 | 90.0% | 7.722 | 7.167 | 0.650 | 1.000 | 0.100 | 19 |
| dijkstra_frozen | 4 | dynamic | 14 / 20 | 70.0% | 10.286 | 14.857 | 7.350 | 1.000 | 0.200 | 20 |
| shared | 2 | dynamic | 58 / 100 | 58.0% | 4.914 | 6.534 | 3.420 | 0.000 | 0.000 | 95 |
| shared | 4 | dynamic | 25 / 100 | 25.0% | 8.360 | 12.600 | 27.100 | 0.000 | 0.000 | 100 |
| solo | 2 | dynamic | 61 / 100 | 61.0% | 4.754 | 6.443 | 5.100 | 0.000 | 0.000 | 95 |
| solo | 4 | dynamic | 28 / 100 | 28.0% | 7.321 | 13.107 | 31.690 | 0.000 | 0.000 | 100 |
| untrained | 2 | dynamic | 1 / 100 | 1.0% | 1.000 | 2.000 | 0.820 | 0.000 | 0.000 | 99 |
| untrained | 4 | dynamic | 0 / 100 | 0.0% | n/a | n/a | 13.870 | 0.000 | 0.000 | 100 |
