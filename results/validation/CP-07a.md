# CP-07a — final protocol and full pilot validation

Date: 2026-10-07. Status: complete; CP-07b final measurements are pending.

## Accepted scope

The [frozen protocol](../../configs/final_protocol.md) fixes ten final geometries
per size/density/endpoint-arrangement stratum, 120 geometries total, and 15,120
unique episodes. Use all final CP-06b solo/shared models from five seeds without
extra training or online updates. Record larger-map/agent/dynamic transfer,
information differences, training budgets, fixed-priority limitations and
congestion-proxy confounds. Final geometry has not been generated.

One/two/four-agent tasks use nested endpoints. Uniform and opposing-boundary
crossing arrangements replace undefined low/high labels. Retain initially
unreachable cases, log geometry/endpoint rejections and avoid global team/dynamic
optimality claims. Three deterministic fresh final timing rollouts per unique
episode are not three independent outcome observations.

## Actual checks

- Initial nine protocol tests passed in 5.917 seconds, and 132 full tests passed
  in 11.246 seconds before adding the timing integration test.
- The initial pilot audit and first timing integration attempt failed on
  tuple-versus-JSON-list event coordinate comparisons. Corrected canonicalization
  in the validator; no measured file was edited. Preserve this failed history.
- Corrected ten protocol tests passed in 17.884 seconds. The integration exercises
  all 21 method/model combinations × three agent counts × two conditions on a
  pilot geometry, with three fresh timing rollouts each. A test-double seal and
  bank avoid generating final geometry; independent tests check real seal/hash
  rejection. Negative repeated-time tampering is detected.
- Final full suite: **133 tests passed in 39.046 seconds**, exit 0. This includes
  historical baseline/environment/learning/dynamic audits and ten protocol tests.
- The complete pilot saved **1,512 episodes on twelve geometries/strata**. The
  corrected audit replayed **63,386 steps**, all policy/controller decisions,
  observations, rewards, plans, diagnostics and CSV projections.
- **Zero actual collisions, zero empty schedules.** Common active-event prefixes
  match across methods and nested teams. Model fingerprints matched; the runner
  cloned/checked weights and update counters with no online training.
- Generated **648 stratified summaries** plus matched shared/solo and classical
  replanned/frozen comparisons and per-case timer summaries. Pilot outputs are
  software evidence; their success scores are not final research findings.
- The evidence-check script verifies summary denominators, successful-only means,
  undefined gaps, failed arrival metrics, matched sample counts, local document
  links, source/model/config/development fingerprints and original QENN SHA-256.

## Commands and artifacts

Exact executed commands are retained in [task.md](../../task.md).

- [Pilot collection](protocol_pilot/20261006T210712802711Z_2c64fadb/COMPLETE.json)
- [Replay audit](CP-07a-audit.json)
- [Generated summaries](CP-07a-analysis/summary.json)
- [Generated matched comparisons](CP-07a-analysis/matched_cases.json)
- [Final seal](CP-07a-freeze/manifest.json)
- [Evidence-check script](check_cp07a.py)

The collection's archived checker predates the serialization fix. The corrected
validator and final sealed implementation are separately archived under
`CP-07a-source`, with matching hashes. This does not rewrite the old collection's
source record or measured outcomes. Raw checks and pilot artifacts remain under
`results/validation`, separate from future final research data.

## Remaining work and practical limits

At CP-07b verify the seal and run the full matrix, replay-audit it, and generate
final figures plus stratified, matched-case hypothesis analyses. Seed standard
deviations describe five models on shared maps, not independent map uncertainty
or significance tests. Crossing may increase route length independently of
congestion. Mild add/remove events may not affect every method's route; early
completion stops future events, and exposed-completion means exclude failures.
Fixed method order, no timing warm-up, logging overhead and machine load limit
runtime interpretation. Do not claim universal speed superiority.

The unrelated QENN Word reference remains unchanged. CP-08 writes/reviews the
graph-search science from audited final outputs and verified primary sources.
CP-09 then produces/checks a separate full Word manuscript in the reference format.
