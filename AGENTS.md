# Project working instructions

The graph-search study in `docs/prd.md` is the active scope. Preserve the existing QENN
Word document; it belongs to a different research topic.

## Every implementation iteration or completed checkpoint

1. Read `docs/task.md`, `docs/prd.md`, and the relevant design sections before editing.
2. Complete the smallest useful change and run its relevant checks.
3. Update `docs/task.md` with the current state, files changed, exact commands,
   observed outcomes, unresolved issues, and next concrete steps.
4. Update `docs/everythingtoknow.md` in language a ten-year-old can understand:
   explain what changed, why, how it works, what was tested, and what remains.
5. Update `docs/tdd.md` and `docs/implementationstrategy.md` if interfaces or decisions
   changed. Update `docs/prd.md` if accepted requirements changed.
6. Add a dated checkpoint entry when a milestone is completed. Keep previous
   entries. Mark partial or failed work accurately, never as completed.

Use test evidence rather than assumptions. Never invent experimental results,
silently change metrics, manually edit measured result values, or claim DQN
outperforms another method without the completed experiment. Keep correctness
test outputs separate from research data. Implement and validate single-agent
baselines before beginning DQN. Do not add unrelated features to this project.
