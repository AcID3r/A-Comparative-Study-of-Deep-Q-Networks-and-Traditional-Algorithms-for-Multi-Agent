"""Classical replanning, frozen-route control and common environment rollouts."""

from time import perf_counter
from algorithms.astar import astar_result
from algorithms.bfs import bfs_result
from algorithms.dijkstra import dijkstra_result
from environments.single_agent_env import Action, ACTION_DELTAS

SEARCHES = {'bfs': bfs_result, 'dijkstra': dijkstra_result, 'astar': astar_result}
BY_DELTA = {delta: Action(i) for i, delta in enumerate(ACTION_DELTAS[:4])}


class SearchController:
    def __init__(self, env, algorithm='astar', *, frozen=False):
        self.env, self.search, self.frozen = env, SEARCHES[algorithm], frozen
        self.version = None
        self.route = None
        self.planning_seconds = 0.0
        self.expanded_nodes = self.plan_calls = 0
        if frozen:
            self._plan(None)

    def _plan(self, version):
        start = self.env.start if self.version is None and self.frozen else self.env.position
        result = self.search(self.env.graph, start, self.env.goal)
        self.route = result.path[1:] if result.path else []
        self.version = version
        self.plan_calls += 1
        self.expanded_nodes += result.expanded_nodes
        self.planning_seconds += result.planning_time_seconds

    def act(self, observation, *, epsilon=0):
        version = getattr(self.env, '_graph_version', 0)
        if not self.frozen and (self.version is None or self.version != version):
            self._plan(version)
        while self.route and self.route[0] == self.env.position:
            self.route.pop(0)
        if not self.route:
            return Action.WAIT
        target = self.route[0]
        delta = (target[0] - self.env.position[0], target[1] - self.env.position[1])
        return BY_DELTA[delta]


def rollout(controller, env, *, seed=0):
    started = perf_counter()
    observation, info = env.reset(seed=seed)
    initial_observation = observation
    transitions = []
    decision_seconds = 0.0
    while not (info['terminated'] or info['truncated']):
        action_started = perf_counter()
        action = int(controller.act(observation, epsilon=0))
        decision_seconds += perf_counter() - action_started
        following, reward, terminated, truncated, info = env.step(action)
        transitions.append({'observation': observation, 'action': action, 'reward': reward,
            'next_observation': following, 'position': info['position'],
            'reward_components': info['reward_components'],
            'action_graph_version': info.get('action_graph_version', 0)})
        observation = following
    return {'initial_observation': initial_observation, 'transitions': transitions, 'final_info': info,
            'decision_time_seconds': decision_seconds, 'episode_time_seconds': perf_counter() - started,
            'planning_time_seconds': getattr(controller, 'planning_seconds', 0.0),
            'expanded_nodes': getattr(controller, 'expanded_nodes', None),
            'plan_calls': getattr(controller, 'plan_calls', 0)}
