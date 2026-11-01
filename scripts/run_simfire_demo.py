#!/usr/bin/env python3
"""Run a small, reproducible SimFire demonstration (not a research result)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMFIRE_ROOT = ROOT / "external" / "simfire"
DEFAULT_OUTPUT = ROOT / "runs" / "simfire-demo"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pokreni mali funkcionalni SimFire primjer. Ovo koristi funkcionalno "
            "generisanu mapu, ne BurnMD historijski požar."
        )
    )
    parser.add_argument("--steps", type=int, default=15, help="broj simulacijskih minuta")
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT / datetime.now().strftime("%Y%m%d-%H%M%S"),
        help="novi direktorij za GIF, graf i JSON receipt",
    )
    args = parser.parse_args()
    if args.steps < 1:
        parser.error("--steps mora biti najmanje 1")
    if not SIMFIRE_ROOT.is_dir():
        parser.error(
            "Nedostaje external/simfire. Pokrenite bootstrap iz "
            "docs/research/SIMFIRE_ENVIRONMENT.md."
        )

    output = args.out.expanduser().resolve()
    if output.exists() and any(output.iterdir()):
        parser.error(f"Izlazni direktorij već sadrži fajlove: {output}")
    output.mkdir(parents=True, exist_ok=True)

    # Pygame can render frames without opening a desktop window.
    local = ROOT / ".local"
    (local / "cache").mkdir(parents=True, exist_ok=True)
    (local / "matplotlib").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("XDG_CACHE_HOME", str(local / "cache"))
    os.environ.setdefault("MPLCONFIGDIR", str(local / "matplotlib"))
    sys.path.insert(0, str(SIMFIRE_ROOT))

    from simfire.enums import BurnStatus
    from simfire.sim.simulation import FireSimulation
    from simfire.utils.config import Config
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap

    config = Config(str(SIMFIRE_ROOT / "configs" / "functional_config.yml"))
    config.simulation.headless = False
    config.simulation.save_data = False
    config.simulation.sf_home = str(output)
    simulation = FireSimulation(config)

    try:
        simulation.rendering = True
        fire_map, active = simulation.run(f"{args.steps}m")
        simulation.save_gif(output / "functional-fire.gif")
    finally:
        if simulation.rendering:
            simulation.rendering = False

    labels = ["Unburned", "Burning", "Burned", "Fireline", "Scratchline", "Wetline"]
    colors = ["#536b3f", "#e63946", "#8d5524", "#f1faee", "#2a9d8f", "#457b9d"]
    fig, axis = plt.subplots(figsize=(7, 6))
    image = axis.imshow(
        fire_map,
        cmap=ListedColormap(colors),
        vmin=0,
        vmax=len(colors) - 1,
        interpolation="nearest",
    )
    axis.set_title(f"SimFire functional demo — {args.steps} simulated minutes")
    axis.set_xlabel("Map cell")
    axis.set_ylabel("Map cell")
    colorbar = fig.colorbar(image, ax=axis, ticks=range(len(labels)), shrink=0.8)
    colorbar.ax.set_yticklabels(labels)
    fig.tight_layout()
    fig.savefig(output / "final-state.png", dpi=150)
    plt.close(fig)

    counts = {
        "unburned": int((fire_map == BurnStatus.UNBURNED).sum()),
        "burning": int((fire_map == BurnStatus.BURNING).sum()),
        "burned": int((fire_map == BurnStatus.BURNED).sum()),
        "fireline": int((fire_map == BurnStatus.FIRELINE).sum()),
        "scratchline": int((fire_map == BurnStatus.SCRATCHLINE).sum()),
        "wetline": int((fire_map == BurnStatus.WETLINE).sum()),
    }
    receipt = {
        "kind": "functional_simulator_smoke",
        "scientific_result": False,
        "real_historical_data": False,
        "training_performed": False,
        "simfire_version": "2.0.1",
        "steps_minutes": args.steps,
        "grid_shape": list(fire_map.shape),
        "active_after_run": bool(active),
        "cell_counts": counts,
        "outputs": ["functional-fire.gif", "final-state.png"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({**receipt, "output_dir": str(output)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
