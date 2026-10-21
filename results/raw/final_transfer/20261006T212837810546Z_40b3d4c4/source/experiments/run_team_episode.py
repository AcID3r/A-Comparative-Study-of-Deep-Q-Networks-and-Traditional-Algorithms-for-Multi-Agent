"""Save scripted team correctness traces, separate from research measurements."""
import argparse
import hashlib
import json
from pathlib import Path
from algorithms.prioritized import prioritized_plan, plan_actions
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('environments/grid_graph.py', 'environments/single_agent_env.py',
           'environments/multi_agent_env.py', 'algorithms/prioritized.py',
           'experiments/run_team_episode.py')


def generate():
    cases = []
    scenarios = (
        ('wait', 2,3, ((0,0),(1,1)), ((0,2),(0,1)), 5, None),
        ('four_lanes', 4,4, ((0,0),(1,0),(2,0),(3,0)), ((0,3),(1,3),(2,3),(3,3)), 6, None),
        ('blocked_goal', 1,3, ((0,0),(0,2)), ((0,1),(0,0)), 8, None),
        ('priority_default', 2,3, ((0,0),(1,0)), ((1,2),(1,1)), 8, None),
        ('priority_reverse', 2,3, ((0,0),(1,0)), ((1,2),(1,1)), 8, (1,0)),
    )
    for name, rows, cols, starts, goals, horizon, priority in scenarios:
        for method in ('bfs','dijkstra','astar'):
            graph = GridGraph(rows, cols)
            plan = prioritized_plan(graph, starts, goals, method=method, max_steps=horizon, priority=priority)
            case = {'name':name, 'method':method, 'rows':rows, 'cols':cols, 'starts':starts,
                    'goals':goals, 'max_steps':horizon, 'priority':plan.priority,
                    'planning_success':plan.success, 'paths':plan.paths, 'failed_agent':plan.failed_agent,
                    'failure_reason':plan.failure_reason, 'expanded_nodes':plan.expanded_nodes,
                    'planning_time_seconds':plan.planning_time_seconds, 'steps':[]}
            if plan.success:
                env = MultiAgentEnv(graph, starts, goals, max_steps=horizon)
                obs, info = env.reset(seed=0)
                case['reset'] = {'observations':obs, 'info':info}
                for tick in range(horizon):
                    if info['success']: break
                    actions = plan_actions(plan.paths, tick)
                    obs, rewards, term, trunc, info = env.step(actions)
                    case['steps'].append({'actions':actions, 'observations':obs, 'rewards':rewards,
                                          'terminated':term, 'truncated':trunc, 'info':info})
                case['final_info'] = info
            cases.append(case)
    env = MultiAgentEnv(GridGraph(2,3), ((1,0),(1,2)), ((0,0),(0,2)), max_steps=2)
    obs, info = env.reset(seed=0)
    case = {'name':'conflict_then_timeout', 'method':'script', 'rows':2,'cols':3,
            'starts':env.starts,'goals':env.goals,'max_steps':2,
            'reset':{'observations':obs,'info':info},'steps':[]}
    for actions in ((3,2),(4,4)):
        obs, rewards, term, trunc, info = env.step(actions)
        case['steps'].append({'actions':actions,'observations':obs,'rewards':rewards,
                             'terminated':term,'truncated':trunc,'info':info})
    case['final_info'] = info
    cases.append(case)
    return {'purpose':'correctness_demonstration_not_research', 'observation_version':2,
            'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}, 'cases':cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    data = generate()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x',encoding='utf-8') as f:
            json.dump(data,f,indent=2); f.write('\n')
    for c in data['cases']:
        result = c.get('final_info')
        print(c['name'], c['method'], 'planning_failed' if result is None else
              f"success={result['success']} ticks={result['elapsed_steps']} moves={result['total_moves']} conflicts={sum(result['conflict_attempts'])}")


if __name__ == '__main__': main()
