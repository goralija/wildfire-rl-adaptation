#!/usr/bin/env python3
"""Scientific summary of the fixed development pilot; no learned-policy claim."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    policies = report["summary"]["policies"]
    names = list(policies)
    labels = [name.replace("_", " ") for name in names]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout="constrained")
    colors = ["#8c98a4", "#c5a251", "#167a72", "#6287ac", "#a379a2"]
    means = [100 * policies[name]["mean_saved_fraction"] for name in names]
    bars = axes[0].barh(labels, means, color=colors)
    axes[0].bar_label(bars, fmt="%.2f%%", padding=5, fontsize=10)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, max(means) * 1.25)
    axes[0].set_xlabel("Mean saved weighted damage (%)")
    axes[0].set_title("Fixed rules; matched no-op, line charge included")
    x = np.arange(3)
    for name, color in zip(names[1:], colors[1:]):
        y = [100 * policies[name]["by_roster"][b] for b in ("B2", "B3", "B4")]
        axes[1].plot(x, y, marker="o", label=name.replace("_", " "), color=color)
    axes[1].set_xticks(x, ["2 units", "3 units", "4 units"])
    axes[1].set_ylabel("Mean saved weighted damage (%)")
    axes[1].set_title("Nested resource rosters, same 16 fires")
    axes[1].legend(frameon=False, fontsize=9)
    for axis in axes:
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="x" if axis is axes[0] else "y", alpha=.15)
        axis.set_axisbelow(True)
    fig.suptitle("Controlled CA development pilot — 16 procedural fires, 240 episodes",
                 fontsize=13)
    fig.supxlabel("Simulator-only, descriptive. direct flank: 20 close calls / 0 unit losses; no RL model evaluated.",
                  fontsize=9)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
