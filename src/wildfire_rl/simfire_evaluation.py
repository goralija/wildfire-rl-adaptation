"""Locked, reproducible evaluation helpers for the FPA-FOD SimFire benchmark.

The module does not train policies. It validates the benchmark membership and
computes summaries from matched SimFire episode receipts.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "configs/simfire/evaluation-v1.json"
POLICY_IDS = ("no_op", "front_edge_heuristic", "base_ppo", "fine_tuned_ppo")
REQUIRED_SPLITS = {"train": 40, "validation": 20, "test": 19}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_protocol(config_path: Path = DEFAULT_CONFIG, root: Path = ROOT) -> dict[str, Any]:
    """Validate pinned files, split membership, and the immutable episode contract."""
    config_path = Path(config_path)
    root = Path(root)
    config = load_json(config_path)
    if config.get("schema_version") != 1:
        raise ValueError("unsupported SimFire evaluation config schema")
    if config.get("benchmark_id") != "simfire-fpa-fod-evaluation-v1":
        raise ValueError("unexpected benchmark_id")
    if tuple(config.get("policies", ())) != POLICY_IDS:
        raise ValueError("policy IDs or their declared order do not match the frozen contract")
    seeds = config.get("evaluation_seeds")
    if (not isinstance(seeds, list) or len(seeds) != 5 or
            any(type(seed) is not int or seed < 0 for seed in seeds) or
            len(set(seeds)) != len(seeds)):
        raise ValueError("evaluation_seeds must contain five distinct nonnegative integers")

    episode = config.get("episode", {})
    expected_episode = {
        "weather_mode": "gridmet_daily_proxy",
        "weather_wind_adjustment_factor": None,
        "fireline_budget": 32,
        "decision_minutes": 30,
        "horizon_decisions": 24,
        "max_fire_duration_updates": 15,
    }
    if episode != expected_episode:
        raise ValueError("episode settings differ from the frozen SimFire contract")

    membership_ref = config.get("membership", {})
    cohort_ref = config.get("cohort_manifest", {})
    membership_path = root / membership_ref.get("path", "")
    cohort_path = root / cohort_ref.get("path", "")
    if sha256_file(membership_path) != membership_ref.get("sha256"):
        raise ValueError("evaluation membership checksum does not match the contract")
    if sha256_file(cohort_path) != cohort_ref.get("sha256"):
        raise ValueError("cohort manifest checksum does not match the contract")
    membership = load_json(membership_path)
    cohort = load_json(cohort_path)
    if membership.get("cohort_id") != cohort.get("cohort_id"):
        raise ValueError("membership and cohort IDs do not match")

    split_ids = membership.get("splits", {})
    if set(split_ids) != set(REQUIRED_SPLITS):
        raise ValueError("membership must declare exactly train, validation, and test")
    all_ids: list[str] = []
    for split, expected_count in REQUIRED_SPLITS.items():
        ids = split_ids.get(split)
        if (not isinstance(ids, list) or len(ids) != expected_count or
                any(not isinstance(scenario_id, str) for scenario_id in ids) or
                len(set(ids)) != expected_count):
            raise ValueError("{} membership must contain {} unique IDs".format(split, expected_count))
        all_ids.extend(ids)
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("an incident appears in more than one split")

    excluded = config.get("excluded_test_ids", [])
    membership_excluded = {
        row.get("scenario_id")
        for row in membership.get("excluded_from_final_test", [])
    }
    if set(excluded) != membership_excluded:
        raise ValueError("excluded incident list differs from the frozen membership manifest")
    if not excluded or set(excluded) & set(split_ids.get("test", [])):
        raise ValueError("excluded smoke incidents must be named and absent from final test")
    cohort_by_id = {row["scenario_id"]: row for row in cohort.get("cases", [])}
    for split, ids in split_ids.items():
        for scenario_id in ids:
            row = cohort_by_id.get(scenario_id)
            if row is None or row.get("split") != split:
                raise ValueError("{} is not in the declared {} cohort split".format(scenario_id, split))
    for scenario_id in excluded:
        row = cohort_by_id.get(scenario_id)
        if row is None or row.get("split") != "test":
            raise ValueError("excluded incident {} is not a cohort test case".format(scenario_id))
    if len(cohort_by_id) != 80:
        raise ValueError("expected the pinned 80-incident cohort")

    return {
        "config": config,
        "membership": membership,
        "cohort": cohort,
        "membership_path": membership_path,
        "cohort_path": cohort_path,
    }


def select_cohort_cases(
    cohort: dict[str, Any], split: str, scenario_ids: list[str]
) -> dict[str, Any]:
    """Return a cohort copy containing only the explicitly authorized incident IDs."""
    cases_by_id = {row["scenario_id"]: row for row in cohort.get("cases", [])}
    selected = []
    for scenario_id in scenario_ids:
        row = cases_by_id.get(scenario_id)
        if row is None or row.get("split") != split:
            raise ValueError("{} is not an incident in the {} split".format(scenario_id, split))
        selected.append(row)
    if len(set(scenario_ids)) != len(scenario_ids):
        raise ValueError("scenario selection contains duplicate IDs")
    result = dict(cohort)
    result["cases"] = selected
    return result


def choose_front_edge_action(
    observation: dict[str, Any], action_masks: Iterable[bool], rows: int, columns: int
) -> int:
    """Place one legal point nearest the currently burning front; ties are row/column ordered.

    The rule reads only the current observation and legal-action mask. It does not
    inspect a final perimeter, future fire map, or hidden simulator state.
    """
    import numpy as np

    mask = np.asarray(action_masks, dtype=bool)
    if mask.ndim != 1 or mask.size != rows * columns + 1:
        raise ValueError("action mask shape does not match the declared grid")
    if not mask[0]:
        raise ValueError("no-op must remain a legal action")
    candidates = np.flatnonzero(mask[1:])
    if candidates.size == 0:
        return 0
    fire_codes = np.rint(np.asarray(observation["map"][-1]) * 5).astype(np.int16)
    if fire_codes.shape != (rows, columns):
        raise ValueError("fire-state observation shape does not match the declared grid")
    active_mask = np.isin(fire_codes, (1, 2))
    if not active_mask.any():
        return 0
    # Two-pass taxicab distance transform avoids comparing every legal cell with
    # every burning cell (which is costly late in a 128x128 episode).
    distance = np.full((rows, columns), rows + columns + 1, dtype=np.int32)
    distance[active_mask] = 0
    for row in range(rows):
        for column in range(columns):
            if row:
                distance[row, column] = min(distance[row, column], distance[row - 1, column] + 1)
            if column:
                distance[row, column] = min(distance[row, column], distance[row, column - 1] + 1)
    for row in range(rows - 1, -1, -1):
        for column in range(columns - 1, -1, -1):
            if row + 1 < rows:
                distance[row, column] = min(distance[row, column], distance[row + 1, column] + 1)
            if column + 1 < columns:
                distance[row, column] = min(distance[row, column], distance[row, column + 1] + 1)
    legal_rows, legal_columns = np.unravel_index(candidates, (rows, columns))
    order = np.lexsort((legal_columns, legal_rows, distance[legal_rows, legal_columns]))
    row, column = int(legal_rows[order[0]]), int(legal_columns[order[0]])
    return 1 + row * columns + column


def _bootstrap_interval(values: list[float], *, resamples: int, seed: int) -> tuple[float, float] | None:
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    draws = sorted(fmean(rng.choices(values, k=len(values))) for _ in range(resamples))
    return draws[int(0.025 * (resamples - 1))], draws[int(0.975 * (resamples - 1))]


def summarize_paired_episodes(
    episodes: list[dict[str, Any]],
    *,
    resamples: int = 10000,
    seed: int = 20261102,
) -> dict[str, Any]:
    """Aggregate over matched (incident, seed) episodes and bootstrap by incident."""
    if not episodes:
        raise ValueError("no evaluation episodes to summarize")
    indexed: dict[tuple[str, int, str], dict[str, Any]] = {}
    policies: set[str] = set()
    for row in episodes:
        key = (str(row["scenario_id"]), int(row["seed"]), str(row["policy"]))
        if key in indexed:
            raise ValueError("duplicate policy/scenario/seed episode: {}".format(key))
        if float(row["cumulative_burned_area_ha"]) < 0:
            raise ValueError("burned area cannot be negative")
        indexed[key] = row
        policies.add(key[2])
    scenario_ids = sorted({key[0] for key in indexed})
    seeds = sorted({key[1] for key in indexed})
    comparisons = []
    per_incident = []
    baseline_policy = "base_ppo"
    target_policy = "fine_tuned_ppo"
    if {baseline_policy, target_policy} <= policies:
        for comparator in sorted(policies - {target_policy}):
            scenario_differences: list[float] = []
            for scenario_id in scenario_ids:
                seed_differences = []
                for evaluation_seed in seeds:
                    left = indexed.get((scenario_id, evaluation_seed, comparator))
                    right = indexed.get((scenario_id, evaluation_seed, target_policy))
                    if left is None or right is None:
                        raise ValueError("paired comparison is missing a matched episode")
                    seed_differences.append(
                        float(left["cumulative_burned_area_ha"]) -
                        float(right["cumulative_burned_area_ha"])
                    )
                incident_difference = fmean(seed_differences)
                scenario_differences.append(incident_difference)
                per_incident.append({
                    "scenario_id": scenario_id,
                    "comparator": comparator,
                    "target": target_policy,
                    "comparator_minus_fine_tuned_mean_ha": incident_difference,
                    "matched_seeds": len(seed_differences),
                })
            interval = _bootstrap_interval(scenario_differences, resamples=resamples, seed=seed)
            comparisons.append({
                "comparator": comparator,
                "target": target_policy,
                "incident_count": len(scenario_differences),
                "paired_mean_area_difference_ha": fmean(scenario_differences),
                "confidence_interval_95_ha": list(interval) if interval else None,
                "positive_means_fine_tuned_had_less_simulated_burned_area": True,
                "bootstrap_unit": "incident; seeds averaged within incident",
                "bootstrap_resamples": resamples,
                "bootstrap_seed": seed,
            })
    policy_summary = []
    for policy in sorted(policies):
        incident_means = []
        all_areas = []
        for scenario_id in scenario_ids:
            values = [
                float(indexed[(scenario_id, evaluation_seed, policy)]["cumulative_burned_area_ha"])
                for evaluation_seed in seeds
                if (scenario_id, evaluation_seed, policy) in indexed
            ]
            if not values:
                continue
            incident_means.append(fmean(values))
            all_areas.extend(values)
        interval = _bootstrap_interval(incident_means, resamples=resamples, seed=seed)
        policy_summary.append({
            "policy": policy,
            "incident_count": len(incident_means),
            "episode_count": len(all_areas),
            "mean_simulated_burned_area_ha": fmean(all_areas),
            "mean_incident_area_ha": fmean(incident_means),
            "incident_bootstrap_ci95_mean_area_ha": list(interval) if interval else None,
        })
    return {
        "policy_summary": policy_summary,
        "paired_comparisons": comparisons,
        "per_incident_paired_rows": per_incident,
    }
