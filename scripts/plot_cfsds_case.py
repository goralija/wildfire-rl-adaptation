#!/usr/bin/env python3
"""Plot one built CFSDS case on the simulator's 20x20 grid."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch


def read_asc(path: Path) -> np.ndarray:
    return np.loadtxt(path, skiprows=6)


def style_grid(axis: plt.Axes) -> None:
    axis.set_xticks([0, 5, 10, 15, 19], labels=[1, 6, 11, 16, 20])
    axis.set_yticks([0, 5, 10, 15, 19], labels=[1, 6, 11, 16, 20])
    axis.set_xlabel("kolona ćelije (100 m)")
    axis.set_ylabel("red ćelije (100 m)")
    axis.set_xticks(np.arange(-0.5, 20, 1), minor=True)
    axis.set_yticks(np.arange(-0.5, 20, 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=0.3, alpha=0.6)
    axis.tick_params(which="minor", bottom=False, left=False)


def read_latest_prediction(probe_dir: Path, initial_mask: np.ndarray) -> np.ndarray | None:
    """Read the furthest saved simulator grid and isolate new burned cells."""
    grids = []
    if not probe_dir.exists():
        return None
    for path in (probe_dir / "simulator").rglob("ForestGrid*.csv"):
        match = re.fullmatch(r"ForestGrid(\d+)\.csv", path.name)
        if match:
            grids.append((int(match.group(1)), path))
    if not grids:
        return None
    _, path = max(grids, key=lambda item: item[0])
    final = np.loadtxt(path, delimiter=",", dtype=np.int16)
    if final.shape != initial_mask.shape:
        raise ValueError(f"Simulator grid shape {final.shape} does not match case {initial_mask.shape}")
    return (final > 0) & ~initial_mask


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-dir", type=Path, default=Path("runs/real-case/2018_747-day228"))
    parser.add_argument("--probe-dir", type=Path, help="optional simulator replay folder; defaults to case-dir/probe/no-action")
    parser.add_argument("--out", type=Path, default=Path("reports/real-fire-data/2018_747-day228.png"))
    args = parser.parse_args()
    case_dir = args.case_dir
    case = json.loads((case_dir / "case.json").read_text())
    target_date = date.fromisoformat(case["event"]["target_date_local"])
    initial_date = target_date - timedelta(days=1)
    event_id = case["event"]["event_id"]
    input_dir = case_dir / "input"
    truth_dir = case_dir / "truth"
    forest = read_asc(input_dir / "Forest.asc").astype(int)
    target_fraction = read_asc(truth_dir / "target_next_day_fraction.asc")

    burnt = np.zeros((20, 20), dtype=bool)
    burning = np.zeros((20, 20), dtype=bool)
    with (input_dir / "InitialState.csv").open(newline="") as stream:
        for item in csv.DictReader(stream):
            index = int(item["ncell"]) - 1
            row, col = divmod(index, 20)
            if item["state"] == "burnt":
                burnt[row, col] = True
            elif item["state"] == "burning":
                burning[row, col] = True

    lookup = pd.read_csv(input_dir / "fbp_lookup_table.csv")
    lookup.columns = [str(column).strip() for column in lookup.columns]
    rgb_by_code = {
        int(row.grid_value): np.array([row.r, row.g, row.b], dtype=float) / 255.0
        for row in lookup.itertuples(index=False)
    }
    fuel_rgb = np.zeros((20, 20, 3), dtype=float)
    for code in np.unique(forest):
        fuel_rgb[forest == code] = rgb_by_code[int(code)]

    initial_rgb = np.empty((20, 20, 3), dtype=float)
    initial_rgb[:] = mcolors.to_rgb("#d6e5d2")
    initial_rgb[burnt] = mcolors.to_rgb("#625653")
    initial_rgb[burning] = mcolors.to_rgb("#ff9f1c")

    overlay_rgb = fuel_rgb.copy()
    overlay_rgb[burnt] = mcolors.to_rgb("#625653")
    overlay_rgb[burning] = mcolors.to_rgb("#ff9f1c")
    probe_dir = args.probe_dir or (case_dir / "probe/no-action")
    predicted = read_latest_prediction(probe_dir, burnt | burning)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.subplots_adjust(left=0.08, right=0.93, top=0.91, bottom=0.19, hspace=0.34, wspace=0.27)
    ax = axes[0, 0]
    ax.imshow(fuel_rgb, origin="upper", interpolation="nearest")
    ax.set_title("FBP gorivo u simulatoru")
    style_grid(ax)
    ax = axes[0, 1]
    ax.imshow(initial_rgb, origin="upper", interpolation="nearest")
    ax.set_title(f"Početno stanje — {initial_date:%d.%m.%Y} (dan n−1)")
    style_grid(ax)

    ax = axes[1, 0]
    image = ax.imshow(target_fraction, origin="upper", interpolation="nearest", cmap="Reds", vmin=0, vmax=1)
    ax.set_title(f"Opaženi rast — {target_date:%d.%m.%Y} (dan n)")
    style_grid(ax)
    colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    colorbar.set_label("udio ćelije pokriven požarom")

    ax = axes[1, 1]
    ax.imshow(overlay_rgb, origin="upper", interpolation="nearest")
    if predicted is not None:
        prediction_rgb = np.zeros((20, 20, 4), dtype=float)
        prediction_rgb[predicted] = (*mcolors.to_rgb("#2b83ba"), 0.9)
        ax.imshow(prediction_rgb, origin="upper", interpolation="nearest")
    target_binary = target_fraction >= 0.5
    if target_binary.any():
        ax.contour(target_binary.astype(float), levels=[0.5], colors=["#d7191c"], linewidths=1.7)
    ax.set_title("Replay bez intervencije + opaženi cilj")
    style_grid(ax)

    fig.suptitle(f"Stvarni požar {event_id} — šta simulator dobija na ulazu", fontsize=15)
    fuel_handles = [
        Patch(facecolor=rgb_by_code[int(code)], label=str(lookup.loc[lookup.grid_value == int(code), "fuel_type"].iloc[0]))
        for code in np.unique(forest)
    ]
    fig.legend(
        handles=[
            *fuel_handles,
            Patch(facecolor=mcolors.to_rgb("#625653"), label="ranije izgorjelo"),
            Patch(facecolor=mcolors.to_rgb("#ff9f1c"), label="aktivni rub dan n−1"),
            *([Patch(facecolor=mcolors.to_rgb("#2b83ba"), label="simulator: novo izgorjelo")] if predicted is not None else []),
            Patch(facecolor="none", edgecolor="#d7191c", label="opaženi cilj dan n"),
        ],
        loc="lower center", bbox_to_anchor=(0.5, 0.075), ncol=5 if predicted is None else 6, frameon=False,
    )
    fig.text(
        0.5, 0.015,
        "CFSDS granica: satelitski interpolirana, 90 m → 100 m; gorivo: službena FBP 2014b karta, 250 m → 100 m. "
        "Plavi replay dodiruje rub 2×2 km karte; nastavak izvan nje nije simuliran. Status gašenja nije poznat.",
        ha="center", va="top", fontsize=9,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=190, bbox_inches="tight")
    plt.close(fig)
    print(json.dumps({"image": str(args.out), "case_id": case["case_id"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
