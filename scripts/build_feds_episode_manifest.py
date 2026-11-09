#!/usr/bin/env python3
"""Freeze FPA-FOD/FEDS episodes after the declared crosswalk gate passes."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _one_record_per_feds_fire(
    cases: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep the lowest-fod_id record per FEDS fire (ADR-030 §6); return kept and excluded.

    A FEDS fire is (fireID, start), the crosswalk's key: FEDS-CONUS numbers fires per
    yearly file, so the same fireID in another year is another fire.
    """
    by_fire: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for case in cases:
        reference = case["evaluation_reference"]
        key = (reference["source_fire_id"], reference["event_start_time"])
        by_fire.setdefault(key, []).append(case)
    kept_ids = set()
    excluded = []
    for (fire_id, _start), group in by_fire.items():
        if len({case["split"] for case in group}) > 1:
            raise ValueError(
                f"FEDS fire {fire_id} is joined by records in both TRAIN and VALIDATION."
            )
        kept = min(group, key=lambda case: case["event"]["fod_id"])
        kept_ids.add(kept["scenario_id"])
        excluded.extend(
            {
                "scenario_id": case["scenario_id"],
                "split": case["split"],
                "fod_id": case["event"]["fod_id"],
                "source_fire_id": fire_id,
                "kept_scenario_id": kept["scenario_id"],
            }
            for case in group
            if case is not kept
        )
    return [case for case in cases if case["scenario_id"] in kept_ids], excluded


def build_episode_manifest(
    frame: dict[str, Any],
    crosswalk: dict[str, Any],
    *,
    frame_sha256: str,
    crosswalk_sha256: str,
) -> dict[str, Any]:
    if frame.get("schema_version") != "fpa-feds-candidate-frame/1.0":
        raise ValueError("Unexpected FPA-FOD candidate-frame schema.")
    if crosswalk.get("schema_version") != "fpa-feds-fle-crosswalk/1.0":
        raise ValueError("Unexpected FPA-FOD/FEDS crosswalk schema.")
    if frame.get("candidate_frame", {}).get("test_year_not_loaded") is not True:
        raise ValueError("Candidate frame must affirm that test-year records were not loaded.")
    if crosswalk.get("test_cases_loaded") is not False:
        raise ValueError("Crosswalk must affirm that test cases were not loaded.")
    if crosswalk.get("pre_agent_data_gate", {}).get("pass") is not True:
        raise ValueError("The pre-agent train/validation data gate has not passed.")
    if set(crosswalk.get("audited_splits", [])) != {"train", "validation"}:
        raise ValueError("A complete train/validation crosswalk is required.")
    frame_cases = frame.get("cases", [])
    crosswalk_cases = crosswalk.get("cases", [])
    if len(frame_cases) != frame.get("case_count"):
        raise ValueError("Candidate-frame rows do not match its declared case count.")
    if len(crosswalk_cases) != frame.get("case_count"):
        raise ValueError("Crosswalk does not cover the complete candidate frame.")
    if any(case.get("split") not in {"train", "validation"} for case in frame_cases):
        raise ValueError("Candidate frame contains a test or unknown split.")

    by_scenario = {case.get("scenario_id"): case for case in frame_cases}
    if None in by_scenario or len(by_scenario) != len(frame_cases):
        raise ValueError("Candidate frame has missing or duplicate scenario IDs.")

    selected_cases = []
    for row in crosswalk_cases:
        scenario_id = row.get("scenario_id")
        case = by_scenario.get(scenario_id)
        if case is None or case.get("split") != row.get("split"):
            raise ValueError(f"Crosswalk case does not match candidate frame: {scenario_id}")
        feds = row.get("feds", {})
        candidate = feds.get("selected")
        if feds.get("status") != "unique_spatiotemporal_candidate" or candidate is None:
            continue
        if not candidate.get("two_consecutive_12h_states"):
            continue
        if not candidate.get("five_states_cover_48h"):
            continue
        state_times = candidate.get("episode_48h_state_timestamps", [])
        if len(state_times) != 5:
            raise ValueError(f"Incomplete 48-hour FEDS reference for {scenario_id}.")
        selected_cases.append(
            {
                "scenario_id": scenario_id,
                "split": case["split"],
                "event": {
                    "fod_id": case["fod_id"],
                    "fpa_unique_fire_id": case["fpa_unique_fire_id"],
                    "name": case["name"],
                    "state": case["state"],
                    "year": case["year"],
                    "discovery_date": case["discovery_date"],
                    "longitude": case["longitude"],
                    "latitude": case["latitude"],
                },
                "evaluation_reference": {
                    "source_fire_id": candidate["fire_id"],
                    "event_start_time": candidate["t_start"],
                    "initial_state_time": candidate["episode_start_state"],
                    "observed_state_times_0_to_48h": state_times,
                    "start_point_distance_m": candidate[
                        "minimum_start_window_distance_m"
                    ],
                },
            }
        )

    selected_cases, excluded_duplicates = _one_record_per_feds_fire(selected_cases)
    counts = {
        split: sum(case["split"] == split for case in selected_cases)
        for split in ("train", "validation")
    }
    threshold = crosswalk["pre_agent_data_gate"]["threshold"]
    if counts["train"] < threshold["train_two_state_minimum"]:
        raise ValueError("Full 48-hour train references fall below the pre-agent minimum.")
    if counts["validation"] < threshold["validation_two_state_minimum"]:
        raise ValueError("Full 48-hour validation references fall below the pre-agent minimum.")

    return {
        "schema_version": "fpa-feds-episode-manifest/1.0",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "cohort_id": frame["cohort_id"],
        "case_count": len(selected_cases),
        "case_counts_by_split": counts,
        "pre_agent_data_gate": crosswalk["pre_agent_data_gate"],
        "test_cases_loaded": False,
        "candidate_frame": {
            "manifest": "data/manifests/fpa-feds-candidate-frame-v1.json",
            "sha256": frame_sha256,
            "case_count": frame["case_count"],
            "selection_filter": frame["candidate_frame"]["filter"],
        },
        "crosswalk": {
            "report": "reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json",
            "sha256": crosswalk_sha256,
            "spatial_search_radius_m": crosswalk["spatial_search_radius_m"],
            "feds_start_date_window_days": crosswalk["feds_start_date_window_days"],
            "matching_rule": (
                "One unique FEDS fire whose t_st date is within -1/+2 days of the "
                "FPA-FOD discovery date and whose perimeter lies within the fixed "
                "3 km radius during the first 24 hours after t_st. Each retained "
                "episode has five consecutive 12-hour FEDS states from its initial "
                "observed state through +48 hours."
            ),
        },
        "deduplication": {
            "rule": (
                "ADR-030 §6: one record per FEDS fire (fireID and start time); when "
                "several FPA-FOD records join the same FEDS fire, keep the one with the "
                "lowest fod_id."
            ),
            "excluded_records": excluded_duplicates,
        },
        "information_boundary": {
            "agent_inputs": [
                "initial FEDS perimeter and active-front state",
                "LANDFIRE fuels and terrain for the episode map",
                "declared weather inputs",
                "standardized resource budget and current simulator state",
            ],
            "evaluation_only": [
                "future FEDS state timestamps and geometries",
                "FPA-FOD discovery point and metadata",
            ],
            "excluded_from_policy": [
                "reported final area",
                "MTBS identifier and final perimeter",
                "FLE post-hoc outcome",
                "all test-year records",
            ],
        },
        "limitations": [
            "The FPA-FOD discovery point is an incident reference point with unknown case-specific positional uncertainty, not a verified ignition coordinate.",
            "The candidate frame is restricted to screened >=5,000-acre incidents in ten western states and is not a representative national sample.",
            "FEDS perimeters are satellite-derived 375 m observations and are noisy references, not ground-truth fire boundaries.",
            "FLE outcomes are not included in this episode manifest and cannot identify counterfactual line effectiveness.",
        ],
        "cases": selected_cases,
    }


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--frame",
        type=Path,
        default=root / "data/manifests/fpa-feds-candidate-frame-v1.json",
    )
    parser.add_argument(
        "--crosswalk",
        type=Path,
        default=root / "reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=root / "data/manifests/feds-episode-cohort-v1.json",
    )
    args = parser.parse_args(argv)
    frame = json.loads(args.frame.read_text(encoding="utf-8"))
    crosswalk = json.loads(args.crosswalk.read_text(encoding="utf-8"))
    manifest = build_episode_manifest(
        frame,
        crosswalk,
        frame_sha256=sha256_file(args.frame),
        crosswalk_sha256=sha256_file(args.crosswalk),
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"case_count": manifest["case_count"], "splits": manifest["case_counts_by_split"], "test_cases_loaded": manifest["test_cases_loaded"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
