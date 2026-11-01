#!/usr/bin/env python3
"""Audit one BurnMD incident and optionally draw a local-only QA map.

The JSON output contains only source provenance and summary metadata; it does not
copy the archive's geometries. A requested map is a derived display and should
remain in ignored local storage while BurnMD data reuse terms are unresolved.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZipFile


EXPECTED_ARCHIVE_SHA256 = (
    "4eefcbfdabce4966d68e0009e8a4b88dd34294a2cb5dee6aea84dd017eb334c7"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _counts(frame: Any, column: str) -> dict[str, int]:
    if column not in frame.columns:
        return {}
    counts = Counter("<null>" if value is None else str(value) for value in frame[column])
    return dict(sorted(counts.items()))


def _date_summary(frame: Any, column: str) -> dict[str, Any]:
    if column not in frame.columns:
        return {"field_present": False}
    values = frame[column]
    dates = values.dropna().map(str)
    return {
        "field_present": True,
        "rows": int(len(values)),
        "non_null": int(values.notna().sum()),
        "null": int(values.isna().sum()),
        "unique_non_null": int(values.dropna().nunique()),
        "min_value": str(dates.min()) if len(dates) else None,
        "max_value": str(dates.max()) if len(dates) else None,
    }


def _empty_timestamp_list(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (list, tuple)):
        return len(value) == 0
    text = str(value).strip()
    return text in {"", "[]", "None", "nan"}


def _geometry_summary(frame: Any) -> dict[str, Any]:
    bounds = frame.total_bounds.tolist() if len(frame) else []
    return {
        "rows": int(len(frame)),
        "crs": str(frame.crs) if frame.crs else None,
        "bounds_wgs84_minx_miny_maxx_maxy": [float(v) for v in bounds],
        "empty_geometries": int(frame.geometry.is_empty.sum()),
        "invalid_geometries": int((~frame.geometry.is_valid).sum()),
    }


def audit_case(
    archive_path: Path,
    state: str,
    year: int,
    fire: str,
    map_out: Path | None = None,
) -> dict[str, Any]:
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - platform setup message
        raise RuntimeError(
            "geopandas is required. Use the isolated SimFire environment described "
            "in docs/research/SIMFIRE_ENVIRONMENT.md."
        ) from exc

    archive_path = archive_path.expanduser().resolve()
    archive_sha256 = sha256_file(archive_path)
    if archive_sha256 != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(
            "BurnMD archive SHA-256 does not match the official LFS pointer: "
            f"{archive_sha256}"
        )

    prefix = f"BurnMD/{state}/{year}/fires/{fire}"

    def read_layer(layer: str):
        member = f"{prefix}/{fire}_{layer}.shp"
        uri = f"zip://{archive_path}!{member}"
        frame = gpd.read_file(uri)
        if frame.crs is None or frame.crs.to_epsg() != 4326:
            raise ValueError(f"Expected EPSG:4326 for {member}; received {frame.crs}")
        return frame

    lines = read_layer("LINES")
    polygons = read_layer("POLYGONS")
    points = read_layer("POINTS")

    with ZipFile(archive_path) as archive:
        event_folders = {
            (parts[1], parts[2], parts[4])
            for entry in archive.infolist()
            if not entry.is_dir()
            and not entry.filename.startswith("__MACOSX/")
            and PurePosixPath(entry.filename).name != ".DS_Store"
            and (parts := PurePosixPath(entry.filename).parts)
            and len(parts) >= 6
            and parts[0] == "BurnMD"
            and parts[3] == "fires"
        }

    completed_mask = lines["FeatureCat"].isin(
        ["Completed Dozer Line", "Completed Hand Line"]
    )
    completed = lines.loc[completed_mask]
    mitigation_values = (
        lines["Mitigation"] if "Mitigation" in lines.columns else []
    )
    empty_mitigation_rows = sum(_empty_timestamp_list(value) for value in mitigation_values)

    polygon_first = polygons.iloc[0]
    fire_start = str(polygon_first.get("DateStart"))
    fire_contained = str(polygon_first.get("DateContai"))
    line_length_ft = None
    if "LengthFeet" in completed.columns:
        line_length_ft = float(completed["LengthFeet"].fillna(0).sum())

    result: dict[str, Any] = {
        "record_type": "burnmd_case_audit",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "case_id": f"{state[:2].upper()}-{year}-{fire.upper()}",
        "source": {
            "archive_name": archive_path.name,
            "archive_sha256": archive_sha256,
            "official_lfs_pointer_sha256_match": True,
            "archive_license": "unresolved; archive/repository contains no data-specific notice",
            "paper_reports_medium_fire_count": 308,
            "archive_event_folder_count": len(event_folders),
            "archive_vs_paper_event_count_discrepancy": 308 - len(event_folders),
        },
        "event": {
            "state": state,
            "year": year,
            "fire_name": fire,
            "incident_name_values": _counts(polygons, "IncidentNa"),
            "local_incident_ids": _counts(polygons, "LocalIncid"),
            "irwin_ids": _counts(polygons, "IRWINID"),
            "fire_start": fire_start,
            "fire_containment": fire_contained,
            "initial_position_raw": str(polygon_first.get("FireInitPo")),
            "perimeter_collection_timestamp_field": _date_summary(polygons, "PolygonDat"),
            "perimeter_feature_created_field": _date_summary(polygons, "CreateDate"),
            "perimeter_rows_by_feature_category": _counts(polygons, "FeatureCat"),
        },
        "layers": {
            "perimeters": _geometry_summary(polygons),
            "lines": _geometry_summary(lines),
            "points": _geometry_summary(points),
        },
        "lines": {
            "rows_by_feature_category": _counts(lines, "FeatureCat"),
            "rows_by_feature_status": _counts(lines, "FeatureSta"),
            "completed_dozer_rows": int((lines["FeatureCat"] == "Completed Dozer Line").sum()),
            "completed_hand_rows": int((lines["FeatureCat"] == "Completed Hand Line").sum()),
            "completed_length_feet_sum_from_source": line_length_ft,
            "source_line_collection_timestamp": _date_summary(lines, "LineDateTi"),
            "source_feature_created_timestamp": _date_summary(lines, "CreateDate"),
            "source_feature_database_timestamp": _date_summary(lines, "DateCurren"),
            "per_vertex_mitigation_timestamp_field": {
                "field_present": "Mitigation" in lines.columns,
                "rows": int(len(lines)),
                "empty_rows": int(empty_mitigation_rows),
                "non_empty_rows": int(len(lines) - empty_mitigation_rows),
            },
            "timestamp_interpretation": (
                "CreateDate is a source-feature creation timestamp; it is not verified "
                "as the real action start/completion time. The paper describes estimated "
                "per-coordinate times, but this Mineral archive has no populated "
                "per-vertex timestamp lists and no LineDateTi anchors."
            ),
        },
        "readiness": {
            "spatial_data_readable": True,
            "simfire_functional_smoke_only": True,
            "historical_simfire_case_loaded": False,
            "historical_action_replay_ready": False,
            "agent_training_ready": False,
            "blockers": [
                "BurnMD data-specific reuse license is unresolved.",
                "The archive's reported 243 event folders do not match the paper's 308-fire total; reconcile coverage.",
                "Mineral's per-vertex Mitigation timestamp lists are empty and LineDateTi is null for all line records.",
                "The official LANDFIRE service migrated in 2025; the SimFire-bundled 2023 client calls a retired endpoint.",
                "A real LANDFIRE request requires a user-provided email; do not fabricate one.",
                "The current public catalog does not list LF2019 FBFM13; the archived 2019 Limited product is available only via help desk.",
            ],
        },
    }

    if map_out is not None:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.cm import ScalarMappable
        from matplotlib.colors import Normalize
        from matplotlib.lines import Line2D

        map_out = map_out.expanduser().resolve()
        map_out.parent.mkdir(parents=True, exist_ok=True)
        polygons_m = polygons.to_crs("EPSG:3310")
        lines_m = lines.to_crs("EPSG:3310")
        points_m = points.to_crs("EPSG:3310")
        fig, ax = plt.subplots(figsize=(10, 9))

        polygon_times = polygons_m["PolygonDat"].astype(str)
        ordered_times = sorted(polygon_times.unique())
        time_index = {value: index for index, value in enumerate(ordered_times)}
        norm = Normalize(vmin=0, vmax=max(1, len(ordered_times) - 1))
        cmap = plt.get_cmap("viridis")
        polygon_colors = [cmap(norm(time_index[value])) for value in polygon_times]
        polygons_m.boundary.plot(
            ax=ax, color=polygon_colors, linewidth=1.8, alpha=0.95, zorder=1
        )

        styles = {
            "Completed Dozer Line": {"color": "#e63946", "linewidth": 1.3, "linestyle": "-"},
            "Completed Hand Line": {"color": "#ff8c42", "linewidth": 1.2, "linestyle": "-"},
            "Uncontrolled Fire Edge": {"color": "#222222", "linewidth": 1.0, "linestyle": "--"},
            "Proposed Dozer Line": {"color": "#8d99ae", "linewidth": 0.9, "linestyle": ":"},
        }
        for category, style in styles.items():
            selected = lines_m.loc[lines_m["FeatureCat"] == category]
            if len(selected):
                selected.plot(ax=ax, zorder=3, **style)
        if len(points_m):
            points_m.plot(ax=ax, color="#4361ee", markersize=8, alpha=0.7, zorder=4)

        longitude, latitude = map(float, str(polygon_first["FireInitPo"]).split(", "))
        start = gpd.GeoDataFrame(
            geometry=gpd.points_from_xy([longitude], [latitude]), crs="EPSG:4326"
        ).to_crs("EPSG:3310")
        start.plot(ax=ax, marker="*", color="#f7b801", edgecolor="black", markersize=170, zorder=5)

        handles = [
            Line2D([0], [0], color=style["color"], linestyle=style["linestyle"], lw=2, label=category)
            for category, style in styles.items()
            if (lines_m["FeatureCat"] == category).any()
        ]
        handles.append(Line2D([0], [0], marker="*", color="w", markerfacecolor="#f7b801", markeredgecolor="black", markersize=12, label="približno paljenje"))
        handles.append(Line2D([0], [0], marker="o", color="w", markerfacecolor="#4361ee", markersize=6, label="BurnMD tačke"))
        ax.legend(handles=handles, loc="lower right", framealpha=0.95)
        ax.set_title(f"{fire} Fire {year}: stvarne BurnMD geometrije\nPerimetri po vremenu opažanja; linije nisu vremenski replay")
        ax.set_xlabel("Easting (m), California Albers")
        ax.set_ylabel("Northing (m), California Albers")
        ax.set_aspect("equal")
        ax.grid(alpha=0.2)
        colorbar = fig.colorbar(
            ScalarMappable(norm=norm, cmap=cmap), ax=ax, shrink=0.72, pad=0.015
        )
        colorbar.set_label("Redoslijed PolygonDate opažanja (ranije → kasnije)")
        fig.tight_layout()
        fig.savefig(map_out, dpi=180)
        plt.close(fig)
        result["local_preview"] = {
            "created": True,
            "path": str(map_out),
            "warning": "Derived from BurnMD source geometries; retain locally until reuse rights are confirmed.",
        }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/raw/burnmd/BurnMD.zip"))
    parser.add_argument("--state", default="California")
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument("--fire", default="Mineral")
    parser.add_argument("--out", type=Path, help="metadata-only JSON output; omit to print")
    parser.add_argument("--map-out", type=Path, help="optional derived map (keep in ignored local storage)")
    args = parser.parse_args()

    result = audit_case(args.archive, args.state, args.year, args.fire, args.map_out)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
