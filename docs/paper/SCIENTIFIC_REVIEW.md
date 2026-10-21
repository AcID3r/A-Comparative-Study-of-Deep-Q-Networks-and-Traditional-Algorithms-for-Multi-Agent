# Scientific review record

Date: 2026-10-07. Status: **completed for CP-08**.
This is a local implementation/scientific self-review, not external peer review.

## Completed design and reference checks

- Author name and affiliation were explicitly confirmed as Madhav Joshi,
  Marwadi University. No contact address or additional author was invented.
- Nine primary sources are documented in `references.json`. Source comparisons
  distinguish classical search, DQN, cooperative search, learned MAPF and graph
  optimization. No claim of first-ever comparison is made.
- The original QENN document is an unrelated reference and is preserved.
- Methods disclose local/full-map information differences, partial observability,
  fixed trained policies, small-map transfer, fixed-priority planning limitations,
  task-budget differences and the safe single-addition/removal dynamic schedule.
- Collision safety comes from the movement referee. Rejected attempts measure
  proposals, while actual collisions measure executed states; zero actual
  collisions cannot be attributed to learned cooperation.
- Failed cases remain in success denominators. Path/completion means condition
  on success and paired differences state their joint-success/exposure subsets.
- Exact optimality gaps apply only to successful static single-agent cases.
  Independent team distances are lower bounds, not feasible team optima.
- Five-seed variation is descriptive standard deviation, not a confidence interval
  or independent replication of the common maps. No significance test is claimed.
- Timing repetitions do not increase outcome sample size; training-loop and
  inference timings are kept separate. Fixed order, no warm-up and shared-machine
  effects prevent a universal runtime ranking.
- All 139 correctness tests passed; the six focused analysis/PDF checks passed
  again after the exact-gap table was added. A real five-page methods preview
  was inspected for equation and table layout.

## Final acceptance findings

The final replay audit checked 15,120 first trajectories and 652,244 steps.
Independent analysis checks verified 837 groups, exclusions, failure/gap/paired
denominators and hashes. Seven figures and all 17 PDF pages were reviewed using
an all-page overview and full-size critical pages. Required sections, nine result
tables, references, measured claims and source/data hashes match. No text exceeds
page bounds. Long tables repeat headers. Sparse figure/table pages are acceptable
for this review PDF; final Word layout remains CP-09.

Page review caught literal bold markers in A* captions. The renderer was fixed,
a real PDF regression was added, and content/layout checks were rerun. The final
full suite passed all 139 tests in 16.539 seconds. Reference punctuation was
corrected before final PDF generation. No missing or clipped content was found.

Final interpretation: A* success 89.17%, solo 24.17%, shared 22.19% on their
matched scenario sets. All six static joint-success movement contrasts favor
A* in the mean, with many ties and one shorter shared-policy team path. H2 has
faster conditional completion in three of six contrasts but lower exposed-pair
success in all six. H3 success decreases in 20/20 contrasts; attempts rise in
8/20. H4 shared success improves in two of six conditions and decreases in four.
These are descriptive findings, not causal ablations or significance tests.

The readable PDF uses ReportLab. XeLaTeX source is supplied but local TeX
compilation is unavailable. CP-09 remains the separate Word-format deliverable.
