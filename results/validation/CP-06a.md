# CP-06a: static multi-agent foundation validation

Date: 2026-10-07 local | Python 3.12.6 | Windows

CP-06a completes the environment/planner foundation. CP-06b shared learning and
dynamic team scheduling/replanning remain unfinished. This is correctness
evidence, not measured research performance.

## Executed checks

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

Environment checks: 11 passed in .324s. Early combined checks: 18 passed in .199s.
With priority sensitivity, full suite passed 101 tests in 8.627s. After adding
trace tampering checks, one test errored because its fixture tried to edit an
immutable tuple. Corrected the fixture to replace the reward sequence. Final
**103 tests passed in 4.551s**, exit 0. No production behavior change was needed
for that fixture correction. Both saved-trace commands and audits exited 0.

Eleven environment tests cover joint movement, vertex/swap rejection, legal
following, four-agent cascading rejection/rotation, absorbing goals, named
rewards, team bonus, horizon, reset, atomic validation and diagnostics copies.
One test checks all **625** four-agent action combinations on 2×2 for unique
occupancy and no edge swaps. Eight planner tests verify waits, swaps/detours,
permanent reservations, initially occupied goals, horizon/priority errors,
four-agent paths, single-agent optimum on 16 obstacle patterns, and an actual
priority-sensitive failure. Two trace tests replay real examples and detect
changed reward and failure records.

## Saved evidence

- [Final episodes](CP-06a-final-episodes.json) and [final replay audit](CP-06a-final-audit.json).
- [Initial episodes](CP-06a-episodes.json) and [initial audit](CP-06a-audit.json).
- [Initial source manifest](CP-06a-source/manifest.json).
- [Final source manifest](CP-06a-final-source/manifest.json).

Both trace sets record 16 cases and 26 steps: nine successful episodes, six
planning failures and one scripted conflict/timeout. Every saved observation,
reward/component, position, counter, done flag and path action replayed correctly.
Source hashes match. Actual final occupancy/edge collision counts are zero.
The scripted timeout has two rejected-agent attempts, demonstrating why attempts
and collisions must be separate.

Wait example: two agents finish after two turns using three total movements.
Four parallel lanes: four agents finish after three turns using 12 movements.
An example's default priority fails; reverse priority finishes after three turns
using four movements. Permanent goals and exhausted planning horizons are
reported as failures rather than partial executable solutions.

Initial snapshots preserve the code before explicit final-edge collision counting
was added. Final snapshots include producer/auditor/tests; older traces stay
unchanged. The current auditor checks current source hashes, so use matching
archived sources to replay historical traces after future edits.

## Limits and next step

Static unit-cost teams only; observation v2 has 17 features. Old v1 checkpoints
are unchanged and incompatible with new observations. Space-time planning
minimizes arrival turns including waits, not movement-only sum or global team
optimality. Agent priority/horizon can cause failure in a solvable case. Prevented
collisions demonstrate the simulator referee rather than learned cooperation.
No shared model or final multi-agent research measurements exist yet.

Next: define compatible model/replay contracts and individual endings, then
implement tiny shared-policy training and a matched single-agent-trained control.
