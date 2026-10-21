"""Replay team correctness traces and verify static plan results."""
import argparse
import hashlib
import json
from pathlib import Path
from algorithms.prioritized import prioritized_plan, plan_actions
from environments.grid_graph import GridGraph
from environments.multi_agent_env import MultiAgentEnv


def canonical(value):
    return json.loads(json.dumps(value))


def audit(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    root = Path(__file__).resolve().parents[1]
    for name, digest in data['source_hashes'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == digest, name
    steps = successes = failures = 0
    for case in data['cases']:
        graph = GridGraph(case['rows'],case['cols'])
        starts = tuple(map(tuple,case['starts']))
        goals = tuple(map(tuple,case['goals']))
        if case['method'] != 'script':
            plan = prioritized_plan(graph,starts,goals,method=case['method'],max_steps=case['max_steps'],priority=case['priority'])
            assert plan.success == case['planning_success']
            assert canonical(plan.paths) == case['paths']
            assert plan.failed_agent == case['failed_agent']
            assert plan.failure_reason == case['failure_reason']
            assert plan.expanded_nodes == case['expanded_nodes']
            assert case['planning_time_seconds'] >= 0
            if not plan.success:
                assert not case['steps']
                failures += 1
                continue
        env = MultiAgentEnv(graph,starts,goals,max_steps=case['max_steps'])
        obs, info = env.reset(seed=0)
        assert canonical({'observations':obs,'info':info}) == case['reset']
        for tick, recorded in enumerate(case['steps']):
            if case['method'] != 'script':
                assert list(plan_actions(plan.paths,tick)) == recorded['actions']
            previous = env.positions
            obs,rewards,term,trunc,info = env.step(recorded['actions'])
            assert canonical({'actions':recorded['actions'],'observations':obs,'rewards':rewards,
                              'terminated':term,'truncated':trunc,'info':info}) == recorded
            assert len(set(env.positions)) == len(starts)
            for i in range(len(starts)):
                for j in range(i):
                    assert not (env.positions[i] == previous[j] and env.positions[j] == previous[i])
            assert all(reward == sum(parts.values()) for reward,parts in zip(rewards,info['reward_components']))
            steps += 1
        assert canonical(info) == case['final_info']
        assert info['terminated'] or info['truncated']
        assert info['actual_collisions'] == 0
        successes += info['success']
    return {'cases':len(data['cases']), 'steps_replayed':steps, 'successful_episodes':successes,
            'planning_failures':failures,'all_traces_replayed':True,'source_hashes_match':True,'actual_collisions':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace',type=Path)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    result = audit(args.trace)
    if args.output:
        with args.output.open('x',encoding='utf-8') as f:
            json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
