"""Simultaneous static unit-cost team episodes; observation layout v2."""
from copy import deepcopy
from itertools import combinations
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action, ACTION_DELTAS, OBSERVATION_FEATURES as SINGLE_FEATURES

OBSERVATION_VERSION = 2
OBSERVATION_FEATURES = SINGLE_FEATURES + ('agent_up', 'agent_down', 'agent_left', 'agent_right')


class MultiAgentEnv:
    def __init__(self, graph, starts, goals, *, max_steps=100):
        if not isinstance(graph, GridGraph) or not graph.uniform_costs or graph.minimum_cost != 1:
            raise ValueError('Teams require a unit-cost GridGraph')
        self.starts, self.goals = tuple(starts), tuple(goals)
        if not self.starts or len(self.starts) != len(self.goals):
            raise ValueError('Provide one start and goal per agent')
        for start, goal in zip(self.starts, self.goals):
            graph.validate_endpoints(start, goal)
        if len(set(self.starts)) != len(self.starts) or len(set(self.goals)) != len(self.goals):
            raise ValueError('Starts and goals must each be unique')
        if type(max_steps) is not int or max_steps <= 0:
            raise ValueError('max_steps must be a positive integer')
        self.graph, self.max_steps = graph, max_steps
        self.n_agents = len(self.starts)
        self._initialized = False

    def _require_reset(self):
        if not self._initialized:
            raise RuntimeError('Call reset first')

    @property
    def positions(self):
        self._require_reset()
        return tuple(self._positions)

    def reset(self, *, seed=None):
        if seed is not None and (type(seed) is not int or seed < 0):
            raise ValueError('seed must be nonnegative or None')
        self._seed, self._elapsed = seed, 0
        self._positions = list(self.starts)
        self._arrivals = [0 if s == g else None for s, g in zip(self.starts, self.goals)]
        self._moves = [0] * self.n_agents
        self._returns = [0.0] * self.n_agents
        self._conflicts = [0] * self.n_agents
        self._obstacles = [0] * self.n_agents
        self._boundaries = [0] * self.n_agents
        self._vertex = self._swaps = self._actual = 0
        self._terminated, self._truncated = all(t is not None for t in self._arrivals), False
        self._components = [self._empty_components() for _ in self.starts]
        self._events = {'vertex_pairs': [], 'swap_pairs': [], 'rejected_agents': []}
        self._initialized = True
        return self.observe(), self.info()

    @staticmethod
    def _empty_components():
        return dict.fromkeys(('step', 'obstacle', 'boundary', 'conflict', 'goal', 'team'), 0.0)

    def observe(self):
        self._require_reset()
        rs, cs = max(self.graph.rows-1, 1), max(self.graph.cols-1, 1)
        observations = []
        for i, ((r, c), goal) in enumerate(zip(self.positions, self.goals)):
            adjacent = [(r+dr, c+dc) for dr, dc in ACTION_DELTAS[:4]]
            others = set(self.positions[:i] + self.positions[i+1:])
            observations.append((r/rs, c/cs, (goal[0]-r)/rs, (goal[1]-c)/cs,
                *(float(p in self.graph.obstacles) for p in adjacent),
                *(float(not self.graph.in_bounds(p)) for p in adjacent),
                (self.max_steps-self._elapsed)/self.max_steps,
                *(float(p in others) for p in adjacent)))
        return tuple(observations)

    def step(self, actions):
        self._require_reset()
        if self._terminated or self._truncated:
            raise RuntimeError('Episode complete; reset first')
        if not isinstance(actions, (tuple, list)) or len(actions) != self.n_agents:
            raise ValueError('One action per agent is required')
        if any(not (type(a) is int or isinstance(a, Action)) or not 0 <= a < 5 for a in actions):
            raise ValueError('Every action must be an integer 0..4')
        old = self.positions
        proposed = list(old)
        components = [self._empty_components() for _ in old]
        for i, action in enumerate(actions):
            if self._arrivals[i] is not None:
                continue
            components[i]['step'] = -1.0
            dr, dc = ACTION_DELTAS[action]
            target = old[i][0]+dr, old[i][1]+dc
            if not self.graph.in_bounds(target):
                components[i]['boundary'] = -5.0
                self._boundaries[i] += 1
            elif target in self.graph.obstacles:
                components[i]['obstacle'] = -10.0
                self._obstacles[i] += 1
            else:
                proposed[i] = target
        moving = {i for i in range(self.n_agents) if proposed[i] != old[i]}
        rejected, vertices, swaps = set(), set(), set()
        for i, j in combinations(range(self.n_agents), 2):
            if proposed[i] == proposed[j]:
                vertices.add((i, j))
                rejected.update({i, j} & moving)
            if i in moving and j in moving and proposed[i] == old[j] and proposed[j] == old[i]:
                swaps.add((i, j))
                rejected.update((i, j))
        # Rejection can make another agent's destination occupied. Resolve to a
        # fixed point before moving any agent; do not use agent iteration order.
        while True:
            final = [old[i] if i in rejected else proposed[i] for i in range(self.n_agents)]
            extra = set()
            for i, j in combinations(range(self.n_agents), 2):
                if final[i] == final[j]:
                    vertices.add((i, j))
                    extra.update(({i, j} & moving) - rejected)
            if not extra:
                break
            rejected.update(extra)
        self._positions = final
        actual = sum(final[i] == final[j] or
                     (final[i] == old[j] and final[j] == old[i])
                     for i, j in combinations(range(self.n_agents), 2))
        self._actual += actual
        assert len(set(final)) == self.n_agents, 'Joint occupancy invariant broken'
        assert actual == 0, 'Joint collision invariant broken'
        self._elapsed += 1
        for i in range(self.n_agents):
            if i in rejected:
                self._conflicts[i] += 1
                components[i]['conflict'] = -25.0
            if final[i] != old[i]:
                self._moves[i] += 1
            if self._arrivals[i] is None and final[i] == self.goals[i]:
                self._arrivals[i] = self._elapsed
                components[i]['goal'] = 100.0
        self._terminated = all(t is not None for t in self._arrivals)
        if self._terminated:
            for c in components:
                c['team'] = 100.0
        self._truncated = self._elapsed >= self.max_steps and not self._terminated
        rewards = tuple(sum(c.values()) for c in components)
        self._returns = [r+new for r, new in zip(self._returns, rewards)]
        self._vertex += len(vertices)
        self._swaps += len(swaps)
        self._events = {'vertex_pairs': sorted(vertices), 'swap_pairs': sorted(swaps), 'rejected_agents': sorted(rejected)}
        self._components = components
        return self.observe(), rewards, self._terminated, self._truncated, self.info()

    def info(self):
        self._require_reset()
        return deepcopy({'positions': self.positions, 'goals': self.goals, 'seed': self._seed,
            'observation_version': OBSERVATION_VERSION, 'elapsed_steps': self._elapsed,
            'arrival_steps': tuple(self._arrivals), 'moves': tuple(self._moves),
            'total_moves': sum(self._moves), 'path_cost': float(sum(self._moves)),
            'episode_rewards': tuple(self._returns), 'reward_components': self._components,
            'conflict_attempts': tuple(self._conflicts), 'vertex_conflicts': self._vertex,
            'swap_conflicts': self._swaps, 'actual_collisions': self._actual,
            'obstacle_attempts': tuple(self._obstacles), 'boundary_attempts': tuple(self._boundaries),
            'events': self._events, 'terminated': self._terminated, 'truncated': self._truncated,
            'success': self._terminated, 'makespan': max(self._arrivals) if self._terminated else None,
            'failure_reason': 'time_limit' if self._truncated else None})
