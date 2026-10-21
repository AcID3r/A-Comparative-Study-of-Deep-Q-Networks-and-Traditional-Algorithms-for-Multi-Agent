"""CPU DQN with independent replay RNG and finite-horizon Bellman targets."""

from dataclasses import asdict, dataclass
from math import isfinite
from numbers import Real
from pathlib import Path
import random

import torch
from torch import nn
from environments.single_agent_env import Action, OBSERVATION_FEATURES, OBSERVATION_VERSION


def observation_features(version):
    if type(version) is not int or version not in (1, 2):
        raise ValueError('Observation version must be 1 or 2')
    if version == 1:
        return OBSERVATION_FEATURES
    from environments.multi_agent_env import OBSERVATION_FEATURES as team_features
    return team_features


def positive_integer(value, name):
    if type(value) is not int or value <= 0:
        raise ValueError(f'{name} must be a positive integer')


def finite_number(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f'{name} must be a finite number')


def check_observation(observation, version=1):
    values = tuple(observation)
    if len(values) != len(observation_features(version)):
        raise ValueError('Observation must match its versioned feature layout')
    for value in values:
        finite_number(value, 'observation feature')
        if not -1 <= value <= 1:
            raise ValueError('Observation features must be normalized to [-1, 1]')
    return tuple(float(value) for value in values)


@dataclass(frozen=True)
class Transition:
    observation: tuple[float, ...]
    action: int
    reward: float
    next_observation: tuple[float, ...]
    terminated: bool
    truncated: bool
    observation_version: int = 1

    def __post_init__(self):
        object.__setattr__(self, 'observation', check_observation(self.observation, self.observation_version))
        object.__setattr__(self, 'next_observation', check_observation(self.next_observation, self.observation_version))
        if not (type(self.action) is int or isinstance(self.action, Action)) or not 0 <= self.action < len(Action):
            raise ValueError('Invalid action')
        finite_number(self.reward, 'reward')
        if type(self.terminated) is not bool or type(self.truncated) is not bool or (self.terminated and self.truncated):
            raise ValueError('Termination flags must be separate Booleans, not simultaneously true')


class ReplayBuffer:
    def __init__(self, capacity: int, *, seed: int = 0):
        positive_integer(capacity, 'capacity')
        self.capacity = capacity
        self._items = []
        self._next = 0
        self._rng = random.Random(seed)

    def __len__(self):
        return len(self._items)

    def append(self, transition: Transition):
        if not isinstance(transition, Transition):
            raise ValueError('Replay expects a Transition')
        if len(self._items) < self.capacity:
            self._items.append(transition)
        else:
            self._items[self._next] = transition
        self._next = (self._next + 1) % self.capacity

    def sample(self, count: int):
        positive_integer(count, 'sample count')
        if count > len(self):
            raise ValueError('Not enough transitions to sample without replacement')
        return self._rng.sample(self._items, count)


@dataclass(frozen=True)
class DQNConfig:
    hidden_sizes: tuple[int, int] = (128, 128)
    learning_rate: float = .001
    gamma: float = .99
    target_update_steps: int = 500
    gradient_clip: float = 10.0

    def __post_init__(self):
        hidden = tuple(self.hidden_sizes)
        if len(hidden) != 2:
            raise ValueError('Exactly two hidden layers are required')
        for size in hidden:
            positive_integer(size, 'hidden size')
        object.__setattr__(self, 'hidden_sizes', hidden)
        for name in ('learning_rate', 'gamma', 'gradient_clip'):
            finite_number(getattr(self, name), name)
        if self.learning_rate <= 0 or self.gradient_clip <= 0 or not 0 <= self.gamma <= 1:
            raise ValueError('Invalid learning rate, gradient limit, or discount')
        positive_integer(self.target_update_steps, 'target update steps')


def epsilon_at(episode_index, initial, final, decay_episodes):
    if type(episode_index) is not int or episode_index < 0:
        raise ValueError('Episode index must be a nonnegative integer')
    positive_integer(decay_episodes, 'epsilon decay episodes')
    finite_number(initial, 'initial epsilon')
    finite_number(final, 'final epsilon')
    if not 0 <= final <= initial <= 1:
        raise ValueError('Epsilon must decay within [0,1]')
    if episode_index >= decay_episodes:
        return float(final)
    return initial + (final - initial) * episode_index / decay_episodes


@torch.no_grad()
def bellman_targets(rewards, terminated, truncated, next_q_values, gamma):
    done = terminated | truncated
    future = next_q_values.max(dim=1).values
    return rewards + gamma * torch.where(done, torch.zeros_like(future), future)


class DQNAgent:
    def __init__(self, config: DQNConfig | None = None, *, seed: int = 0, observation_version=1):
        if type(seed) is not int or seed < 0:
            raise ValueError('Seed must be a nonnegative integer')
        self.config = config or DQNConfig()
        self.seed = seed
        self.observation_version = observation_version
        input_size = len(observation_features(observation_version))
        self._rng = random.Random(seed)
        # Avoid changing caller's global torch RNG during seeded initialization.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(seed)
            a, b = self.config.hidden_sizes
            self.online = nn.Sequential(nn.Linear(input_size, a), nn.ReLU(), nn.Linear(a, b), nn.ReLU(), nn.Linear(b, 5))
            self.target = nn.Sequential(nn.Linear(input_size, a), nn.ReLU(), nn.Linear(a, b), nn.ReLU(), nn.Linear(b, 5))
        self.target.load_state_dict(self.online.state_dict())
        self.target.requires_grad_(False)
        self.target.eval()
        self.optimizer = torch.optim.Adam(self.online.parameters(), lr=self.config.learning_rate)
        self.updates = 0

    @torch.no_grad()
    def q_values(self, observation):
        values = check_observation(observation, self.observation_version)
        self.online.eval()
        return self.online(torch.tensor(values, dtype=torch.float32))

    def act(self, observation, *, epsilon=0.0):
        finite_number(epsilon, 'epsilon')
        if not 0 <= epsilon <= 1:
            raise ValueError('Epsilon must be in [0,1]')
        observation = check_observation(observation, self.observation_version)
        # Greedy evaluation does not consume exploration RNG state.
        if epsilon > 0 and self._rng.random() < epsilon:
            return self._rng.randrange(5)
        return int(self.q_values(observation).argmax().item())

    def train_batch(self, batch):
        if not batch or any(not isinstance(t, Transition) for t in batch):
            raise ValueError('Batch must contain transitions')
        if any(t.observation_version != self.observation_version for t in batch):
            raise ValueError('Batch layout does not match model observation version')
        states = torch.tensor([t.observation for t in batch], dtype=torch.float32)
        following = torch.tensor([t.next_observation for t in batch], dtype=torch.float32)
        actions = torch.tensor([t.action for t in batch], dtype=torch.int64)
        rewards = torch.tensor([t.reward for t in batch], dtype=torch.float32)
        terminated = torch.tensor([t.terminated for t in batch], dtype=torch.bool)
        truncated = torch.tensor([t.truncated for t in batch], dtype=torch.bool)
        self.online.train()
        predicted = self.online(states).gather(1, actions[:, None]).squeeze(1)
        targets = bellman_targets(rewards, terminated, truncated, self.target(following), self.config.gamma)
        loss = nn.functional.mse_loss(predicted, targets)
        if not torch.isfinite(loss):
            raise RuntimeError('Training produced a nonfinite loss')
        self.optimizer.zero_grad(set_to_none=True)
        loss.backward()
        norm = nn.utils.clip_grad_norm_(self.online.parameters(), self.config.gradient_clip, error_if_nonfinite=True)
        self.optimizer.step()
        self.updates += 1
        synced = self.updates % self.config.target_update_steps == 0
        if synced:
            self.target.load_state_dict(self.online.state_dict())
        return {'loss': float(loss.item()), 'gradient_norm_before_clip': float(norm.item()), 'target_synced': synced}

    def save(self, path, *, metadata=None):
        payload = {'checkpoint_version': 1, 'observation_version': self.observation_version,
                   'observation_features': list(observation_features(self.observation_version)), 'actions': [a.name for a in Action],
                   'config': asdict(self.config), 'seed': self.seed, 'updates': self.updates,
                   'online': self.online.state_dict(), 'target': self.target.state_dict(),
                   'metadata': metadata or {}}
        with Path(path).open('xb') as file:
            torch.save(payload, file)

    @classmethod
    def load(cls, path):
        payload = torch.load(path, map_location='cpu', weights_only=True)
        if (payload['checkpoint_version'] != 1
                or payload['observation_features'] != list(observation_features(payload['observation_version']))
                or payload['actions'] != [a.name for a in Action]):
            raise ValueError('Checkpoint observation or action layout is incompatible')
        agent = cls(DQNConfig(**payload['config']), seed=payload['seed'], observation_version=payload['observation_version'])
        agent.online.load_state_dict(payload['online'])
        agent.target.load_state_dict(payload['target'])
        agent.updates = payload['updates']
        agent.online.eval()
        return agent, payload['metadata']
