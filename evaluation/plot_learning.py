"""Generate learning figures from recorded training CSV, without editing data."""

import csv
import os
from pathlib import Path


def plot_run(directory, window):
    os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / '.cache' / 'matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory = Path(directory)
    with (directory / 'training_episodes.csv').open(newline='', encoding='utf-8') as file:
        rows = list(csv.DictReader(file))
    figures = directory / 'figures'
    figures.mkdir(exist_ok=True)
    panels = [('episode_reward', 'Training episode return', 'reward.png'),
              ('success', 'Training success fraction', 'success.png'),
              ('mean_loss', 'Mean episode MSE loss', 'loss.png')]
    for metric, ylabel, name in panels:
        fig, ax = plt.subplots(figsize=(9, 5), layout='constrained')
        for seed in sorted({r['seed'] for r in rows}, key=int):
            selected = [r for r in rows if r['seed'] == seed]
            values = [float(r[metric]) if r[metric] != '' else None for r in selected]
            smoothed = []
            for index in range(len(values)):
                valid = [v for v in values[max(0, index - window + 1):index + 1] if v is not None]
                smoothed.append(sum(valid) / len(valid) if valid else float('nan'))
            ax.plot([int(r['episode']) for r in selected], smoothed, label=f'Seed {seed}')
        ax.set(xlabel='Training episode', ylabel=ylabel, title=f'Fixed training map; trailing window {window}')
        ax.grid(alpha=.2)
        ax.legend()
        if metric == 'success':
            ax.set_ylim(-.02, 1.02)
        fig.savefig(figures / name, dpi=160)
        fig.savefig(figures / name.replace('.png', '.svg'))
        plt.close(fig)
