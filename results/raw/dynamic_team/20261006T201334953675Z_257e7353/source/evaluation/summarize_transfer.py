"""Generate descriptive comparison tables/charts from measured transfer CSV."""

import argparse
import csv
import json
import os
from pathlib import Path
from statistics import mean, stdev
from evaluation.varied_protocol import ROOT


def summarize(directory, output):
    directory, output = Path(directory), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (directory / 'raw_results.csv').open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    groups = []
    for method in sorted({r['method'] for r in rows}):
        for condition in ('static', 'dynamic'):
            selected = [r for r in rows if r['method']==method and r['condition']==condition]
            seeds = sorted({r['training_seed'] for r in selected})
            rates = [sum(int(r['success']) for r in selected if r['training_seed']==s) / sum(r['training_seed']==s for r in selected) for s in seeds]
            succeeded = [r for r in selected if r['success']=='1']
            groups.append({'method': method, 'condition': condition, 'episodes': len(selected),
                'successes': len(succeeded), 'mean_seed_success_rate': mean(rates),
                'seed_success_rate_std': stdev(rates) if len(rates)>1 else None,
                'successful_mean_moves': mean(float(r['moves']) for r in succeeded) if succeeded else None,
                'successful_mean_arrival': mean(float(r['arrival_step']) for r in succeeded) if succeeded else None})
    (output / 'summary.json').write_text(json.dumps(groups, indent=2)+'\n', encoding='utf-8')
    lines = ['# Held-out transfer comparison', '', 'Generated from measured CSV. Success uses all test maps, including initially unreachable ones. Means of moves/arrival are successful episodes only. Seed standard deviation describes variation across trained models, not independent map uncertainty.', '', '| Method | Condition | Successes / episodes | Mean seed success | Seed std | Successful mean moves | Successful mean arrival |', '|---|---|---|---|---|---|---|']
    for g in groups:
        value = lambda key: f'{g[key]:.3f}' if g[key] is not None else 'n/a'
        lines.append(f"| {g['method']} | {g['condition']} | {g['successes']} / {g['episodes']} | {g['mean_seed_success_rate']:.1%} | {value('seed_success_rate_std')} | {value('successful_mean_moves')} | {value('successful_mean_arrival')} |")
    (output / 'comparison.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    methods = sorted({g['method'] for g in groups})
    fig, ax = plt.subplots(figsize=(11, 5), layout='constrained')
    for offset, condition, color in ((-.18, 'static', '#2563eb'), (.18, 'dynamic', '#d97706')):
        values = [next(g['mean_seed_success_rate'] for g in groups if g['method']==m and g['condition']==condition) for m in methods]
        ax.bar([i+offset for i in range(len(methods))], values, width=.34, label=condition, color=color)
    ax.set(xticks=range(len(methods)), xticklabels=methods, ylabel='Mean success rate across model seeds', ylim=(0, 1.05), title='Held-out 5x5 maps; all cases included')
    ax.tick_params(axis='x', rotation=20); ax.legend(); ax.grid(axis='y', alpha=.2)
    for suffix in ('png', 'svg'):
        fig.savefig(output / f'success_comparison.{suffix}', dpi=160)
    plt.close(fig)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(f'Generated analysis: {summarize(args.run_directory, args.output)}')


if __name__ == '__main__':
    main()
