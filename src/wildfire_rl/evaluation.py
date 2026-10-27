"""Paired synthetic experiments and reproducibility manifests (stdlib only)."""

import csv
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import platform
import random
from statistics import fmean
import subprocess
from time import perf_counter

from .policies import POLICIES, choose_action
from .simulator import GridFire, Scenario


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                             allow_nan=False).encode()).hexdigest()


def validate_config(config):
    expected = {'schema_version', 'label', 'backend', 'scenario', 'budgets', 'seeds', 'policies'}
    if set(config) != expected or config['schema_version'] != 1:
        raise ValueError('config must match schema_version 1 fields')
    if config['backend'] != 'synthetic-v1':
        raise ValueError('only synthetic-v1 is implemented')
    if not isinstance(config['label'], str) or not config['label'].strip():
        raise ValueError('label must be nonempty')
    for key in ('budgets', 'seeds'):
        values = config[key]
        if not isinstance(values, list) or not values or any(
            type(v) is not int or v < 0 for v in values
        ) or len(set(values)) != len(values):
            raise ValueError(f'{key} must contain distinct nonnegative integers')
    policies = config['policies']
    if (not isinstance(policies, list) or 'none' not in policies or
            any(p not in POLICIES for p in policies) or len(set(policies)) != len(policies)):
        raise ValueError('policies must be distinct known baselines including none')
    try:
        return Scenario(**config['scenario'])
    except TypeError as exc:
        raise ValueError(f'invalid scenario: {exc}') from exc


def evaluate(config):
    scenario = validate_config(config)
    rows = []
    scenario_hash = digest(asdict(scenario))
    for budget in config['budgets']:
        for seed in config['seeds']:
            for policy in config['policies']:
                start = perf_counter()
                env = GridFire(scenario, budget)
                env.reset(seed)
                policy_rng = random.Random(f'policy:{seed}')
                while not (env.terminated or env.truncated):
                    env.step(choose_action(env, policy, policy_rng))
                rows.append(dict(backend=config['backend'], scenario_sha256=scenario_hash,
                                 budget=budget, seed=seed, policy=policy, **env.metrics(),
                                 runtime_seconds=perf_counter() - start))
    return rows


def bootstrap_interval(values, resamples=2000):
    if len(values) < 2:
        return None, None
    rng = random.Random(0)
    means = sorted(fmean(rng.choices(values, k=len(values))) for _ in range(resamples))
    return means[int(.025 * (resamples - 1))], means[int(.975 * (resamples - 1))]


def summarize(rows):
    if not rows:
        raise ValueError('no episodes to summarize')
    contexts = {(r['backend'], r['scenario_sha256']) for r in rows}
    if len(contexts) != 1:
        raise ValueError('cannot pool different backends or scenarios')
    indexed = {}
    groups = {}
    for row in rows:
        key = (row['budget'], row['seed'], row['policy'])
        if key in indexed:
            raise ValueError('duplicate episode')
        indexed[key] = row
        groups.setdefault((row['budget'], row['policy']), []).append(row)
    summaries = []
    for (budget, policy), group in sorted(groups.items()):
        reference = groups.get((budget, 'none'), [])
        if not reference or {r['seed'] for r in group} != {r['seed'] for r in reference}:
            raise ValueError('each policy needs exactly the same seeds as the none control')
        damage = [r['burned_fraction'] for r in group]
        saved = [indexed[budget, r['seed'], 'none']['burned_fraction'] -
                 r['burned_fraction'] for r in group]
        damage_lo, damage_hi = bootstrap_interval(damage)
        saved_lo, saved_hi = bootstrap_interval(saved)
        summaries.append(dict(budget=budget, policy=policy, episodes=len(group),
                              burned_fraction_mean=fmean(damage),
                              burned_fraction_ci95_low=damage_lo,
                              burned_fraction_ci95_high=damage_hi,
                              priority_burned_fraction_mean=fmean(
                                  r['priority_burned_fraction'] for r in group),
                              saved_fraction_mean=fmean(saved),
                              saved_fraction_ci95_low=saved_lo, saved_fraction_ci95_high=saved_hi,
                              interventions_mean=fmean(r['interventions'] for r in group),
                              truncation_rate=fmean(r['truncated'] for r in group),
                              runtime_seconds_mean=fmean(r['runtime_seconds'] for r in group)))
    return summaries


def budget_plot(summary):
    colors = ['#475569', '#dc2626', '#2563eb', '#16a34a', '#9333ea']
    max_budget = max(1, max(r['budget'] for r in summary))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="500" viewBox="0 0 840 500">',
             '<rect width="840" height="500" fill="white"/>',
             '<g font-family="sans-serif" font-size="14" fill="#172033">',
             '<text x="65" y="30" font-size="20">Synthetic pilot — technical validation only</text>',
             '<text x="65" y="52">Mean ever-burned fraction; 95% seed bootstrap intervals</text>']
    for tick in range(6):
        y = 400 - tick * 64
        parts.extend([f'<path d="M65 {y} H625" stroke="#e2e8f0"/>',
                      f'<text x="22" y="{y+5}">{tick/5:.1f}</text>'])
    for budget in sorted({r['budget'] for r in summary}):
        x = 65 + 560 * budget / max_budget
        parts.append(f'<text x="{x}" y="425" text-anchor="middle">{budget}</text>')
    for n, policy in enumerate(sorted({r['policy'] for r in summary})):
        color = colors[n % len(colors)]
        points = []
        for row in sorted((r for r in summary if r['policy'] == policy), key=lambda r: r['budget']):
            x = 65 + 560 * row['budget'] / max_budget
            y = 400 - 320 * row['burned_fraction_mean']
            points.append(f'{x},{y}')
            if row['burned_fraction_ci95_low'] is not None:
                low = 400 - 320 * row['burned_fraction_ci95_low']
                high = 400 - 320 * row['burned_fraction_ci95_high']
                parts.append(f'<path d="M{x} {low} V{high}" stroke="{color}" opacity=".5"/>')
            parts.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}"/>')
        parts.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="650" y="{100+n*28}" fill="{color}">{escape(policy)}</text>')
    parts += ['<text x="345" y="458" text-anchor="middle">Intervention budget (cells)</text>',
              '<text x="65" y="485" font-size="12">Not Cell2Fire. No RL comparison. One synthetic layout; intervals do not cover model or map uncertainty.</text>',
              '</g></svg>']
    return '\n'.join(parts)


def source_metadata():
    source = Path(__file__).parent
    h = sha256()
    for path in sorted(source.glob('*.py')):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    def git(*args):
        try:
            return subprocess.check_output(['git', *args], cwd=source, stderr=subprocess.DEVNULL,
                                           text=True).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    return dict(source_sha256=h.hexdigest(), git_commit=git('rev-parse', 'HEAD'),
                git_dirty=bool(git('status', '--porcelain')), python=platform.python_version(),
                platform=platform.platform())


def write_run(config, out):
    out = Path(out)
    if out.exists():
        raise FileExistsError(f'output already exists: {out}')
    rows = evaluate(config)
    summary = summarize(rows)
    manifest = dict(schema_version=1, label='SYNTHETIC PILOT — not research evidence',
                    created_utc=datetime.now(timezone.utc).isoformat(), config=config,
                    config_sha256=digest(config), **source_metadata())
    out.mkdir(parents=True, exist_ok=False)
    for name, records in [('episodes', rows), ('summary', summary)]:
        with (out / f'{name}.csv').open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (out / 'budget_damage.svg').write_text(budget_plot(summary))
    return manifest
