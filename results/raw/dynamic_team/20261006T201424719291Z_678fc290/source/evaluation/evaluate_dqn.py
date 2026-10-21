"""Greedy finite-horizon rollout; training and action times remain separate."""

from time import perf_counter
from environments.single_agent_env import SingleAgentEnv


def evaluate_agent(agent, env: SingleAgentEnv, *, seed=0):
    episode_started = perf_counter()
    observation, info = env.reset(seed=seed)
    initial = info['position']
    actions, observations, positions = [], [observation], [initial]
    inference_seconds = 0.0
    while not (info['terminated'] or info['truncated']):
        started = perf_counter()
        action = agent.act(observation, epsilon=0)
        inference_seconds += perf_counter() - started
        observation, _, _, _, info = env.step(action)
        actions.append(action)
        observations.append(observation)
        positions.append(info['position'])
    return {'success': info['success'], 'terminated': info['terminated'], 'truncated': info['truncated'],
            'failure_reason': info['failure_reason'], 'episode_reward': info['episode_reward'],
            'elapsed_steps': info['elapsed_steps'], 'moves': info['moves'], 'path_cost': info['path_cost'],
            'arrival_step': info['arrival_step'], 'obstacle_attempts': info['obstacle_attempts'],
            'boundary_attempts': info['boundary_attempts'], 'inference_time_seconds': inference_seconds,
            'episode_time_seconds': perf_counter() - episode_started, 'actions': actions,
            'positions': positions, 'observations': observations}
