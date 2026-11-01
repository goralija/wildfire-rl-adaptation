#!/usr/bin/env python3
"""Build a small, event-separated SimFire cohort from the official USFS FPA-FOD.

The filter uses large reported fires only to keep the first mapping workload bounded.
Reported final size is retained as context and never becomes an agent input or reward.
Fuel vintages are selected to predate each cohort year and to use public ImageServer
products that were confirmed reachable on 2026-11-01.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_fpa_fod_scenario import (  # noqa: E402
    ACRES_TO_HECTARES,
    OUT_FIELDS,
    QUERY_URL,
    SERVICE_LAYER,
    SOURCE_RELEASE,
    _read_geojson,
    _scenario,
    _sha256,
)

COHORT_ID = "fpa-fod-western-us-2018-2024-v2"
STATES = ("CA", "OR", "WA", "ID", "NV", "AZ", "UT", "CO", "NM", "MT")
YEARS_BY_SPLIT = {"train": (2018, 2019), "validation": (2023,), "test": (2024,)}
CASES_PER_YEAR = 20
MIN_FIRE_SIZE_ACRES = 5000
FUEL_BY_YEAR = {
    2018: ("LF2016", "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2016/LF2016_FBFM13_CONUS/ImageServer"),
    2019: ("LF2016", "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2016/LF2016_FBFM13_CONUS/ImageServer"),
    2023: ("LF2022", "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2022/LF2022_FBFM13_CONUS/ImageServer"),
    2024: ("LF2022", "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2022/LF2022_FBFM13_CONUS/ImageServer"),
}
TERRAIN_SERVICE = "https://lfps.usgs.gov/arcgis/rest/services/Landfire_Topo/LF2020_Elev_CONUS/ImageServer"
WEATHER_SERVICE = "https://archive-api.open-meteo.com/v1/archive"
LICENSE_TEXT = (
    "USFS Research Data Archive says FPA-FOD may be used without additional permissions "
    "or fees; cite Short (2026), DOI 10.2737/RDS-2013-0009.7. Check joined raster and "
    "perimeter products separately."
)


def _verify_release() -> None:
    response = requests.get(SERVICE_LAYER.rsplit("/", 1)[0], params={"f": "json"}, timeout=60)
    response.raise_for_status()
    if SOURCE_RELEASE.split()[0] not in json.dumps(response.json(), sort_keys=True):
        raise RuntimeError("USFS FPA-FOD service release changed; review the new edition before rebuilding.")


def _query_year(year: int) -> tuple[dict, str]:
    state_list = ",".join("'{}'".format(state) for state in STATES)
    where = (
        "fire_year = {} AND state IN ({}) AND fire_size >= {} AND "
        "latitude IS NOT NULL AND longitude IS NOT NULL AND discovery_date IS NOT NULL "
        "AND mtbs_id IS NOT NULL"
    ).format(year, state_list, MIN_FIRE_SIZE_ACRES)
    params = {
        "where": where,
        "outFields": OUT_FIELDS,
        "returnGeometry": "true",
        "outSR": "4326",
        "f": "geojson",
        "resultRecordCount": 2000,
    }
    response = requests.get(QUERY_URL, params=params, timeout=90)
    response.raise_for_status()
    payload = response.json()
    if payload.get("type") != "FeatureCollection":
        raise RuntimeError("USFS returned a non-GeoJSON result for {}: {}".format(year, payload))
    return payload, response.url


def _rank(feature: dict, year: int) -> str:
    fod_id = int(feature["properties"]["fod_id"])
    raw = "simfire-cohort-v2:{}:{}".format(year, fod_id).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _select(features: list[dict], year: int) -> list[dict]:
    ranked = sorted(features, key=lambda item: _rank(item, year))
    selected = []
    used_states = set()
    for feature in ranked:
        state = feature["properties"].get("state")
        if state not in used_states:
            selected.append(feature)
            used_states.add(state)
        if len(selected) == CASES_PER_YEAR:
            return selected
    for feature in ranked:
        if feature not in selected:
            selected.append(feature)
        if len(selected) == CASES_PER_YEAR:
            return selected
    raise RuntimeError(
        "Only {} eligible records for {}; need {}. The cohort filter may need review.".format(
            len(features), year, CASES_PER_YEAR
        )
    )


def _make_case(feature: dict, year: int, split: str, snapshot_dir: Path, offline: bool) -> dict:
    fod_id = int(feature["properties"]["fod_id"])
    params = {
        "where": "fod_id = {}".format(fod_id),
        "outFields": OUT_FIELDS,
        "outSR": "4326",
        "returnGeometry": "true",
        "f": "geojson",
    }
    exact_url = "{}?{}".format(QUERY_URL, urlencode(params))
    snapshot_path = snapshot_dir / "fod-{}.geojson".format(fod_id)
    if offline:
        if not snapshot_path.is_file():
            raise FileNotFoundError("Missing saved record snapshot: {}".format(snapshot_path))
    else:
        response = requests.get(QUERY_URL, params=params, timeout=60)
        response.raise_for_status()
        payload = response.json()
        if len(payload.get("features", [])) != 1 or int(payload["features"][0]["properties"]["fod_id"]) != fod_id:
            raise RuntimeError("Exact FPA-FOD lookup did not return selected FOD_ID {}.".format(fod_id))
        snapshot_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    record = _read_geojson(snapshot_path)
    case = _scenario(record, 3840, 3840, snapshot_path)
    props = feature["properties"]
    fuel_release, _ = FUEL_BY_YEAR[year]
    snapshot_rel = snapshot_path.relative_to(ROOT).as_posix()
    case["event"]["source_url"] = exact_url
    case["event"]["source_record_snapshot"] = {
        "path": snapshot_rel,
        "sha256": _sha256(snapshot_path),
        "source_url": exact_url,
    }
    case["inputs"] = {
        "fuel": {
            "status": "candidate",
            "source": "LANDFIRE {} FBFM13 CONUS ImageServer".format(fuel_release),
            "source_release": fuel_release,
            "path": ".local/simfire-cohort-v2/{}/fuel-{}-fbfm13.tif".format(case["scenario_id"], fuel_release.lower()),
            "sha256": None,
            "units_and_mapping": (
                "30 m nearest-neighbor sample from pre-event {} FBFM13. Native codes must "
                "pass the pinned SimFire operational fuel mapping before case promotion."
            ).format(fuel_release),
        },
        "terrain": {
            "status": "candidate",
            "source": "LANDFIRE LF2020 Elevation CONUS ImageServer",
            "source_release": "LF2020 Elevation",
            "path": ".local/simfire-cohort-v2/{}/elevation-lf2020-m.tif".format(case["scenario_id"]),
            "sha256": None,
            "units_and_mapping": "Source meters; nearest-neighbor aligned to the 30 m UTM grid; SimFire converts meters to feet.",
        },
        "weather": {
            "status": "candidate",
            "source": "NCAR GDEX gridMET Daily Surface Data",
            "source_release": "gridMET daily, incident date, nearest sampled grid cell",
            "path": "data/processed/simfire-cohort-v2-gridmet-weather/{}.json".format(case["scenario_id"]),
            "sha256": None,
            "units_and_mapping": (
                "Eight original daily context variables with provider units and sampled grid-cell metadata; "
                "the separate gridMET-to-SimFire proxy is generated after acquisition."
            ),
        },
    }
    case["readiness"] = "candidate"
    case["split"] = split
    case["fire_behavior"]["seed"] = fod_id
    case["fire_behavior"]["weather_mapping_note"] = (
        "Daily gridMET is kept as original context. Generate the separate versioned SimFire "
        "proxy after acquisition; it is not an hourly replay or measured fuel moisture."
    )
    case["references"]["notes"] = (
        "MTBS_ID={} is a separate observed-perimeter reference for later visual context only. "
        "Neither MTBS perimeters nor FPA final size are agent input or reward."
    ).format(props.get("mtbs_id"))
    case["limitations"] = [
        "FPA-FOD point has unknown event-specific precision and represents an incident reference, not verified GPS ignition.",
        "The cohort is screened to >=5000 reported acres and ten western states; it is not a representative sample of all fires.",
        "FPA-reported final area is post-response context only and is not used as a no-action target or agent reward.",
        "gridMET is daily, approximately 4-km context; its SimFire proxy is approximate and not an hourly event replay.",
        "A source-compatible fuel raster is pre-event but is not a field-verified vegetation survey for the event date.",
    ]
    return case


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort-out",
        type=Path,
        default=ROOT / "data/manifests/simfire-fpa-fod-cohort-v2.json",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=ROOT / "reports/real-fire-data/fpa-fod-simfire-cohort-v2",
    )
    parser.add_argument(
        "--case-dir",
        type=Path,
        default=ROOT / "data/manifests/simfire-cases-v2",
    )
    parser.add_argument("--offline", action="store_true", help="regenerate from saved annual GeoJSON screen snapshots")
    args = parser.parse_args()
    cohort_path = args.cohort_out.expanduser().resolve()
    snapshot_dir = args.snapshot_dir.expanduser().resolve()
    case_dir = args.case_dir.expanduser().resolve()
    cohort_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)

    if not args.offline:
        _verify_release()

    cases = []
    screens = []
    for split, years in YEARS_BY_SPLIT.items():
        for year in years:
            snapshot_path = snapshot_dir / "{}-screen.geojson".format(year)
            if args.offline:
                payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
                query_url = payload.get("_cohort_query_url", "saved snapshot")
                payload.pop("_cohort_query_url", None)
            else:
                payload, query_url = _query_year(year)
                payload["_cohort_query_url"] = query_url
                snapshot_path.write_text(
                    json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
                )
            features = payload.get("features", [])
            if len(features) > 2000:
                raise RuntimeError("{} annual query exceeded the FPA service's record limit.".format(year))
            selected = _select(features, year)
            screens.append({
                "year": year,
                "split": split,
                "screened_pool_count": len(features),
                "selected_count": len(selected),
                "snapshot": snapshot_path.relative_to(ROOT).as_posix(),
                "snapshot_sha256": _sha256(snapshot_path),
                "query_url": query_url,
            })
            for feature in selected:
                props = feature["properties"]
                scenario = _make_case(feature, year, split, snapshot_dir, args.offline)
                path = case_dir / "{}.json".format(scenario["scenario_id"])
                path.write_text(json.dumps(scenario, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                cases.append({
                    "scenario_id": scenario["scenario_id"],
                    "source_record_id": "FOD_ID:{}".format(props["fod_id"]),
                    "year": year,
                    "state": props["state"],
                    "name": props.get("fire_name"),
                    "split": split,
                    "reported_final_area_ha_reference_only": float(props["fire_size"]) * ACRES_TO_HECTARES,
                    "mtbs_id_reference_only": props.get("mtbs_id"),
                    "fuel_release": FUEL_BY_YEAR[year][0],
                    "scenario_manifest": path.relative_to(ROOT).as_posix(),
                })

    all_ids = [case["source_record_id"] for case in cases]
    if len(all_ids) != len(set(all_ids)):
        raise RuntimeError("The selected cohort contains duplicate incident IDs across splits.")
    cohort = {
        "schema_version": "simfire-cohort/1.0",
        "cohort_id": COHORT_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Small, reproducible, real-incident environmental cohort for SimFire policy experiments; not a physical reconstruction.",
        "source": {
            "name": "USFS FPA-FOD current edition",
            "release": SOURCE_RELEASE,
            "service_url": SERVICE_LAYER,
            "license_and_citation": LICENSE_TEXT,
            "query_date": datetime.now(timezone.utc).date().isoformat(),
            "selection_rule": {
                "years": sorted(year for values in YEARS_BY_SPLIT.values() for year in values),
                "states": list(STATES),
                "minimum_reported_fire_size_acres": MIN_FIRE_SIZE_ACRES,
                "requires_mtbs_id": True,
                "requires_location_and_discovery_date": True,
                "sample_per_year": CASES_PER_YEAR,
                "sampling": "Stable SHA-256 ranking of FOD_ID, greedily preferring one event per state before filling the annual quota; selection does not rank by final size.",
            },
        },
        "split_rule": {
            "train": [2018, 2019],
            "validation": [2023],
            "test": [2024],
            "unit": "whole incident; events from one fire never cross splits",
            "note": "Out-of-time validation/test. Years 2020-2022 are omitted from this first cohort because their best pre-event FBFM13 layer is not presently available from the public ImageServer endpoint; do not substitute a post-event fuel map.",
        },
        "fuel_vintage_rule": {
            "2018-2019": "LF2016 FBFM13, pre-event by 2-3 calendar years",
            "2023-2024": "LF2022 FBFM13, pre-event by 1-2 calendar years; LF2022 fuel disturbance layers include disturbances through 2022",
            "terrain": "LF2020 elevation, treated as static terrain",
        },
        "cohort_screen_receipts": screens,
        "case_count": len(cases),
        "case_counts_by_split": {
            split: sum(case["split"] == split for case in cases) for split in YEARS_BY_SPLIT
        },
        "cases": cases,
        "training_rule": "The agent learns only from SimFire rollouts on each case's environmental inputs. FPA final size and MTBS historical perimeters stay hidden from observations and rewards.",
        "limitations": [
            "FPA-FOD occurrence points are not verified ignition coordinates and have at least section-scale source precision.",
            "Twenty per year is still a screened western-US large-fire sample, not a representative national benchmark.",
            "Daily gridMET context is converted to a versioned SimFire proxy with explicit assumptions; it is not an hourly historical replay or physical validation.",
            "Fuel map vintages are pre-event and public-service available, but are not per-event vegetation surveys.",
            "MTBS IDs support later visual reference only; no historical perimeter defines the simulator reward.",
        ],
    }
    cohort_path.write_text(json.dumps(cohort, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "cohort": str(cohort_path),
        "cases": len(cases),
        "counts_by_split": cohort["case_counts_by_split"],
        "years": screens,
        "case_ids": [case["source_record_id"] for case in cases],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
