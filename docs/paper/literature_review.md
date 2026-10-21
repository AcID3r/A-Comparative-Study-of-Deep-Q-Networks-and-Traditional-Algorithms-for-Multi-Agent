# Verified literature notes

Verified 2026-10-07 through primary papers, publisher records, official course
notes and author repositories. References and metadata caveats are stored in
`references.json`; the manuscript uses the same numeric reference IDs.

| Reference | Problem | Method | Environment | Difference from this study |
|---|---|---|---|---|
| [1] MIT course notes | Unweighted shortest paths | BFS levels/parents | Graph | Teaching foundation; no learned team coordination |
| [2] Dijkstra | Minimum-length paths | Classical graph search | Weighted graph | No trained local policy or simultaneous team resolver |
| [3] Hart et al. | Minimum-cost paths | Heuristic search | Graph | Single search guarantees do not imply prioritized-team optimality |
| [4] Mnih et al. | Learned control | DQN | Atari | Does not directly establish performance on our navigation tasks |
| [5] Silver | Cooperative navigation | Space-time reservations | Game maps | Richer cooperative variants than our fixed-priority implementation |
| [6] Stern et al. | MAPF terminology/benchmarks | Variant definitions | Grid benchmarks | Informs explicit assumptions; our small custom maps are different |
| [7] Sartoretti et al. | Decentralized MAPF | RL plus expert imitation | Random worlds/hybrid robot demonstration | Our DQN has neither imitation training nor recurrent policy |
| [8] Li et al. | Decentralized robot planning | GNN communication/expert imitation | Cluttered workspaces | Our agents do not communicate or use graph embeddings |
| [9] Dai/Khalil et al. | Combinatorial optimization | RL and graph embedding | Vertex cover, cut, TSP | Different objectives and representations |

The study gap is experimental: a reproducible comparison of small static-trained
local DQNs and simple prioritized classical search under explicitly matched
static/changing custom grids. It is not a claim that classical search versus
learned multi-agent navigation has never been studied. No prior paper's published
performance numbers are reused as if measured on our maps.

Primary links appear in `references.json`. Stern's original conference paper is
2019, although the migrated publisher page displays 2021. PRIMAL and the GNN
paper are cited as inspected author preprints, with their version years. The
graph-optimization paper's author order follows its PDF, with equal first authors.
These differences are recorded rather than silently mixing metadata.
