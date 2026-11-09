#!/usr/bin/env python3
"""Preflight FEDS starts and fetch verified LANDFIRE map pairs.

The script reads only the episode's initial FEDS state. It never uses later
perimeters to construct the start, and it never opens the held-out 2024 split.
Raw vectors, rasters and masks stay under the ignored `.local/` directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/manifests/feds-episode-cohort-v1.json"
DEFAULT_REPORT = ROOT / "reports/real-fire-data/feds-simfire-grid-preflight-v1.json"
OUTPUT_ROOT = ROOT / ".local/feds-simfire-cases"
FUEL_SERVICES = {
    "LF2016": "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2016/LF2016_FBFM13_CONUS/ImageServer/exportImage",
    "LF2022": "https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2022/LF2022_FBFM13_CONUS/ImageServer/exportImage",
}
ELEVATION_SERVICE = "https://lfps.usgs.gov/arcgis/rest/services/Landfire_Topo/LF2020_Elev_CONUS/ImageServer/exportImage"
ALLOWED_FUEL_CODES = {
    -32768, -9999, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
    91, 92, 93, 98, 99, 32767,
}

try:
    from scripts.audit_feds_fpa_fle_crosswalk import _feds_file_path
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "scripts"))
    from audit_feds_fpa_fle_crosswalk import _feds_file_path

from wildfire_rl.feds_simfire_inputs import (
    centered_grid_spec,
    grid_covers_geometry,
    rasterize_observed_masks,
    utm_crs_for_lon_lat,
)


def _key(fire_id: Any, timestamp: Any) -> tuple[str, str]:
    return str(int(fire_id)), str(timestamp)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_exact_geometries(manifest: dict, selected_ids: set[str] | None = None):
    import fiona
    from shapely.geometry import shape
    from shapely.ops import transform as transform_geometry, unary_union
    from pyproj import CRS, Transformer

    selected_cases = [
        case for case in manifest["cases"]
        if selected_ids is None or case["scenario_id"] in selected_ids
    ]
    if not selected_cases:
        raise ValueError("No manifest cases selected.")
    if any(case.get("split") not in {"train", "validation"} for case in selected_cases):
        raise ValueError("Only train and validation episodes are available to this builder.")

    cases_by_year: dict[int, list[dict]] = defaultdict(list)
    for case in selected_cases:
        cases_by_year[int(case["event"]["year"])].append(case)

    result: dict[str, dict] = {}
    for year, year_cases in sorted(cases_by_year.items()):
        target_keys = {
            _key(case["evaluation_reference"]["source_fire_id"], case["evaluation_reference"]["initial_state_time"])
            for case in year_cases
        }
        layer_parts: dict[str, dict[tuple[str, str], list]] = {
            "perimeter": defaultdict(list), "fireline": defaultdict(list),
        }
        source_crs: dict[str, CRS] = {}
        for layer in ("perimeter", "fireline"):
            path = _feds_file_path(year, layer)
            with fiona.open(path) as source:
                crs_input = source.crs_wkt or source.crs or "EPSG:9311"
                source_crs[layer] = CRS.from_user_input(crs_input)
                for feature in source:
                    props = feature["properties"]
                    if props.get("fireID") is None or props.get("t") is None:
                        continue
                    key = _key(props["fireID"], props["t"])
                    if key in target_keys and feature.get("geometry"):
                        layer_parts[layer][key].append(shape(feature["geometry"]))

        for case in year_cases:
            scenario_id = case["scenario_id"]
            event = case["event"]
            ref = case["evaluation_reference"]
            key = _key(ref["source_fire_id"], ref["initial_state_time"])
            perimeter_parts = layer_parts["perimeter"].get(key, [])
            front_parts = layer_parts["fireline"].get(key, [])
            if not perimeter_parts or not front_parts:
                raise ValueError(f"Missing exact-time FEDS geometry for {scenario_id} at {key}.")
            perimeter = unary_union(perimeter_parts)
            front = unary_union(front_parts)
            target_crs = utm_crs_for_lon_lat(float(event["longitude"]), float(event["latitude"]))
            source = source_crs["perimeter"]
            if source != source_crs["fireline"]:
                raise ValueError(f"FEDS vector CRS differs between layers for year {year}.")
            project = Transformer.from_crs(source, target_crs, always_xy=True).transform
            perimeter_utm = transform_geometry(project, perimeter)
            front_utm = transform_geometry(project, front)
            centroid = perimeter_utm.centroid
            centroid_lon, centroid_lat = Transformer.from_crs(
                target_crs, "EPSG:4326", always_xy=True
            ).transform(centroid.x, centroid.y)
            grid = centered_grid_spec(centroid.x, centroid.y, crs=target_crs)
            in_bounds = grid_covers_geometry(grid, perimeter_utm) and grid_covers_geometry(grid, front_utm)
            result[scenario_id] = {
                "case": case,
                "key": key,
                "source_crs": source.to_string(),
                "target_crs": target_crs,
                "perimeter": perimeter_utm,
                "front": front_utm,
                "grid": grid,
                "centroid_wgs84": [float(centroid_lon), float(centroid_lat)],
                "perimeter_bounds_m": [float(v) for v in perimeter_utm.bounds],
                "front_bounds_m": [float(v) for v in front_utm.bounds],
                "perimeter_area_ha": float(perimeter_utm.area / 10000),
                "active_front_length_km": float(front_utm.length / 1000),
                "fits_grid": in_bounds,
            }
    return result


def _preflight_report(geometries: dict[str, dict], manifest: dict) -> dict:
    items = []
    for scenario_id, item in sorted(geometries.items()):
        spec = item["grid"]
        items.append({
            "scenario_id": scenario_id,
            "split": item["case"]["split"],
            "year": item["case"]["event"]["year"],
            "source_fire_id": item["key"][0],
            "initial_state_time": item["key"][1],
            "source_crs": item["source_crs"],
            "grid_crs": spec.crs,
            "grid_shape": [spec.rows, spec.columns],
            "resolution_m": spec.resolution_m,
            "bounds_m": list(spec.bounds_m),
            "perimeter_bounds_m": item["perimeter_bounds_m"],
            "active_front_bounds_m": item["front_bounds_m"],
            "initial_perimeter_area_ha": item["perimeter_area_ha"],
            "active_front_length_km": item["active_front_length_km"],
            "initial_perimeter_centroid_wgs84": {
                "longitude": item["centroid_wgs84"][0],
                "latitude": item["centroid_wgs84"][1],
            },
            "fits_grid": item["fits_grid"],
        })
    by_split = {}
    for split in ("train", "validation"):
        split_items = [item for item in items if item["split"] == split]
        by_split[split] = {
            "episode_count": len(split_items),
            "fits_fixed_map_count": sum(item["fits_grid"] for item in split_items),
        }
    return {
        "schema_version": "feds-simfire-grid-preflight/1.0",
        "kind": "input_geometry_preflight_not_simulation_or_physical_validation",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "episode_manifest": "data/manifests/feds-episode-cohort-v1.json",
        "episode_manifest_sha256": _sha256(MANIFEST),
        "test_cases_loaded": manifest.get("test_cases_loaded") is not False,
        "grid_contract": {
            "rows": 256, "columns": 256, "resolution_m": 180,
            "side_length_m": 46080,
            "center": "centroid of the exact-time initial FEDS perimeter, projected to local UTM",
            "rasterization": "whole initial perimeter as historical scar; exact-time FEDS active line as active cells; all_touched=true",
        },
        "by_split": by_split,
        "all_cases_fit": all(item["fits_grid"] for item in items),
        "cases": items,
        "limitations": [
            "FEDS perimeter and active line are satellite-derived estimates, not ground truth.",
            "This only checks source geometry coverage and fixed-map extent; it does not test fire spread or suppression.",
            "The active FEDS line is an observed satellite-estimated front, not a crew-built suppression line.",
        ],
    }


def _image_params(item: dict, interpolation: str, pixel_type: str) -> dict[str, str]:
    spec = item["grid"]
    xmin, ymin, xmax, ymax = spec.bounds_m
    wkid = spec.crs.removeprefix("EPSG:")
    return {
        "bbox": f"{xmin:.6f},{ymin:.6f},{xmax:.6f},{ymax:.6f}",
        "bboxSR": wkid,
        "imageSR": wkid,
        "size": f"{spec.columns},{spec.rows}",
        "adjustAspectRatio": "false",
        "format": "tiff",
        "pixelType": pixel_type,
        "interpolation": interpolation,
        "f": "image",
    }


def _fetch_image(url: str, params: dict[str, str], destination: Path) -> str:
    import requests

    response = requests.get(url, params=params, timeout=180)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "image/tiff" not in content_type or len(response.content) < 1024:
        raise RuntimeError(f"Expected non-empty GeoTIFF from LANDFIRE; received {content_type!r}.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.write_bytes(response.content)
    os.replace(partial, destination)
    return _sha256(destination)


def _validate_raster(path: Path, item: dict, *, kind: str) -> dict:
    import numpy as np
    import rasterio

    spec = item["grid"]
    with rasterio.open(path) as dataset:
        values = dataset.read(1)
        bounds = [dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top]
        if (dataset.count, dataset.height, dataset.width) != (1, spec.rows, spec.columns):
            raise ValueError(f"Unexpected raster dimensions/count from {path.name}.")
        if dataset.crs is None or dataset.crs.to_string() != spec.crs:
            raise ValueError(f"Expected {spec.crs}, got {dataset.crs} in {path.name}.")
        if any(abs(a - b) > 0.01 for a, b in zip(bounds, spec.bounds_m)):
            raise ValueError(f"Raster extent differs from the fixed study grid in {path.name}.")
        if dataset.nodata is not None and np.any(values == dataset.nodata):
            raise ValueError(f"NoData occurs inside study extent in {path.name}; no implicit filling allowed.")
        if not np.isfinite(values).all():
            raise ValueError(f"Non-finite cells occur in {path.name}.")
        unique = np.unique(values)
        if kind == "fuel":
            unexpected = sorted(set(int(value) for value in unique) - ALLOWED_FUEL_CODES)
            if unexpected:
                raise ValueError(f"Unrecognized FBFM13 codes in {path.name}: {unexpected}.")
        return {
            "shape": [spec.rows, spec.columns],
            "crs": spec.crs,
            "bounds_m": bounds,
            "dtype": values.dtype.name,
            "minimum": float(np.min(values)),
            "maximum": float(np.max(values)),
            "unique_values": [int(value) for value in unique] if kind == "fuel" else None,
        }


def _fetch_case(item: dict, output_root: Path) -> dict:
    import numpy as np

    scenario_id = item["case"]["scenario_id"]
    year = int(item["case"]["event"]["year"])
    fuel_release = "LF2016" if year in {2018, 2019} else "LF2022"
    case_dir = output_root / scenario_id
    case_dir.mkdir(parents=True, exist_ok=True)
    fuel_path = case_dir / f"fuel-{fuel_release.lower()}-fbfm13.tif"
    terrain_path = case_dir / "elevation-lf2020-m.tif"
    masks_path = case_dir / "initial-feds-masks.npz"
    scar, front, transform = rasterize_observed_masks(item["grid"], item["perimeter"], item["front"])
    np.savez_compressed(masks_path, burn_scar=scar.astype(np.uint8), active_front=front.astype(np.uint8))
    fuel_params = _image_params(item, "RSP_Majority", "S16")
    terrain_params = _image_params(item, "RSP_BilinearInterpolation", "F32")
    fuel_hash = _fetch_image(FUEL_SERVICES[fuel_release], fuel_params, fuel_path)
    terrain_hash = _fetch_image(ELEVATION_SERVICE, terrain_params, terrain_path)
    fuel_info = _validate_raster(fuel_path, item, kind="fuel")
    terrain_info = _validate_raster(terrain_path, item, kind="terrain")
    receipt = {
        "schema_version": "feds-simfire-input-receipt/1.0",
        "kind": "observed_start_and_environmental_inputs_not_simulation_result",
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario_id,
        "split": item["case"]["split"],
        "source_fire_id": item["key"][0],
        "initial_state_time": item["key"][1],
        "test_cases_loaded": False,
        "simfire_commit": "04905b19fe8c10dc08d64faddd00303e0561bb66",
        "grid": {
            "crs": item["grid"].crs,
            "shape": [item["grid"].rows, item["grid"].columns],
            "resolution_m": item["grid"].resolution_m,
            "bounds_m": list(item["grid"].bounds_m),
            "raster_transform": list(transform)[:6],
        },
        "initial_feds_state": {
            "perimeter_source": "FEDS-CONUS v1 lf_perimeter at exact initial_state_time",
            "active_front_source": "FEDS-CONUS v1 lf_fireline at exact initial_state_time",
            "mask_file": masks_path.name,
            "mask_sha256": _sha256(masks_path),
            "burn_scar_cells": int(np.count_nonzero(scar)),
            "active_front_cells": int(np.count_nonzero(front)),
            "active_front_overrides_scar_status": True,
        },
        "fuel": {
            "source": f"LANDFIRE {fuel_release} FBFM13 CONUS ImageServer",
            "interpolation": "RSP_Majority",
            "file": fuel_path.name,
            "sha256": fuel_hash,
            "validation": fuel_info,
            "vintage_note": "pre-event landscape fuel product; not a field-verified event-date survey",
        },
        "terrain": {
            "source": "LANDFIRE LF2020 Elevation CONUS ImageServer",
            "interpolation": "RSP_BilinearInterpolation",
            "file": terrain_path.name,
            "sha256": terrain_hash,
            "validation": terrain_info,
            "source_units": "meters",
        },
        "weather": {
            "status": "not_acquired",
            "note": "Daily gridMET acquisition is a separate input-gate; no weather is silently fabricated here.",
        },
        "interpretation_limits": [
            "This is one observed initial state with candidate fuel and terrain grids, not a completed replay.",
            "FEDS inputs are satellite estimates. The active line is not a suppression line.",
            "FPA-FOD final area and future FEDS geometries are not used to rasterize the start.",
        ],
    }
    receipt_path = case_dir / "input-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def fetch_split_cases(
    geometries: dict[str, dict],
    split: str,
    output_root: Path,
    *,
    fetcher=None,
) -> dict:
    """Fetch every selected split case and return a complete success/failure receipt."""
    if split not in {"train", "validation"}:
        raise ValueError("Only train or validation inputs may be fetched.")
    fetcher = _fetch_case if fetcher is None else fetcher
    selected = [
        item for _, item in sorted(geometries.items())
        if item["case"].get("split") == split
    ]
    if not selected:
        raise ValueError(f"No {split} cases selected for LANDFIRE fetch.")
    results = []
    for item in selected:
        scenario_id = item["case"]["scenario_id"]
        try:
            receipt = fetcher(item, output_root)
            results.append({
                "scenario_id": scenario_id,
                "status": "verified",
                "receipt": str((output_root / scenario_id / "input-receipt.json").as_posix()),
                "fuel_sha256": receipt["fuel"]["sha256"],
                "terrain_sha256": receipt["terrain"]["sha256"],
                "mask_sha256": receipt["initial_feds_state"]["mask_sha256"],
            })
        except Exception as exc:
            results.append({
                "scenario_id": scenario_id,
                "status": "failed",
                "error_type": type(exc).__name__,
                "error": str(exc),
            })
    verified_count = sum(row["status"] == "verified" for row in results)
    return {
        "schema_version": "feds-simfire-input-coverage/1.0",
        "kind": "landfire_input_fetch_and_validation_not_simulation_or_physical_validation",
        "split": split,
        "test_cases_loaded": False,
        "selected_case_count": len(selected),
        "verified_case_count": verified_count,
        "failed_case_count": len(results) - verified_count,
        "all_cases_verified": verified_count == len(selected),
        "cases": results,
        "limitations": [
            "FEDS initial states are satellite-derived estimates, not ground truth.",
            "LANDFIRE products are candidate fuel/terrain layers, not field-verified event-date measurements.",
            "Successful raster validation does not validate SimFire spread or suppression outcomes.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true", help="check map coverage for all 119 train/validation cases")
    group.add_argument("--scenario-id", help="fetch inputs for one manifest case after all-case preflight")
    group.add_argument("--fetch-split", choices=("train", "validation"), help="fetch all verified map pairs in one split and write a coverage receipt")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--out-dir", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if manifest.get("test_cases_loaded") is not False:
            raise ValueError("Refusing to read a manifest that includes test cases.")
        if args.fetch_split:
            selected_ids = {
                case["scenario_id"] for case in manifest["cases"]
                if case.get("split") == args.fetch_split
            }
        else:
            selected_ids = None if args.preflight else {args.scenario_id}
        geometries = _read_exact_geometries(manifest, selected_ids)
        if args.preflight:
            report = _preflight_report(geometries, manifest)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"report": str(args.report), "by_split": report["by_split"], "all_cases_fit": report["all_cases_fit"]}, indent=2))
            return 0 if report["all_cases_fit"] else 2
        if args.fetch_split:
            report = fetch_split_cases(geometries, args.fetch_split, args.out_dir)
            report_path = ROOT / f"reports/real-fire-data/feds-simfire-input-{args.fetch_split}-coverage-v1.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({
                "report": str(report_path),
                "split": args.fetch_split,
                "selected_case_count": report["selected_case_count"],
                "verified_case_count": report["verified_case_count"],
                "failed_case_count": report["failed_case_count"],
            }, indent=2))
            return 0 if report["all_cases_verified"] else 1
        item = geometries.get(args.scenario_id)
        if item is None:
            raise ValueError(f"Unknown scenario_id: {args.scenario_id}")
        if not item["fits_grid"]:
            raise ValueError("Initial FEDS perimeter/front exceeds the fixed 256x256x180m map; refusing to crop it.")
        receipt = _fetch_case(item, args.out_dir)
        print(json.dumps({
            "scenario_id": receipt["scenario_id"],
            "receipt": str(args.out_dir / args.scenario_id / "input-receipt.json"),
            "grid": receipt["grid"],
            "burn_scar_cells": receipt["initial_feds_state"]["burn_scar_cells"],
            "active_front_cells": receipt["initial_feds_state"]["active_front_cells"],
            "fuel_codes": receipt["fuel"]["validation"]["unique_values"],
            "weather_status": receipt["weather"]["status"],
        }, indent=2))
        return 0
    except Exception as exc:
        print(f"FEDS-SimFire input build failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
