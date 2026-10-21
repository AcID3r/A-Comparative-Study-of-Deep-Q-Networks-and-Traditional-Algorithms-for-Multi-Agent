# Scientific manuscript source: fixed sections

## 1. Introduction

Graph search supplies routes for software agents and mobile robots. Breadth-first
search (BFS) finds minimum-edge paths in unweighted graphs [1], Dijkstra's algorithm
addresses minimum-length graph paths [2], and A* directs search with a heuristic
estimate [3]. These foundations solve an individual graph-search problem; using
them for several simultaneous agents additionally requires temporal coordination.
Multi-agent pathfinding (MAPF) has applications in automated warehouses and
robotics, but collision and goal-occupancy assumptions differ between studies [6].

Reinforcement learning offers a different approach: a policy is learned before
deployment and then reused to choose actions. DQN provides a neural approximation
to action values [4]. A reusable policy might react to a changed neighborhood
without running a fresh graph search, although that does not establish optimal
paths, reliable generalization or a computational advantage over replanning.
The present study tests these possibilities with a deliberately small method.

We compare fixed-priority space-time BFS, Dijkstra and A* with compact DQNs trained
on static 5×5 maps. A solo-trained policy is deployed independently for each
agent; a shared-policy model is trained with two simultaneous agents. Both are
tested without further learning on fresh 5×5, 10×10 and 15×15 grids, one/two/four
agents, and static or scheduled-changing obstacles. Frozen classical routes and
untrained networks are controls. Our question is how these particular trained
policies transfer, rather than whether reinforcement learning universally replaces
classical search. The planners receive the full current graph and DQNs receive
local features, so the comparison includes an information-access difference.

The study contributes (1) a tested environment with simultaneous proposals,
absorbing goals and explicit dynamic snapshots; (2) a frozen, geometry-disjoint
comparison retaining unsuccessful cases and five model seeds; and (3) an audited
analysis of transfer, path quality, conflict attempts and runtime. The novelty is
the controlled experiment and reproducible implementation, not a new MAPF or
reinforcement-learning algorithm.

Before final collection we recorded four hypotheses. H1 predicts shorter static
paths from A* than DQN. H2 predicts faster completion after obstacle changes from
DQN than fixed precomputed routes, with replanning also evaluated. H3 predicts
lower success and more conflict attempts with more agents. H4 predicts stronger
success from shared training than independent use of a solo-trained policy.
Each is assessed descriptively on matched cases; contrary evidence is retained.

## 2. Related Work

### 2.1 Classical shortest-path algorithms

BFS uses graph-distance levels [1]. Dijkstra searches minimum-length paths [2],
while A* adds heuristic guidance [3]. In our unit-cost grid, Manhattan distance
is the heuristic. These single-agent foundations do not make the entire
fixed-priority team planner optimal. Our team searches add a time coordinate,
wait actions and reservations, following the cooperative-search principle [5].

### 2.2 Deep reinforcement learning and DQN

Mnih et al. demonstrated learned control through neural action values [4]. Our
implementation uses the DQN ideas of experience replay and a target network,
with a small multilayer perceptron receiving a vector of navigation features.
It differs from pixel-based Atari control in architecture, rewards and simulator
assumptions. We examine trained policies' failures as well as successes.

### 2.3 Reinforcement learning on graphs

Dai and Khalil et al. combine reinforcement learning with graph embeddings for
combinatorial optimization [9]. That work concerns objectives such as vertex
cover, graph cuts and traveling-salesman solutions. Our DQN uses no graph
embedding and chooses local navigation actions. Consequently, graph-optimization
results cannot be imported as evidence for collision-safe pathfinding here.

### 2.4 Multi-agent pathfinding

Silver's cooperative search uses space-time routes and reservations [5]. Stern
et al. clarify MAPF variants and evaluation conventions [6]. Learned MAPF methods
can be substantially richer than our baseline: PRIMAL combines reinforcement
and expert imitation learning [7], and Li et al. communicate local features
through graph neural networks trained by expert imitation [8]. We use neither
expert demonstrations nor communication. Their results therefore motivate
future work rather than provide performance numbers comparable to our maps.

| Source | Problem/method | Setting | Difference from this experiment |
|---|---|---|---|
| Dijkstra [2], Hart et al. [3] | Minimum-cost graph search | Known graphs | No learned simultaneous-agent policy |
| Mnih et al. [4] | DQN control | Atari | Different observation/action domain |
| Silver [5] | Cooperative space-time search | Game navigation | Includes richer cooperative search variants |
| Stern et al. [6] | MAPF terminology/benchmarks | Grid MAPF | Our custom maps are not their benchmark |
| Sartoretti et al. [7] | RL with imitation | Decentralized MAPF | Our small DQN lacks imitation learning |
| Li et al. [8] | GNN feature communication | Multi-robot planning | Our agents do not communicate |
| Dai/Khalil et al. [9] | RL with graph embeddings | Combinatorial graph tasks | Different objective and representation |

The selected experimental gap is a transparent comparison of small
static-trained local DQNs and simple classical replanning under matched graph
changes. This is not a claim that such comparisons have never been studied.

## 3. Problem Formulation

At action tick t the environment has a unit-cost grid graph G_t = (V_t, E_t).
Free cells are vertices and orthogonal free-cell adjacency defines movement
edges. There are n agents, with positions p_t^i, distinct starts s^i and distinct
goals g^i. Each may move up, down, left or right, or wait. Upon first arrival an
agent remains at its goal, continuing to occupy that vertex. The global state
includes positions, goals, the current graph and elapsed time; a policy receives
only its feature observation. The local observation is generally partially
observable, so we do not assert that its vector is a Markov state.

All actions are proposed simultaneously. A moving proposal into an obstacle or
outside the grid fails. Moving proposals sharing a destination and opposite
edge swaps are rejected. Rejection then propagates until a move cannot enter
a cell whose occupant now stays. Following a cell vacated in the same tick and
cycles longer than two are permitted. This centralized movement referee enforces
collision safety for every method, without supplying extra information to the
learned policies. Rejected-agent attempts and actual collisions are distinct.

Wall changes prepare before the corresponding action observation. At tick 2 a
safe free cell is added to the obstacle set, then removed at tick 8. All eight
candidate team endpoints are protected, and the added cell is initially at
Manhattan distance at least 2 from all four starts. No agent can occupy it after
only one move. Events are deterministic and shared across methods and nested
team sizes, but completion stops subsequent events. Empty schedules remain in
the denominator if no eligible cell exists. The route-dependent perturbation
need not obstruct every selected method's path.

Our primary objective is feasible team completion within horizon H. We then
report makespan T = max_i T_i, sum of first-arrival times sum_i T_i, executed
movement count L, conflict attempts and computational time. A single weighted
objective is not minimized by all implementations: prioritized planners minimize
each agent's arrival turns in fixed order, and DQN optimizes a shaped return.
This distinction prevents a misleading claim of a shared global optimality target.

## 4. Methodology

### 4.1 Environment and observations

The v2 observation has 17 normalized features: current row/column (2), signed
goal displacement (2), neighboring wall flags (4), neighboring boundary flags
(4), remaining time (1), and adjacent other-agent occupancy flags (4). Coordinates
and goal displacements are normalized by each grid's row/column span. Policy
inputs contain these features only, with no future schedule, full graph or
diagnostic counters. All final one-agent cases also use this v2 team interface;
earlier 13-feature development results are not pooled into final comparisons.

The observation/action/reward loop is illustrated in Figure 1. After joint
movement, a fresh next observation includes any event prepared for the next
action tick. Reset restores the original graph, positions and event history.

### 4.2 Rewards and finite-horizon learning

An active agent receives a -1 turn cost; additional penalties are -10 for an
obstacle attempt, -5 for a boundary attempt, and -25 for a rejected conflict
attempt. First goal arrival awards +100 once. Team completion awards +100 once
to every agent, including agents that arrived earlier. Finished agents incur
no turn cost. Reset-at-goal gives no free completion bonus. Named components
are logged separately. The reward is therefore the sum of applicable components,
not mutually exclusive event labels in a table.

The online network estimates Q(o,a;theta). For replay samples the target is

$$y = r + \gamma (1-d) \max_{a'} Q(o',a';\theta^-),$$

where d is team termination or finite-horizon truncation. The loss is

$$\mathcal{L}(\theta) = \frac{1}{B}\sum_{j=1}^{B} [y_j-Q(o_j,a_j;\theta)]^2.$$

Both endings mask the bootstrap because there is no continuation beyond this
task's allowed horizon. Shared replay retains arrived-agent forced-WAIT
transitions until the team ends, preserving their delayed team bonuses.

### 4.3 Models and training

The network is 17–128–128–5, with ReLU hidden activations. Adam uses learning
rate .001, discount .99, batch 64, replay capacity 50,000, warm-up 256
transitions, an update every eight transitions, target copying every 500
optimizer updates, and gradient clipping at norm 10. Epsilon falls linearly
from 1 to .05 over 600 cycles. Five training seeds (0–4) are retained.

Models train on 50 static 5×5 geometries at .10 wall probability; ten validation
geometries are observed without best-checkpoint selection. Each seed/mode uses
1,000 cycles. A solo cycle consists of two one-agent tasks; a shared cycle
consists of one two-agent task. Both assign 2,000 agent tasks per seed. They do
not match realized transitions, updates or reward timing: solo team bonuses
arrive with individual completion, while shared bonuses wait for the last agent.
These differences are reported as limitations of H4's causal interpretation.
Training geometry generation also kept the two opposite corner cells free,
before sampling team endpoints from all free cells; final wall sampling covers
every cell. Solo training has zero other-agent occupancy features, whereas shared
training encounters nearby teammates. Matching vector formats therefore does
not match the full observation distribution at deployment.

Final weights are retained for every seed. During evaluation epsilon is zero,
gradients and learning are disabled, and weights/update counters are checked
for preservation. There is no online obstacle-change adaptation through training.
An untrained v2 network for each seed is a diagnostic control. Parameter sharing
does not give agents explicit communication or a centralized critic.

### 4.4 Classical methods and controls

BFS uses a FIFO queue; Dijkstra and A* use stable heaps. Space-time states are
(cell, tick), with unit turn costs including waits. Reservations forbid occupied
vertices, opposite edges and permanent earlier-agent goals. Priority is agent
index. Plans use the current graph and remaining horizon, and are recomputed
after graph changes or execution deviations. A failed complete plan leads to
joint waiting until a relevant change or timeout, rather than immediate episode
removal. This decoupled planner is not complete or globally team-optimal.
The same space-time planner is used for one-agent final cases, including wait
states. Its runtime is therefore not the runtime of an optimized spatial-only
static shortest-path implementation, even though successful static one-agent
paths can be checked against the exact spatial BFS distance.

Frozen variants compute their routes only on the initial graph. Each agent
advances its route cursor only when the next route cell is executed; blocked
movements are retried. Resulting delays may invalidate original temporal
reservations, although the common referee still rejects conflicts. Frozen
routes are controls, not the main comparison for a changing graph.

## 5. Experimental Setup

### 5.1 Frozen evaluation design

The protocol was fixed before generating final cases. There are three grid
sizes (5, 10, 15), two wall probabilities (.10, .20), two endpoint arrangements
(uniform, crossing), three nested agent counts (1, 2, 4) and two conditions
(static, dynamic). Horizons are 30, 60 and 90 turns by size. Ten final geometries
per size/density/arrangement yield 120 geometries. Six classical variants and
fifteen policy/seed pairs yield 21 runs per agent/condition case: 15,120 unique
episodes. Each final episode has three fresh deterministic timing rollouts,
45,360 rollouts total. Only repeat zero contributes an outcome/trajectory.

Wall sampling includes every cell. Endpoints are sampled from free cells with
RNG seed map_seed + 70000. Uniform sampling draws eight distinct cells, four
starts followed by four goals. Crossing sampling draws four free left-edge
starts ordered top-to-bottom and four free right-edge goals ordered bottom-to-top.
The first one/two pairs form the smaller-team tasks. Crossing is a traffic
proxy and also changes route length; it does not guarantee high congestion.
Initial deterministic BFS-route overlap pairs are recorded descriptively.

Final seed intervals start at 200000 and advance by 10000 per stratum in
size/density/arrangement order. Duplicate geometries, too few free cells or too
few free boundary endpoints for crossing are rejected and logged. Unreachable
tasks are retained. Final geometry excludes all recorded development and pilot
geometries, with 280 exclusions fixed in the seal. Requested probability and
realized density are distinct. Pilot runs validate software and are excluded
from all final research tables.

### 5.2 Metrics and analysis

Success requires all agents to arrive within the horizon. Failures remain in
success denominators; completed makespan and arrival sum are missing on failures.
Path and completion means use successful episodes and report sample counts.
The exact relative movement gap (L-L*)/L* is computed only for successful static
one-agent episodes with positive reference distance. Independent shortest paths
give a team lower bound, not a global feasible optimum. Dynamic/team gaps are
left missing with reasons rather than fabricated.

Learned results report seed rates and their sample standard deviation on shared
maps. These are descriptive model variability, not confidence intervals or
independent map replications. Matched shared-versus-solo comparisons preserve
map, agent count, condition and seed. Classical paired comparisons have no
training seed. Learned-to-classical pairs reuse a classical reference for each
model seed, without pretending the reference has independently trained replicas.
Completion comparisons use jointly successful cases and state their denominator.

For H2 we separately record whether an addition was observed. Successful
exposed completion steps are T - 2 + 1; a failure does not acquire a made-up
completion time. Both-exposed paired comparisons also report success differences.
Conditioning on exposure or joint success can change the sampled difficulty,
so such comparisons alone do not establish an adaptation advantage.

### 5.3 Hardware, timing and validation

Execution uses a local Windows 11 CPU system, Python 3.12.6, PyTorch 2.11.0,
NumPy 1.26.4 and Matplotlib 3.10.0, with eight logical CPUs reported by the
environment and one PyTorch thread. Exact processor/platform strings are archived
in run metadata; no unsupported hardware model or GPU is assumed. Repeated
planning, action-selection and complete-episode timers are stored separately.
Training timers come from the saved training logs. Method order is fixed and
there is no timing warm-up; machine load and logging overhead limit speed claims.
Recorded training seconds sum timed episode loops, including optimizer work;
they exclude validation, setup and checkpoint saving and are not an end-to-end
training-job wall time.
Expanded classical states count processed space-time nodes, including popped
goals and excluding stale heap entries, summed over initial planning and replans.
The corresponding metric is not defined for neural action selection.

Correctness tests cover known/weighted shortest paths, simultaneous collision
resolution, goal absorption, dynamic visibility, failed plans, model versions,
replay targets and metric denominators. The saved final audit regenerates
scenarios and re-executes every first-trajectory policy/planner decision, checking
observations, rewards, plans, metrics, hashes and common active-event prefixes.
Timing repetitions are checked for identical non-time outcomes during collection;
the audit validates repetition counts and finite nonnegative timers, rather than
claiming to reproduce machine elapsed times exactly. A recorded success is never
substituted for this evidence.
