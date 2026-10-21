# CP-07b — final experiment and scientific analysis

Date: **2026-10-07**. Status: **completed**.

## Collected evidence

The unchanged CP-07a seal was verified before creating final geometry. Run:
`results/raw/final_transfer/20261006T212837810546Z_40b3d4c4`.
Collection exited 0 and wrote its completion marker: 120 new geometries in twelve
size/density/endpoint strata, 15,120 unique episodes and three fresh timing
rollouts each (45,360 total). No final-test training or model selection occurred.
Failed and initially unreachable cases were retained.

Replay audit exited 0: **15,120 first trajectories, 652,244 steps**, no empty
dynamic schedules, active event prefixes matching, source/model hashes matching
and zero actual collisions. The common referee enforces executed-state safety;
this is not evidence that the DQN learned collision-free proposals.

Independent analysis checks exited 0: **837 grouped summaries** checked against
raw CSV, 120 unique geometries disjoint from the 280 sealed exclusions,
case/method counts, failure denominators, exact single-agent gaps, paired seed
differences and input/output hashes verified. Seven figures were generated in
PNG/SVG/PDF and inspected; nine manuscript result tables were generated.

## Exact main commands

```powershell
python -m experiments.run_final --final
python -m evaluation.audit_final results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 --output results/validation/CP-07b-audit.json
python -m unittest discover -v
python -m evaluation.summarize_final results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 --output results/analysis/CP-07b-base
python -m evaluation.research_analysis results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 --audit results/validation/CP-07b-audit.json --output results/analysis/CP-07b
python -m evaluation.check_research_outputs results/raw/final_transfer/20261006T212837810546Z_40b3d4c4 results/analysis/CP-07b --output results/validation/CP-07b-checks.json
python -m unittest test_research_analysis test_manuscript_tools -v
```

Observed full suite: **139 tests, 30.522s, OK**. Focused six-tool suite:
**6 tests, 1.176s, OK** after the exact-gap table addition. Earlier fixture failure
and its correction remain recorded in task history. These are correctness
outputs, separate from research data. A subsequent final suite is in CP-08.

## Measured findings and limits

Generated overall outcomes: BFS and Dijkstra each 644/720 (89.44%), A* 642/720
(89.17%), solo DQN 870/3,600 (24.17%), shared DQN 799/3,600 (22.19%). Policy
totals include five models on the same scenario set, not five times as many maps.
All six jointly successful static policy/A* contrasts have positive mean
policy-minus-A* movement differences. Many individual pairs tie. Smaller unpaired
successful DQN path means do not establish better paths on matching tasks.

H2 shows shorter post-addition completion for DQN in three of six jointly
successful contrasts, but lower exposed-pair success in all six. H3 has lower
success in 20/20 adjacent-agent contrasts and higher attempts in 8/20; classical
reservations keep attempts at zero. H4 favors shared success in two of six
conditions and solo in four. No significance or universal superiority is claimed.

Limitations: partially observed fixed policies trained only on static 5×5 maps;
full-current-map classical planners; unit-cost synthetic grids and at most four
agents; one safe addition/removal; incomplete fixed-priority planning; task budgets
do not match realized updates; conditional path/exposure comparisons; five-seed
variation is descriptive; fixed timer order/no warm-up/shared-machine effects.

## Files and next checkpoint

Added `evaluation/research_analysis.py`, `evaluation/check_research_outputs.py`,
`test_research_analysis.py`; saved raw run, base/extended analyses, audit/check
JSON and test evidence. Sealed algorithm/environment/runner source is unchanged.
CP-08 consumes this completed evidence for the scientific manuscript; CP-09
remains the separate Word formatting step. Original QENN Word hash is unchanged.
