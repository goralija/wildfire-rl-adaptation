#!/usr/bin/env python3
"""Stratify a full TRAIN no-op gate report to locate where SimFire loses IoU.

Reads one local full evaluator report (with per-case trajectories) and writes a
compact JSON summary. Growth-attribution uses only scored metrics: cells that
SimFire adds beyond the initial mask and that the later FEDS outline also covers
are ``new_hit`` cells; the rest of the added cells are ``new_false``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics


def _tercile_edges(values):
    ordered = sorted(values)
    return ordered[len(ordered) // 3], ordered[(2 * len(ordered)) // 3]


def _bucket(value, edges):
    low, high = edges
    return "low" if value <= low else ("mid" if value <= high else "high")


def case_rows(report: dict) -> list:
    rows = []
    for case in report["results"]:
        initial_cells = case["initial_feds_state"]["burn_scar_cells"]
        for row in case["trajectory"]:
            persist = row["persistence_reference"]
            observed = row["observed_burned_cells"]
            persist_hit = persist["intersection_cells"]
            observed_growth = max(0, observed - persist_hit)
            new_cells = row["new_burned_cells_since_initial"]
            new_hit = max(0, row["intersection_cells"] - persist_hit)
            rows.append({
                "scenario_id": case["scenario_id"],
                "hours": row["hours_since_start"],
                "initial_cells": persist["predicted_burned_cells"],
                "scar_cells": initial_cells,
                "observed_cells": observed,
                "observed_growth_cells": observed_growth,
                "observed_growth_ratio": observed / max(1, persist["predicted_burned_cells"]),
                "sim_new_cells": new_cells,
                "sim_new_hit_cells": new_hit,
                "sim_new_false_cells": max(0, new_cells - new_hit),
                "iou": row["iou"],
                "persistence_iou": persist["iou"],
                "iou_delta": row["iou"] - persist["iou"],
                "area_error_ha": abs(row["predicted_area_ha"] - row["observed_area_ha"]),
                "persistence_area_error_ha": abs(persist["predicted_area_ha"] - persist["observed_area_ha"]),
                "fire_active": row["fire_active_after_segment"],
                "edge": row["touches_map_edge"],
                "wind_ft_min": row["forcing"]["wind_speed_proxy_ft_per_min"],
                "moisture": row["forcing"]["fuel_moisture_fraction_proxy"],
            })
    return rows


def summarize(rows: list) -> dict:
    def block(items):
        if not items:
            return {"timepoints": 0}
        added = sum(r["sim_new_cells"] for r in items)
        hit = sum(r["sim_new_hit_cells"] for r in items)
        growth = sum(r["observed_growth_cells"] for r in items)
        return {
            "timepoints": len(items),
            "mean_iou_delta_vs_persistence": statistics.fmean(r["iou_delta"] for r in items),
            "sum_iou_delta": sum(r["iou_delta"] for r in items),
            "mean_sim_new_cells": statistics.fmean(r["sim_new_cells"] for r in items),
            "mean_observed_growth_cells": statistics.fmean(r["observed_growth_cells"] for r in items),
            "new_cell_precision": hit / added if added else None,
            "observed_growth_recall": hit / growth if growth else None,
            "share_timepoints_sim_grows": sum(r["sim_new_cells"] > 0 for r in items) / len(items),
            "share_timepoints_observed_grows": sum(r["observed_growth_cells"] > 0 for r in items) / len(items),
        }

    size_edges = _tercile_edges([r["initial_cells"] for r in rows])
    growth_edges = _tercile_edges([r["observed_growth_ratio"] for r in rows])
    output = {"all": block(rows), "by_hours": {}, "by_initial_size": {}, "by_observed_growth": {}}
    for hours in sorted({r["hours"] for r in rows}):
        output["by_hours"][str(hours)] = block([r for r in rows if r["hours"] == hours])
    for name in ("low", "mid", "high"):
        output["by_initial_size"][name] = block([r for r in rows if _bucket(r["initial_cells"], size_edges) == name])
        output["by_observed_growth"][name] = block(
            [r for r in rows if _bucket(r["observed_growth_ratio"], growth_edges) == name])
    output["tercile_edges"] = {"initial_cells": size_edges, "observed_growth_ratio": growth_edges}
    sim_grows = [r for r in rows if r["sim_new_cells"] > 0]
    sim_static = [r for r in rows if r["sim_new_cells"] == 0]
    output["sim_grows"] = block(sim_grows)
    output["sim_static"] = block(sim_static)
    worst = sorted(rows, key=lambda r: r["iou_delta"])[:10]
    output["worst_timepoints"] = [
        {k: r[k] for k in ("scenario_id", "hours", "initial_cells", "observed_cells", "sim_new_cells",
                           "sim_new_hit_cells", "iou", "persistence_iou", "wind_ft_min", "moisture")}
        for r in worst
    ]
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    if report.get("test_cases_loaded") is not False:
        parser.error("refusing a report that loaded TEST cases")
    summary = {
        "source_configuration": report["configuration"],
        "source_summary": report.get("summary"),
        "diagnosis": summarize(case_rows(report)),
    }
    text = json.dumps(summary, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
