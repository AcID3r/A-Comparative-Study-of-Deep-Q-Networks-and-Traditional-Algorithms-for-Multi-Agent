"""Scheduled unit-cost graph snapshots; events precede the corresponding action."""

from dataclasses import asdict, dataclass
from environments.grid_graph import GridGraph
from environments.single_agent_env import Action, SingleAgentEnv


@dataclass(frozen=True)
class ObstacleChange:
    tick: int
    position: tuple[int, int]
    operation: str

    def __post_init__(self):
        if type(self.tick) is not int or self.tick <= 0 or self.operation not in ('add', 'remove'):
            raise ValueError('Changes need a positive tick and add/remove operation')
        if not isinstance(self.position, tuple) or len(self.position) != 2 or any(type(x) is not int for x in self.position):
            raise ValueError('Change position must be an integer coordinate tuple')


class DynamicSingleAgentEnv(SingleAgentEnv):
    def __init__(self, graph, start, goal, *, max_steps=100, schedule=()):
        super().__init__(graph, start, goal, max_steps=max_steps)
        self._initial_graph = graph
        changes = tuple(schedule)
        if any(not isinstance(event, ObstacleChange) for event in changes):
            raise ValueError('Schedule must contain ObstacleChange objects')
        if len({(e.tick, e.position) for e in changes}) != len(changes):
            raise ValueError('At most one change per cell/tick is allowed')
        for event in changes:
            if (not graph.in_bounds(event.position) or event.position in (start, goal)
                    or event.tick > max_steps):
                raise ValueError('Changes must be in bounds, within the horizon, and protect endpoints')
        self.schedule = tuple(sorted(changes, key=lambda e: (e.tick, e.position)))

    def reset(self, *, seed=None):
        if seed is not None and (type(seed) is not int or seed < 0):
            raise ValueError('seed must be None or a nonnegative integer')
        self._graph = self._initial_graph
        self._graph_version = 0
        self._prepared_tick = 0
        self._history = []
        self._action_graph_version = None
        return super().reset(seed=seed)

    def _prepare(self):
        self._require_reset()
        if self._terminated or self._truncated:
            return
        tick = self._elapsed + 1
        if tick == self._prepared_tick:
            return
        for event in self.schedule:
            if event.tick != tick:
                continue
            obstacles = set(self.graph.obstacles)
            if event.position == self.position and event.operation == 'add':
                status = 'rejected_occupied'
            elif (event.position in obstacles) == (event.operation == 'add'):
                status = 'no_change'
            else:
                if event.operation == 'add':
                    obstacles.add(event.position)
                else:
                    obstacles.remove(event.position)
                self._graph = GridGraph(self.graph.rows, self.graph.cols, obstacles)
                self._graph_version += 1
                status = 'applied'
            self._history.append(asdict(event) | {'status': status, 'graph_version': self._graph_version})
        self._prepared_tick = tick

    def observe(self):
        self._prepare()
        return super().observe()

    def step(self, action):
        self._require_reset()
        if self._terminated or self._truncated:
            raise RuntimeError('Episode is complete; reset before stepping again')
        if not (type(action) is int or isinstance(action, Action)) or not 0 <= action < len(Action):
            raise ValueError('Invalid action')
        # Reset/previous step have already prepared the action's graph snapshot.
        self._action_graph_version = self._graph_version
        return super().step(action)

    def _info(self):
        return super()._info() | {'graph_version': self._graph_version,
            'action_graph_version': self._action_graph_version, 'prepared_tick': self._prepared_tick,
            'change_history': [dict(event) for event in self._history]}
