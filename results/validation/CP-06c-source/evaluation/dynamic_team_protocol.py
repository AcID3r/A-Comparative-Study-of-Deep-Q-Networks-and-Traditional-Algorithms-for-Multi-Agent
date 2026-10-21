"""Matched schedules, current-map replanning and independently retried frozen routes."""
from dataclasses import asdict
from time import perf_counter
from algorithms.bfs import bfs
from algorithms.prioritized import prioritized_plan,plan_actions
from environments.dynamic_env import ObstacleChange
from environments.dynamic_team_env import DynamicTeamEnv
from environments.single_agent_env import ACTION_DELTAS
from evaluation.team_protocol import graph_for,environment


def team_schedule(scenario,add_tick=2,remove_tick=8):
    if type(add_tick) is not int or type(remove_tick) is not int or not 1 <= add_tick < remove_tick:
        raise ValueError('Schedule ticks must be increasing positive integers')
    graph = graph_for(scenario)
    starts = tuple(map(tuple,scenario['team_starts']))
    goals = tuple(map(tuple,scenario['team_goals']))
    candidates = []
    for start,goal in zip(starts,goals):
        path = bfs(graph,start,goal)
        if path: candidates.extend(path[1:-1])
    candidates.extend((r,c) for r in range(graph.rows) for c in range(graph.cols) if graph.is_free((r,c)))
    for p in candidates:
        if p not in starts+goals and min(abs(p[0]-s[0])+abs(p[1]-s[1]) for s in starts) >= add_tick:
            return (ObstacleChange(add_tick,p,'add'),ObstacleChange(remove_tick,p,'remove'))
    return ()


def make_env(scenario,horizon,n,condition,add_tick=2,remove_tick=8):
    if condition not in ('static','dynamic'): raise ValueError('Unknown condition')
    if condition == 'static': return environment(scenario,horizon,n)
    return DynamicTeamEnv(graph_for(scenario),tuple(map(tuple,scenario['team_starts'][:n])),
        tuple(map(tuple,scenario['team_goals'][:n])),max_steps=horizon,
        schedule=team_schedule(scenario,add_tick,remove_tick))


class TeamController:
    def __init__(self,env,method,frozen=False):
        if method not in ('bfs','dijkstra','astar'): raise ValueError('Unknown planning method')
        self.method,self.frozen = method,frozen
        self.calls = []
        self.plan = None
        self.version = None
        self.at_tick = 0
        self.expected = None
        self.cursors = [0]*env.n_agents
        if frozen:
            # Compute before reset prepares tick 1, on the original static map.
            self._compute(env,env.starts,0,0)

    def _compute(self,env,positions,elapsed,version):
        self.plan = prioritized_plan(env.graph,positions,env.goals,method=self.method,
                                    max_steps=env.max_steps-elapsed)
        self.at_tick,self.version = elapsed,version
        self.calls.append({'elapsed':elapsed,'graph_version':version,'positions':positions,
            'remaining_horizon':env.max_steps-elapsed,'success':self.plan.success,'paths':self.plan.paths,
            'failed_agent':self.plan.failed_agent,'failure_reason':self.plan.failure_reason,
            'expanded_nodes':self.plan.expanded_nodes,'seconds':self.plan.planning_time_seconds})

    def actions(self,env,info):
        elapsed,version = info['elapsed_steps'],info.get('graph_version',0)
        if not self.frozen:
            if self.plan is None or version != self.version or (self.expected is not None and env.positions != self.expected):
                self._compute(env,env.positions,elapsed,version)
            if not self.plan.success:
                self.expected = env.positions
                return (4,)*env.n_agents
            tick = elapsed-self.at_tick
            actions = plan_actions(self.plan.paths,tick)
            self.expected = tuple(p[min(tick+1,len(p)-1)] for p in self.plan.paths)
            return actions
        if not self.plan.success: return (4,)*env.n_agents
        actions = []
        for i,(path,pos) in enumerate(zip(self.plan.paths,env.positions)):
            cursor = self.cursors[i]
            if cursor+1 == len(path): actions.append(4)
            else:
                nxt = path[cursor+1]
                actions.append(ACTION_DELTAS.index((nxt[0]-pos[0],nxt[1]-pos[1])))
        return tuple(actions)

    def after_step(self,env):
        if self.frozen and self.plan.success:
            for i,path in enumerate(self.plan.paths):
                cursor = self.cursors[i]
                if cursor+1 < len(path) and env.positions[i] == path[cursor+1]:
                    self.cursors[i] += 1


def rollout(env,agent=None,method=None,frozen=False):
    began = perf_counter()
    controller = TeamController(env,method,frozen) if method else None
    obs,info = env.reset(seed=0)
    trace,decision = [],0.0
    while not (info['terminated'] or info['truncated']):
        before = obs
        started = perf_counter()
        planning_before = sum(c['seconds'] for c in controller.calls) if controller else 0
        actions = controller.actions(env,info) if controller else tuple(
            4 if arrival is not None else agent.act(o,epsilon=0) for o,arrival in zip(obs,info['arrival_steps']))
        action_seconds = perf_counter()-started
        # Planning has a separate timer; subtract its new calls from decisions.
        planning_after = sum(c['seconds'] for c in controller.calls) if controller else 0
        decision += max(0.0,action_seconds-(planning_after-planning_before))
        obs,rewards,term,trunc,info = env.step(actions)
        if controller: controller.after_step(env)
        trace.append({'observations':before,'actions':actions,'next_observations':obs,'rewards':rewards,
                      'terminated':term,'truncated':trunc,'info':info})
    calls = [] if controller is None else controller.calls
    return {'success':info['success'],'failure_reason':info['failure_reason'],'final_info':info,'trace':trace,
            'planning_calls':calls,'decision_seconds':decision,'planning_seconds':sum(c['seconds'] for c in calls),
            'episode_seconds':perf_counter()-began,'expanded_nodes':sum(c['expanded_nodes'] for c in calls),
            'plan_failures':sum(not c['success'] for c in calls)}
