"""Static unit-cost space-time prioritized search with permanent goal occupancy."""
from dataclasses import dataclass
from collections import deque
from heapq import heappop, heappush
from itertools import count
from time import perf_counter
from environments.multi_agent_env import MultiAgentEnv


@dataclass(frozen=True)
class TeamPlan:
    paths: tuple | None
    partial_paths: tuple
    priority: tuple
    failed_agent: int | None
    failure_reason: str | None
    expanded_nodes: int
    planning_time_seconds: float

    @property
    def success(self):
        return self.paths is not None


def prioritized_plan(graph, starts, goals, *, method='astar', max_steps=100, priority=None):
    started = perf_counter()
    env = MultiAgentEnv(graph, starts, goals, max_steps=max_steps)
    if method not in ('bfs', 'dijkstra', 'astar'):
        raise ValueError('method must be bfs, dijkstra or astar')
    order = tuple(range(env.n_agents)) if priority is None else tuple(priority)
    if len(order) != env.n_agents or any(type(i) is not int for i in order) or set(order) != set(range(env.n_agents)):
        raise ValueError('priority must be a permutation of agent indices')
    vertices, edges = set(), set()
    paths = [None] * env.n_agents
    # Agents already at goals cannot vacate their cells even if planned last.
    for s, g in zip(env.starts, env.goals):
        if s == g:
            vertices.update((s, t) for t in range(max_steps+1))
    expanded = 0
    for i in order:
        start, goal = env.starts[i], env.goals[i]
        if start == goal:
            path, checked = (start,), 0
        else:
            path, checked = _search(graph, start, goal, max_steps, vertices, edges, method)
        expanded += checked
        if path is None:
            return TeamPlan(None, tuple(paths), order, i, 'no_reserved_path_within_horizon', expanded, perf_counter()-started)
        paths[i] = path
        for t, pos in enumerate(path):
            vertices.add((pos, t))
            if t:
                edges.add((path[t-1], pos, t))
        vertices.update((goal, t) for t in range(len(path), max_steps+1))
    return TeamPlan(tuple(paths), tuple(paths), order, None, None, expanded, perf_counter()-started)


def _search(graph, start, goal, horizon, vertices, edges, method):
    serial = count()
    def h(p):
        return abs(p[0]-goal[0])+abs(p[1]-goal[1]) if method == 'astar' else 0
    first = (start, 0)
    frontier = [(h(start), next(serial), first)]
    queue = deque([first])
    parents = {first: None}
    expanded = 0
    while queue if method == 'bfs' else frontier:
        if method == 'bfs':
            state = queue.popleft()
        else:
            _, _, state = heappop(frontier)
        pos, tick = state
        expanded += 1
        if pos == goal and all((goal, future) not in vertices for future in range(tick, horizon+1)):
            path = []
            while state is not None:
                path.append(state[0])
                state = parents[state]
            return tuple(reversed(path)), expanded
        if pos == goal:
            # The simulator makes goals absorbing: never route through one's
            # own goal and depart again to evade a later reservation.
            continue
        if tick == horizon:
            continue
        for dest in (*graph.neighbors(pos), pos):
            nxt = dest, tick+1
            if nxt in parents or nxt in vertices or (dest, pos, tick+1) in edges:
                continue
            parents[nxt] = state
            if method == 'bfs':
                queue.append(nxt)
            else:
                heappush(frontier, (tick+1+h(dest), next(serial), nxt))
    return None, expanded


def plan_actions(paths, tick):
    """Actions at zero-based turn index, including waits after arrival."""
    from environments.single_agent_env import ACTION_DELTAS
    actions = []
    for path in paths:
        before, after = path[min(tick, len(path)-1)], path[min(tick+1, len(path)-1)]
        actions.append(ACTION_DELTAS.index((after[0]-before[0], after[1]-before[1])))
    return tuple(actions)
