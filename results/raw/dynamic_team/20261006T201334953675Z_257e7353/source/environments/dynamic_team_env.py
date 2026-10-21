"""Scheduled team graph snapshots; preserve the static v2 observation/reward API."""
from dataclasses import asdict
from copy import deepcopy
from environments.grid_graph import GridGraph
from environments.dynamic_env import ObstacleChange
from environments.multi_agent_env import MultiAgentEnv
from environments.single_agent_env import Action


class DynamicTeamEnv(MultiAgentEnv):
    def __init__(self, graph, starts, goals, *, max_steps=100, schedule=()):
        super().__init__(graph,starts,goals,max_steps=max_steps)
        self._initial_graph = graph
        changes = tuple(schedule)
        if any(not isinstance(e,ObstacleChange) for e in changes):
            raise ValueError('Schedule must contain ObstacleChange objects')
        if len({(e.tick,e.position) for e in changes}) != len(changes):
            raise ValueError('Only one change per cell/tick is allowed')
        for e in changes:
            if not graph.in_bounds(e.position) or e.position in self.starts+self.goals or e.tick > max_steps:
                raise ValueError('Schedule must protect all endpoints and respect bounds/horizon')
        self.schedule = tuple(sorted(changes,key=lambda e:(e.tick,e.position)))

    def reset(self, *, seed=None):
        if seed is not None and (type(seed) is not int or seed < 0):
            raise ValueError('seed must be nonnegative or None')
        self.graph = self._initial_graph
        self._graph_version = self._prepared_tick = 0
        self._action_graph_version = None
        self._history = []
        return super().reset(seed=seed)

    def _prepare(self):
        self._require_reset()
        if self._terminated or self._truncated: return
        tick = self._elapsed+1
        if self._prepared_tick == tick: return
        for event in self.schedule:
            if event.tick != tick: continue
            walls = set(self.graph.obstacles)
            if event.operation == 'add' and event.position in self.positions:
                status = 'rejected_occupied'
            elif (event.position in walls) == (event.operation == 'add'):
                status = 'no_change'
            else:
                if event.operation == 'add': walls.add(event.position)
                else: walls.remove(event.position)
                self.graph = GridGraph(self.graph.rows,self.graph.cols,walls)
                self._graph_version += 1
                status = 'applied'
            self._history.append(asdict(event)|{'status':status,'graph_version':self._graph_version})
        self._prepared_tick = tick

    def observe(self):
        self._prepare()
        return super().observe()

    def step(self,actions):
        self._require_reset()
        if self._terminated or self._truncated:
            raise RuntimeError('Episode complete; reset first')
        if not isinstance(actions,(tuple,list)) or len(actions) != self.n_agents or any(
            not (type(a) is int or isinstance(a,Action)) or not 0 <= a < 5 for a in actions):
            raise ValueError('Every agent needs one integer action 0..4')
        self._action_graph_version = self._graph_version
        return super().step(actions)

    def info(self):
        return super().info()|{'graph_version':self._graph_version,'action_graph_version':self._action_graph_version,
            'prepared_tick':self._prepared_tick,'change_history':deepcopy(self._history)}
