#!/usr/bin/env python3
"""Plot mean added burned area by budget for each policy family in a benchmark report.

PPO seeds are averaged into one line per family (frozen base, each fine-tune), with a
band spanning the per-seed means. The figure is a simulator comparison only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics


def family(policy: str) -> str:
    match = re.fullmatch(r"(base|ft-b\d+)-s\d+", policy)
    if not match:
        return policy
    return "frozen base (B=2)" if match.group(1) == "base" else "fine-tuned B=%s" % match.group(1)[4:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads(args.report.read_text(encoding="utf-8"))
    per_policy = {}
    for row in report["episodes"]:
        per_policy.setdefault(row["policy"], {}).setdefault(row["budget"], []).append(row["added_burned_ha"])
    budgets = sorted({row["budget"] for row in report["episodes"]})
    families = {}
    for policy, by_budget in per_policy.items():
        means = [statistics.fmean(by_budget[b]) for b in budgets]
        families.setdefault(family(policy), []).append(means)

    figure, axis = plt.subplots(figsize=(7.5, 4.5), dpi=150)
    for name in sorted(families):
        runs = families[name]
        mean = [statistics.fmean(values) for values in zip(*runs)]
        (line,) = axis.plot(budgets, mean, marker="o",
                            label="%s (n=%d)" % (name, len(runs)) if len(runs) > 1 else name)
        if len(runs) > 1:
            low = [min(values) for values in zip(*runs)]
            high = [max(values) for values in zip(*runs)]
            axis.fill_between(budgets, low, high, alpha=0.08, color=line.get_color())
    axis.set_xticks(budgets)
    axis.set_xlabel("crew-shift budget per 48 h episode")
    axis.set_ylabel("mean added burned area (ha)")
    axis.set_title("SimFire %s cases, %s setting (simulator only)" % (
        report["split"].upper(), report.get("params_gate_status")))
    axis.grid(alpha=0.3)
    axis.legend(fontsize=7, ncol=2)
    figure.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.out)
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
