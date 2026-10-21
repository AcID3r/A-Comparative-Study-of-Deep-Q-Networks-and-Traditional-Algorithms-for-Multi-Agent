# Frozen final study protocol — CP-07a

The configuration in `final_experiment.json` is the final transfer study's
predeclared protocol. CP-07a pilot cases test software. CP-07b creates and runs
the new final cases only after a source/config/model/exclusion seal is saved.
Neither pilot nor final scores may select models, rewards or hyperparameters.

## Models and study question

Use the final CP-06b solo and shared-policy v2 models from training seeds 0–4.
Retain all ten models, with no extra training or online updates. These policies
were trained on static 5×5 maps at .10 wall probability, for 1,000 cycles per
seed/mode. Solo training used two individual tasks per cycle; shared training
used one two-agent episode. Both modes assigned 2,000 agent tasks per seed;
realized environment transitions, optimizer updates and reward timing differ.
See the archived training config and logs rather than assuming equal compute.

Each solo model is deployed independently for every agent, without learning.
Each shared model uses common weights and local observations for every agent.
The one-agent final condition uses the same v2 team environment and models.
It must not be mixed with v1 results from the earlier single-agent study.
Untrained v2 networks from the same five seeds are diagnostic controls.

The question is how these fixed policies transfer across sizes, agent counts,
obstacle probabilities, endpoint arrangements and graph changes. Larger sizes,
four-agent tasks and dynamic maps were not used for these models' training.
This is not a comparison between separately optimized models for each condition.

## Matrix and cases

| Factor | Fixed values |
|---|---|
| Square grid size | 5, 10, 15 |
| Bernoulli wall probability | .10, .20 |
| Endpoint arrangement | uniform, crossing |
| Agents | 1, 2, 4 |
| Environment | static, dynamic |
| Turn horizon | 30, 60, 90 for sizes 5, 10, 15 |
| Model seeds | 0, 1, 2, 3, 4 |
| Pilot maps per size/density/arrangement stratum | 1 (12 geometries) |
| Final maps per size/density/arrangement stratum | 10 (120 geometries) |
| Unique pilot/final episodes | 1,512 / 15,120 |
| Fresh timing rollouts per unique final episode | 3 (45,360 rollouts) |

Walls are sampled for every cell, including boundary/corner cells. Start and goal
cells are selected afterwards from free cells. Uniform arrangement samples eight
distinct free cells: four starts, then four goals. Crossing arrangement samples
four free left-boundary cells and four free right-boundary cells, sorts starts
top-to-bottom and goals bottom-to-top, and pairs by index. Endpoints use RNG
seed `map_seed + 70000`. One/two-agent cases use the first one/two of the same
four pairs. This matching controls map geometry, not aggregate task length.

Crossing is a congestion proxy: longer routes and different endpoint geometry
also change difficulty. It is not guaranteed to produce collisions or a strict
high-versus-low congestion ordering. Record pairwise intersections of independently
computed deterministic BFS routes for each agent count as a descriptive proxy.
Route overlap is not a measured simultaneous collision or a filter.

Pilot seeds begin at 100000; final seeds at 200000. Strata follow size, density,
arrangement order. Each has a 10000-candidate interval. Reject duplicate geometry
across all accepted strata and all recorded development banks, insufficient free
cells for eight endpoints, or insufficient free boundary endpoints for crossing.
Log each rejection. Final cases also exclude every pilot geometry. Record
requested and realized wall density separately. Do not filter disconnected or
individually unreachable tasks; retain these failures and initial distances.

CP-07a seals development-source hashes, geometry exclusions, pilot IDs, model
hashes, config and implementation hashes in `results/validation/CP-07a-freeze`.
Final cases are not generated or evaluated until CP-07b. A subsequent change to
a frozen file requires an explicit protocol amendment and new validation.

## Methods, dynamics and movement

Main methods: prioritized BFS, Dijkstra, A*, solo DQN and shared DQN. All costs
are one, so BFS is applicable. A* uses Manhattan distance. Planning is in
space-time with waits, vertex/edge reservations and permanent goal occupancy.
Priority is fixed agent-index order; prioritized planning can fail on a solvable
team instance and is not globally optimal. Planners see the current full graph;
policies see the 17 local v2 features. This information difference limits causal
claims about architecture alone.

Controls: each classical method's frozen initial routes and five untrained DQNs.
Classical methods have no model seed and execute once per unique condition,
not five replicated observations for five identical model seeds. There are
six classical method variants plus fifteen policy/model pairs = 21 runs per case.

In dynamic conditions add one free non-endpoint cell at tick 2 and remove it at
tick 8. Prefer independent initial BFS routes, then row-major free cells. The
chosen cell must be Manhattan-distance at least 2 from all four starts. It cannot
be occupied before tick 2 regardless of policy. Protect all eight endpoints so
the same schedule applies to 1/2/4-agent conditions. An absent candidate yields
an explicitly recorded empty schedule, retained in the denominator.

Events prepare before their action observation; early completion stops future
events. Check common active-event prefixes, not equal event counts after a
method has already finished. This perturbation can leave a method's route
unchanged. Main planners replan on graph changes or execution deviations using
current positions, remaining horizon and arrived agents' occupied goals. If a
complete plan is unavailable, joint WAIT continues until a graph change/timeout.
Frozen controls retry their independent original routes without replanning.

Movement and rewards remain unchanged: five actions, simultaneous proposals,
rejected vertex/swap/cascade conflicts, absorbing goals, active-turn costs and
one-time individual/team bonuses. Actual collisions must remain zero because
the environment enforces safety. Count rejected-agent attempts per turn
separately from unique vertex/swap pairs and actual collisions.

## Metrics, analysis and timing

Success means every agent arrives before the horizon. Include every failed,
unreachable, empty-schedule and priority-failure episode in success denominators.
Log steps, executed moves/cost, attempts, arrival ticks and planning diagnostics.
Completed makespan and sum of arrival times are missing on failed episodes.
Movement/path averages use successful episodes and state their sample counts.

Initial independent shortest path lengths sum to a lower bound for teams;
an unreachable individual makes this reference missing. The relative move gap
is defined only for a successful static single-agent episode with positive
exact initial shortest path length. Dynamic/multi-agent/failure/zero-reference
gaps are missing, with a saved reason. Do not call a team lower bound its optimum.

Dynamic addition exposure is separately recorded. For an exposed successful run,
steps after addition = makespan − add_tick + 1. Failures have missing completion
time. Report both exposed episode and exposed-success denominators; exposure
depends on earlier completion, so this subset alone cannot establish H2.

For learned policies report success rate per seed and descriptive mean/sample
standard deviation across the five seeds on matched maps. These maps are reused
across seeds; 50 outcomes in a stratum do not mean 50 independently trained
models. Classical success uses ten maps, with no model-seed variance. Do not
make significance claims from descriptive standard deviations. Matched
comparisons use identical map/agent/condition/seed keys for shared versus solo;
classical replanned/frozen comparisons omit model seed. Compare completion
metrics only on jointly successful matched cases and report that subset size.
The final analysis should stratify comparisons and assess all four hypotheses;
retain contrary findings and disclose the limited final map sample.

Use CPU, one PyTorch thread, greedy epsilon zero and no gradients/updates.
Three fresh deterministic final rollouts provide separately saved planning,
action-selection and complete-episode timers; only the first trajectory/outcome
enters result denominators. Check that all repetitions produce identical
non-time outcomes. Timer means are per case, not additional success samples.
The pilot runs once per case. Fixed method order, shared-machine load, no timing
warm-up and logging overhead limit runtime conclusions; do not infer universal
speed superiority. Preserve training wall time separately in CP-06b records.

## Acceptance and commands

CP-07a requires relevant/full tests, the complete pilot matrix, saved trajectory
replay/controller/model audits, safe common event prefixes, generated stratified
summaries, correct undefined values and failure denominators, a preserved QENN
hash, and the final seal. Pilot files stay under `results/validation` and are not
final research evidence. CP-07b runs the sealed final matrix, audits it, and
generates final figures plus stratified/matched analyses before paper writing.

```powershell
python -m unittest test_final_protocol -v
python -m unittest discover -v
python -m experiments.run_final
python -m evaluation.audit_final <pilot-run> --output results/validation/CP-07a-audit.json
python -m evaluation.summarize_final <pilot-run> --output results/validation/CP-07a-analysis
# CP-07b, after the seal exists:
python -m experiments.run_final --final
```
