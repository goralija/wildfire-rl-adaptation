"""Paired statistics and report tables for the synthetic CA evaluations (ADR-028, ADR-029).

Saved fraction (weighted no-op damage the policy prevents) is the primary outcome.
Safety (close calls, units lost, retreats) is reported in its own block. Return is the
training objective, saved fraction minus the safety penalties, and is reported as such.
Every contrast and interval in the evaluation reports is computed here, from per-episode
rows of ``SyntheticSuppressionEnv.summary()`` plus ``return``.

Acceptance follows ADR-030 section 5: a learned policy passes against the comparator
heuristic when its paired saved-fraction difference has a 95% CI above 0 and it has no more
close calls and no more lost units in total. Return is reported but does not decide.
"""

from __future__ import annotations

import zlib
from typing import Dict, List, Mapping, Optional, Sequence

import numpy as np


HEURISTIC_NAMES = ("direct_flank", "protect_urban", "downwind_indirect")
REFERENCES = ("noop", "random")
CONTRAST_METRICS = ("saved_fraction", "return", "close_calls")
BOOTSTRAP_DRAWS = 4000
ACCEPTANCE_RULE = "ADR-030 section 5"
RETURN_DEFINITION = "saved_fraction - unit_loss_penalty * units_lost - close_call_penalty * close_calls"


def paired_bootstrap(a: Sequence[float], b: Sequence[float], seed: int,
                     draws: int = BOOTSTRAP_DRAWS) -> Optional[dict]:
    """Mean of the paired difference a - b with a percentile bootstrap 95% interval."""
    diff = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    if not diff.size:
        return None
    rng = np.random.default_rng(seed)
    boots = diff[rng.integers(0, diff.size, size=(draws, diff.size))].mean(axis=1)
    return {
        "mean": float(diff.mean()),
        "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))],
        "wins": int((diff > 0).sum()),
        "losses": int((diff < 0).sum()),
        "ties": int((diff == 0).sum()),
        "n": int(diff.size),
    }


def _contrast_seed(*labels: str) -> int:
    """Seed keyed on the contrast itself, so intervals do not depend on loop order."""
    return zlib.crc32("|".join(labels).encode())


def _column(rows: Sequence[dict], key: str) -> np.ndarray:
    return np.asarray([float(r.get(key, 0) or 0) for r in rows])


def policy_block(rows: Sequence[dict]) -> dict:
    """Suppression, safety and objective blocks for one policy's episodes."""
    saved = _column(rows, "saved_fraction")
    calls = _column(rows, "close_calls")
    lost = _column(rows, "units_lost")
    return {
        "episodes": len(rows),
        "suppression": {
            "mean_saved_fraction": float(saved.mean()),
            "median_saved_fraction": float(np.median(saved)),
            "new_cells_burned": int(_column(rows, "agent_new_cells").sum()),
            "noop_new_cells_burned": int(_column(rows, "noop_new_cells").sum()),
            "urban_cells_burned": float(_column(rows, "agent_urban_cells").sum()),
            "noop_urban_cells_burned": float(_column(rows, "noop_urban_cells").sum()),
            "line_cells": int(_column(rows, "line_cells").sum()),
            "line_area_ha": float(_column(rows, "line_area_ha").sum()),
            "line_cells_in_noop_footprint": int(_column(rows, "line_cells_in_noop_footprint").sum()),
            "edge_contact_episodes": int(_column(rows, "edge_contact").sum()),
        },
        "safety": {
            "units_lost": int(lost.sum()),
            "close_calls": int(calls.sum()),
            "retreats": int(_column(rows, "retreats").sum()),
            "episodes_with_unit_lost": int((lost > 0).sum()),
            "episodes_with_close_call": int((calls > 0).sum()),
        },
        "objective": {
            "mean_return": float(_column(rows, "return").mean()),
            "definition": RETURN_DEFINITION,
        },
    }


def best_heuristic_of(rows_by_policy: Mapping[str, Sequence[dict]]) -> Optional[str]:
    """Scripted tactic with the highest mean saved fraction among those evaluated."""
    present = [name for name in HEURISTIC_NAMES if name in rows_by_policy]
    if not present:
        return None
    return max(present, key=lambda name: _column(rows_by_policy[name], "saved_fraction").mean())


def acceptance_block(rows: Sequence[dict], comparator_rows: Sequence[dict], comparator: str,
                     label: str, name: str) -> dict:
    """Pass/fail of one learned policy against the comparator heuristic (ADR-030 section 5)."""
    primary = paired_bootstrap(_column(rows, "saved_fraction"),
                               _column(comparator_rows, "saved_fraction"),
                               _contrast_seed(label, name, comparator, "saved_fraction"))
    safety = {}
    for metric in ("close_calls", "units_lost"):
        mine, theirs = int(_column(rows, metric).sum()), int(_column(comparator_rows, metric).sum())
        safety[metric] = {"policy": mine, "comparator": theirs, "non_inferior": mine <= theirs}
    ret = paired_bootstrap(_column(rows, "return"), _column(comparator_rows, "return"),
                           _contrast_seed(label, name, comparator, "return"))
    primary_pass = bool(primary is not None and primary["ci95"][0] > 0)
    safety_pass = all(value["non_inferior"] for value in safety.values())
    return {
        "rule": ACCEPTANCE_RULE,
        "comparator": comparator,
        "primary_outcome": "saved_fraction",
        "primary": primary,
        "primary_pass": primary_pass,
        "safety": safety,
        "safety_pass": safety_pass,
        "return": dict(ret or {}, decides_acceptance=False),
        "pass": primary_pass and safety_pass,
    }


def summarize_policies(rows_by_policy: Mapping[str, Sequence[dict]],
                       best_heuristic: Optional[str] = None, label: str = "") -> dict:
    """Per-policy blocks and paired contrasts against no-op, random and the best heuristic.

    ``rows_by_policy[name][i]`` must be the same episode (seed or case) for every policy.
    """
    sizes = {len(rows) for rows in rows_by_policy.values()}
    if len(sizes) > 1:
        raise ValueError("every policy needs the same paired episodes")
    best = best_heuristic or best_heuristic_of(rows_by_policy)
    if best is not None and best not in rows_by_policy:
        raise ValueError("best heuristic %r was not evaluated" % best)
    references = [("vs_" + name, name) for name in REFERENCES if name in rows_by_policy]
    if best is not None:
        references.append(("vs_best_heuristic", best))
    table = {}
    for name, rows in rows_by_policy.items():
        block = policy_block(rows)
        block["contrasts"] = {}
        for key, other in references:
            if other == name:
                continue
            contrast = {"reference": other}
            for metric in CONTRAST_METRICS:
                contrast[metric] = paired_bootstrap(
                    _column(rows, metric), _column(rows_by_policy[other], metric),
                    _contrast_seed(label, name, other, metric))
            block["contrasts"][key] = contrast
        table[name] = block
    candidates = [name for name in rows_by_policy
                  if name not in REFERENCES and name not in HEURISTIC_NAMES]
    acceptance = {} if best is None else {
        name: acceptance_block(rows_by_policy[name], rows_by_policy[best], best, label, name)
        for name in candidates}
    return {"primary_outcome": "saved_fraction", "best_heuristic": best, "policies": table,
            "acceptance": acceptance}


def summarize_groups(rows_by_policy: Mapping[str, Sequence[dict]], groups: Mapping[str, List[int]],
                     main: str, best_heuristic: Optional[str] = None) -> dict:
    """Summaries for episode subsets; the best heuristic is fixed once on the ``main`` group."""
    def subset(indices):
        return {name: [rows[i] for i in indices] for name, rows in rows_by_policy.items()}

    best = best_heuristic or best_heuristic_of(subset(groups[main]))
    return {"primary_outcome": "saved_fraction", "best_heuristic": best,
            "groups": {group: summarize_policies(subset(indices), best, label=group)
                       for group, indices in groups.items()}}


def real_case_groups(results: Sequence[tuple]) -> Dict[str, List[int]]:
    """Index groups over ``(case_id, metadata, rows_by_policy)`` real-case results.

    ``no_edge_in_crop`` keeps cases whose no-op fire never reaches the crop edge and whose
    initial cells all lie inside the crop (the ADR-028 edge-sensitivity subset).
    """
    def noop_edge(rows):
        row = next(iter(rows.values()))
        if "noop_edge_contact" in row:
            return bool(row["noop_edge_contact"])
        return bool(rows["noop"]["edge_contact"])  # reports written before TASK-024

    in_crop = [i for i, r in enumerate(results) if not r[1].get("initial_cells_outside_crop")]
    return {
        "ex_train": [i for i, r in enumerate(results) if r[1]["split"] == "train"],
        "ex_validation": [i for i, r in enumerate(results) if r[1]["split"] == "validation"],
        "all": list(range(len(results))),
        "all_in_crop": in_crop,
        "no_edge_in_crop": [i for i in in_crop if not noop_edge(results[i][2])],
    }


def format_table(summary: dict) -> List[str]:
    """Plain-text lines: suppression first, then safety, then return and contrasts."""
    lines = []
    for name, block in summary["policies"].items():
        sup, safe = block["suppression"], block["safety"]
        lines.append("%-22s saved mean %.4f median %.4f | line %d cells (%d in no-op footprint)"
                     % (name[:22], sup["mean_saved_fraction"], sup["median_saved_fraction"],
                        sup["line_cells"], sup["line_cells_in_noop_footprint"]))
        lines.append("%-22s safety: close calls %d, units lost %d | return %.4f"
                     % ("", safe["close_calls"], safe["units_lost"],
                        block["objective"]["mean_return"]))
        for key, contrast in block["contrasts"].items():
            parts = []
            for metric in ("saved_fraction", "return"):
                value = contrast[metric]
                if value is not None:
                    parts.append("%s %+.4f [%+.4f, %+.4f]" % (metric, value["mean"], *value["ci95"]))
            lines.append("%-22s %s (%s): %s" % ("", key, contrast["reference"], "; ".join(parts)))
    for name, block in summary.get("acceptance", {}).items():
        primary, safety = block["primary"], block["safety"]
        lines.append("ACCEPTANCE %s vs %s (%s): %s | saved %+.4f [%+.4f, %+.4f] %s | "
                     "close calls %d vs %d, units lost %d vs %d %s | return %+.4f (not deciding)"
                     % (name, block["comparator"], block["rule"],
                        "PASS" if block["pass"] else "FAIL", primary["mean"], *primary["ci95"],
                        "pass" if block["primary_pass"] else "fail",
                        safety["close_calls"]["policy"], safety["close_calls"]["comparator"],
                        safety["units_lost"]["policy"], safety["units_lost"]["comparator"],
                        "pass" if block["safety_pass"] else "fail",
                        block["return"].get("mean", float("nan"))))
    return lines
