#!/usr/bin/env python3
"""Plot exploratory OOF gains, separately for the two line accounting rules."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    report = json.loads(args.analysis.read_text())
    methods = ["downwind", "fixed_sequence", "ridge_q_alpha_1", "ridge_q_alpha_10",
               "ridge_q_alpha_100", "tabular_q", "nearest_neighbor_bc_5"]
    labels = ["Downwind", "Fixed time + direction", "Ridge Q / 1", "Ridge Q / 10",
              "Ridge Q / 100", "Tabular Q", "Nearest-neighbor BC / 5"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True, layout="constrained")
    for ax, mode, title in zip(axes, ("raw", "charged"),
                              ("Original burn accounting", "Line-footprint charge")):
        block = report["results"][mode]
        means = np.array([block["methods"][m]["mean_gain_ha_vs_advancing_front"] for m in methods])
        intervals = np.array([block["methods"][m]["descriptive_paired_bootstrap_95"] for m in methods])
        positions = np.arange(len(methods))
        colors = ["#2563eb" if value >= 0 else "#94a3b8" for value in means]
        ax.barh(positions, means, color=colors, height=.6)
        # Plot endpoints directly: percentile intervals need not bracket their point estimate.
        ax.hlines(positions, intervals[:, 0], intervals[:, 1], color="#172554", linewidth=1.5)
        ax.scatter(means, positions, color="#172554", s=18, zorder=3)
        ax.axvline(0, color="#475569", linewidth=1)
        rule = report["continuation_threshold"]
        threshold = max(rule["mean_gain_ha_vs_advancing_front"],
                        rule["fraction_of_oracle_gap"] * block["oracle_gap_vs_advancing_front_ha"])
        ax.axvline(threshold, color="#d97706", linestyle="--", label="Continuation threshold")
        ax.set_title(title + "\nOracle gap: %.1f ha" % block["oracle_gap_vs_advancing_front_ha"])
        ax.set_xlabel("Mean gain over advancing_front (ha); positive = better")
        ax.set_yticks(positions, labels)
        ax.grid(axis="x", alpha=.2)
        ax.set_axisbelow(True)
    axes[0].invert_yaxis()
    axes[1].legend(loc="lower right", fontsize=8)
    fig.suptitle("B=1 | 98 TRAIN fires | leave one fire out | exploratory simulator results\n"
                 "Bands: descriptive bootstrap of fixed OOF deltas; no independent final test", fontsize=11)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
