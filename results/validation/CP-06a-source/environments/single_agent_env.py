"""Static unit-cost navigation episodes; standard-library reset/step API."""

from enum import IntEnum
from environments.grid_graph import GridGraph, Position


class Action(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3
    WAIT = 4


ACTION_DELTAS = ((-1, 0), (1, 0), (0, -1), (0, 1), (0, 0))
OBSERVATION_VERSION = 1
OBSERVATION_FEATURES = (
    'position_row', 'position_col', 'goal_delta_row', 'goal_delta_col',
    'wall_up', 'wall_down', 'wall_left', 'wall_right',
    'boundary_up', 'boundary_down', 'boundary_left', 'boundary_right',
    'remaining_time',
)


class SingleAgentEnv:
    """A fixed map and endpoints; call reset before every episode.

    reset -> (observation, info)
    step -> (observation, reward, terminated, truncated, info)
    Observations are immutable tuples of 13 floats; this is not a Gymnasium class.
    """

    def __init__(self, graph: GridGraph, start: Position, goal: Position, *, max_steps: int = 100):
        if not isinstance(graph, GridGraph):
            raise ValueError('graph must be a GridGraph')
        graph.validate_endpoints(start, goal)
        if type(max_steps) is not int or max_steps <= 0:
            raise ValueError('max_steps must be a positive integer')
        if not graph.uniform_costs or graph.minimum_cost != 1:
            raise ValueError('SingleAgentEnv currently requires unit movement costs')
        self._graph, self._start, self._goal, self._max_steps = graph, start, goal, max_steps
        self._initialized = False

    @property
    def graph(self):
        return self._graph

    @property
    def start(self):
        return self._start

    @property
    def goal(self):
        return self._goal

    @property
    def max_steps(self):
        return self._max_steps

    @property
    def position(self):
        self._require_reset()
        return self._position

    def _require_reset(self):
        if not self._initialized:
            raise RuntimeError('Call reset before using the episode')

    def reset(self, *, seed: int | None = None):
        if seed is not None and (type(seed) is not int or seed < 0):
            raise ValueError('seed must be None or a nonnegative integer')
        # The fixed map has no stochastic transitions; seed is recorded, not used
        # to randomize this episode or touch the process-wide random generator.
        self._seed = seed
        self._position = self.start
        self._elapsed = self._moves = self._obstacle_attempts = self._boundary_attempts = 0
        self._path_cost = self._episode_reward = 0.0
        self._terminated = self.start == self.goal
        self._truncated = False
        self._arrival_step = 0 if self._terminated else None
        self._event = 'already_at_goal' if self._terminated else 'reset'
        self._components = {'step': 0.0, 'obstacle': 0.0, 'boundary': 0.0, 'goal': 0.0}
        self._requested_position = self.start
        self._action = None
        self._executed_move = False
        self._initialized = True
        return self.observe(), self._info()

    def observe(self) -> tuple[float, ...]:
        self._require_reset()
        r, c = self.position
        row_scale, col_scale = max(self.graph.rows - 1, 1), max(self.graph.cols - 1, 1)
        adjacent = [(r + dr, c + dc) for dr, dc in ACTION_DELTAS[:4]]
        walls = tuple(float(p in self.graph.obstacles) for p in adjacent)
        boundaries = tuple(float(not self.graph.in_bounds(p)) for p in adjacent)
        return (r / row_scale, c / col_scale,
                (self.goal[0] - r) / row_scale, (self.goal[1] - c) / col_scale,
                *walls, *boundaries, (self.max_steps - self._elapsed) / self.max_steps)

    def step(self, action: int | Action):
        self._require_reset()
        if self._terminated or self._truncated:
            raise RuntimeError('Episode is complete; call reset before stepping again')
        if not (type(action) is int or isinstance(action, Action)) or not 0 <= action < len(Action):
            raise ValueError('action must be an integer from 0 to 4 (UP, DOWN, LEFT, RIGHT, WAIT)')
        action = Action(action)
        dr, dc = ACTION_DELTAS[action]
        requested = (self.position[0] + dr, self.position[1] + dc)
        components = {'step': -1.0, 'obstacle': 0.0, 'boundary': 0.0, 'goal': 0.0}
        self._executed_move = False
        if not self.graph.in_bounds(requested):
            components['boundary'] = -5.0
            self._boundary_attempts += 1
            self._event = 'boundary'
        elif requested in self.graph.obstacles:
            components['obstacle'] = -10.0
            self._obstacle_attempts += 1
            self._event = 'obstacle'
        elif action == Action.WAIT:
            self._event = 'wait'
        else:
            self._position = requested
            self._moves += 1
            self._path_cost += self.graph.cost(requested)
            self._executed_move = True
            self._event = 'move'
        self._elapsed += 1
        if self.position == self.goal:
            components['goal'] = 100.0
            self._terminated = True
            self._arrival_step = self._elapsed
            self._event = 'goal'
        # Goal arrival takes precedence over the horizon on the same turn.
        self._truncated = self._elapsed >= self.max_steps and not self._terminated
        reward = sum(components.values())
        self._episode_reward += reward
        self._components, self._action, self._requested_position = components, action, requested
        return self.observe(), reward, self._terminated, self._truncated, self._info()

    def _info(self):
        return {'position': self.position, 'start': self.start, 'goal': self.goal,
                'seed': self._seed, 'observation_version': OBSERVATION_VERSION,
                'elapsed_steps': self._elapsed, 'moves': self._moves, 'path_cost': self._path_cost,
                'episode_reward': self._episode_reward, 'arrival_step': self._arrival_step,
                'obstacle_attempts': self._obstacle_attempts, 'boundary_attempts': self._boundary_attempts,
                'terminated': self._terminated, 'truncated': self._truncated, 'success': self._terminated,
                'failure_reason': 'time_limit' if self._truncated else None,
                'event': self._event, 'action': None if self._action is None else self._action.name,
                'requested_position': self._requested_position, 'executed_move': self._executed_move,
                'reward_components': dict(self._components)}
