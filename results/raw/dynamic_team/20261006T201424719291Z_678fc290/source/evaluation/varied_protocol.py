"""Shared frozen CP-05 configuration, split generation, and source snapshots."""

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
from uuid import uuid4
from algorithms.dqn import DQNConfig, epsilon_at, positive_integer
from environments.random_maps import build_bank, map_id

ROOT = Path(__file__).resolve().parents[1]


def fixed_directory(config):
    path = Path(config['fixed_run'])
    return path if path.is_absolute() else ROOT / path


def validate_config(config):
    expected = {'schema_version', 'purpose', 'map_spec', 'partitions', 'seeds', 'episodes', 'batch_size',
                'replay_capacity', 'warmup_steps', 'train_every_steps', 'epsilon_initial', 'epsilon_final',
                'epsilon_decay_episodes', 'evaluate_every_episodes', 'rolling_window', 'network', 'fixed_run'}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError('Unexpected varied-map config fields')
    if type(config['schema_version']) is not int or config['schema_version'] != 1 or config['purpose'] not in ('random_map_development', 'random_map_smoke'):
        raise ValueError('Unsupported varied-map config version/purpose')
    for key in ('episodes', 'batch_size', 'replay_capacity', 'warmup_steps', 'train_every_steps',
                'epsilon_decay_episodes', 'evaluate_every_episodes', 'rolling_window'):
        positive_integer(config[key], key)
    if config['warmup_steps'] < config['batch_size'] or config['batch_size'] > config['replay_capacity']:
        raise ValueError('Replay and warm-up must accommodate batches')
    if not isinstance(config['seeds'], list) or not config['seeds'] or any(type(s) is not int or s < 0 for s in config['seeds']) or len(set(config['seeds'])) != len(config['seeds']):
        raise ValueError('Seeds must be distinct nonnegative integers')
    if not isinstance(config['partitions'], dict) or list(config['partitions']) != ['train', 'validation', 'test']:
        raise ValueError('Partition order must be train, validation, test')
    for value in config['partitions'].values():
        if not isinstance(value, list) or len(value) != 2 or type(value[0]) is not int or value[0] < 0:
            raise ValueError('Partition values must be [first_seed, count]')
        positive_integer(value[1], 'partition count')
    if not isinstance(config['map_spec'], dict) or set(config['map_spec']) != {'rows', 'cols', 'density', 'max_steps'}:
        raise ValueError('Unexpected map specification fields')
    for name in ('rows', 'cols', 'max_steps'):
        positive_integer(config['map_spec'][name], name)
    if config['map_spec']['max_steps'] < 8:
        raise ValueError('The dynamic development protocol needs at least eight turns')
    epsilon_at(0, config['epsilon_initial'], config['epsilon_final'], config['epsilon_decay_episodes'])
    DQNConfig(**config['network'])
    if not isinstance(config['fixed_run'], str) or not (fixed_directory(config) / 'COMPLETE.json').is_file():
        raise ValueError('A completed fixed-map reference run is required')


def generate_bank(config):
    validate_config(config)
    fixed_map = json.loads((fixed_directory(config) / 'config.json').read_text(encoding='utf-8'))['map']
    excluded = [map_id(fixed_map['rows'], fixed_map['cols'], fixed_map['obstacles'])]
    spec = config['map_spec']
    return build_bank(spec['rows'], spec['cols'], spec['density'], config['partitions'], excluded_ids=excluded)


def new_run(output_root, config, bank, purpose):
    stamp = datetime.now(timezone.utc)
    directory = Path(output_root) / (stamp.strftime('%Y%m%dT%H%M%S%fZ') + '_' + uuid4().hex[:8])
    directory.mkdir(parents=True, exist_ok=False)
    (directory / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
    (directory / 'map_bank.json').write_text(json.dumps(bank, indent=2) + '\n', encoding='utf-8')
    files = [*ROOT.joinpath('algorithms').glob('*.py'), *ROOT.joinpath('environments').glob('*.py'),
             *ROOT.joinpath('evaluation').glob('*.py'), *ROOT.joinpath('training').glob('*.py'),
             *ROOT.joinpath('experiments').glob('*.py')]
    snapshot = directory / 'source'
    hashes = {}
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = path.read_bytes()
        destination.write_bytes(content)
        hashes[relative.as_posix()] = hashlib.sha256(content).hexdigest()
    metadata = {'purpose': purpose, 'created_at_utc': stamp.isoformat(), 'python': sys.version,
                'platform': platform.platform(), 'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
                'versions': {name: importlib.metadata.version(name) for name in ('torch', 'numpy', 'matplotlib')},
                'device': 'cpu', 'torch_threads': 1, 'source_sha256': hashes,
                'split_rules': 'unique geometry across all partitions; CP-04 training geometry excluded; no reachability filtering',
                'dynamic_rules': 'add at tick 3 at start-distance >=3; remove same cell at tick 8; unchanged observations v1',
                'limitations': 'small 5x5 development; fixed endpoints; one rollout per map/model/condition; no online updates at evaluation'}
    (directory / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    return directory
