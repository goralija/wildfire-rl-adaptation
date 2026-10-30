#!/usr/bin/env python3
"""Build one auditable CFSDS day-pair as a 20x20 Cell2Fire input instance.

The simulator input is written below ``--out/input``. The next-day observed
burn fraction is written separately below ``--out/truth`` so it is not exposed
to a training or rollout environment.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window
from scipy.ndimage import binary_dilation


CFSDS_OSF = "https://osf.io/f48ry/"
FBP_2014_URL = (
    "https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/archive/"
    "National_FBP_Fueltypes_version2014b.zip"
)
MRDEM_VRT = (
    "https://canelevation-dem.s3.ca-central-1.amazonaws.com/"
    "mrdem-30/mrdem-30-dtm.vrt"
)
WEATHER_API = "https://archive-api.open-meteo.com/v1/archive"
MODEL_SIZE = 20
MODEL_CELL_M = 100
NODATA_ARRIVAL = 4_000_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_dbf_value_labels(raw: bytes) -> dict[int, str]:
    """Read the small dBase table shipped as the official fuel raster's RAT."""
    record_count = int.from_bytes(raw[4:8], "little")
    header_length = int.from_bytes(raw[8:10], "little")
    record_length = int.from_bytes(raw[10:12], "little")
    fields: list[tuple[str, int, int]] = []
    offset = 1  # dBase record deletion marker
    cursor = 32
    while raw[cursor] != 13:
        descriptor = raw[cursor : cursor + 32]
        name = descriptor[:11].split(b"\0", 1)[0].decode("ascii")
        length = descriptor[16]
        fields.append((name, offset, length))
        offset += length
        cursor += 32
    field_offsets = {name: (start, length) for name, start, length in fields}
    if "VALUE" not in field_offsets or "fueltype" not in field_offsets:
        raise ValueError("Fuel raster RAT is missing VALUE or fueltype fields")
    value_offset, value_length = field_offsets["VALUE"]
    label_offset, label_length = field_offsets["fueltype"]
    result: dict[int, str] = {}
    for index in range(record_count):
        record = raw[header_length + index * record_length : header_length + (index + 1) * record_length]
        value_text = record[value_offset : value_offset + value_length].decode("ascii").strip()
        label = record[label_offset : label_offset + label_length].decode("ascii").strip()
        if value_text:
            result[int(value_text)] = label
    return result


def build_fuel_mapping(rat: dict[int, str], lookup_path: Path) -> tuple[dict[int, int], dict[str, Any]]:
    lookup = pd.read_csv(lookup_path)
    lookup.columns = [str(column).strip() for column in lookup.columns]
    by_fuel_type = {
        str(row.fuel_type).replace("-", "").replace(" ", "").lower(): int(row.grid_value)
        for row in lookup.itertuples(index=False)
    }
    # The upstream 2014b raster stores a class label in its raster attribute
    # table. Convert that label to the numeric grid value used by this pinned
    # Firehose/Cell2Fire lookup table. Wetland/urban map to generic non-fuel;
    # vegetated non-fuel maps to Cell2Fire's explicit vegetated non-fuel class.
    fixed_grid_values = {
        "water": 102,
        "non-fuel": 101,
        "wetland": 101,
        "urban": 101,
        "veg non-fuel": 105,
    }
    mapping: dict[int, int] = {}
    labels: dict[str, Any] = {}
    for source_value, source_label in rat.items():
        key = source_label.replace("-", "").replace(" ", "").lower()
        if source_label.lower() in fixed_grid_values:
            mapping[source_value] = fixed_grid_values[source_label.lower()]
        elif key in by_fuel_type:
            mapping[source_value] = by_fuel_type[key]
        else:
            raise ValueError(f"No pinned Cell2Fire fuel code for 2014b class {source_label!r}")
        labels[str(source_value)] = {
            "source_label": source_label,
            "simulator_grid_value": mapping[source_value],
            "simulator_fuel_type": str(lookup.loc[lookup.grid_value == mapping[source_value], "fuel_type"].iloc[0]),
        }
    return mapping, labels


def write_ascii(path: Path, array: np.ndarray, transform: Affine, nodata: int | float = -9999) -> None:
    values = np.asarray(array)
    if values.ndim != 2:
        raise ValueError(f"Expected a 2D grid for {path}")
    cell_x = float(transform.a)
    cell_y = float(-transform.e)
    if not math.isclose(cell_x, cell_y, rel_tol=0, abs_tol=1e-6):
        raise ValueError("ASCII grid requires square cells")
    xll = float(transform.c)
    yll = float(transform.f - values.shape[0] * cell_y)
    with path.open("w", newline="") as stream:
        stream.write(f"ncols {values.shape[1]}\n")
        stream.write(f"nrows {values.shape[0]}\n")
        stream.write(f"xllcorner {xll:.3f}\n")
        stream.write(f"yllcorner {yll:.3f}\n")
        stream.write(f"cellsize {cell_x:.3f}\n")
        stream.write(f"NODATA_value {nodata}\n")
        if np.issubdtype(values.dtype, np.integer):
            np.savetxt(stream, values, fmt="%d")
        else:
            np.savetxt(stream, values, fmt="%.3f")


def daily_row(raw_root: Path, event_id: str, year: int, day_of_year: int) -> dict[str, Any]:
    group_zip = raw_root / str(year) / f"Firegrowth_groups_v1_1_{year}.zip"
    with zipfile.ZipFile(group_zip) as archive:
        members = [item for item in archive.namelist() if item.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one daily-summary CSV in {group_zip}")
        table = pd.read_csv(archive.open(members[0]), dtype={"ID": str})
    rows = table[(table.ID == event_id) & (table.DOB == day_of_year)]
    if len(rows) != 1:
        raise ValueError(f"Expected one {event_id} DOB={day_of_year} summary row, found {len(rows)}")
    row = rows.iloc[0]
    keys = ("year", "DOB", "fireday", "firearea", "fwi", "isi", "ffmc", "dmc", "dc", "bui", "prec", "tmax", "ws", "rh", "lat", "lon")
    result: dict[str, Any] = {}
    for key in keys:
        value = row[key]
        result[key] = None if pd.isna(value) else float(value)
    return result


def get_weather_rows(path: Path, target_date: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    response = json.loads(path.read_text())
    hourly = response.get("hourly", {})
    keys = (
        "temperature_2m",
        "relative_humidity_2m",
        "wind_speed_10m",
        "wind_direction_10m",
        "precipitation",
    )
    if any(key not in hourly for key in ("time", *keys)):
        raise ValueError(f"{path} lacks one or more required hourly weather fields")
    selected = [index for index, stamp in enumerate(hourly["time"]) if stamp.startswith(target_date.isoformat())]
    if len(selected) != 24:
        raise ValueError(f"Expected 24 local hourly weather records for {target_date}, found {len(selected)}")
    rows = []
    for index in selected:
        values = {key: hourly[key][index] for key in keys}
        if any(value is None or not math.isfinite(float(value)) for value in values.values()):
            raise ValueError(f"Missing hourly weather value at {hourly['time'][index]}")
        direction_from = float(values["wind_direction_10m"])
        rows.append({
            "datetime": pd.Timestamp(hourly["time"][index]).strftime("%Y-%m-%d %H:%M"),
            "APCP": float(values["precipitation"]),
            "TMP": float(values["temperature_2m"]),
            "RH": float(values["relative_humidity_2m"]),
            "WS": float(values["wind_speed_10m"]),
            # Open-Meteo reports meteorological direction (where wind comes
            # from); the FBP vector calculation expects direction of travel.
            "WD": int(round((direction_from + 180.0) % 360.0)),
        })
    info = {
        "api_url": WEATHER_API,
        "model": "ERA5-Seamless",
        "timezone": response.get("timezone"),
        "utc_offset_seconds": response.get("utc_offset_seconds"),
        "request_location": {"lat": float(response.get("latitude")), "lon": float(response.get("longitude"))},
        "grid_elevation_m": response.get("elevation"),
        "rows_for_target_day": len(rows),
        "wind_direction_conversion": "met-from direction + 180 degrees -> downwind bearing, modulo 360",
        "temperature_humidity_source_note": "ERA5-Land within ERA5-Seamless",
        "wind_precipitation_source_note": "ERA5 within ERA5-Seamless",
    }
    return rows, info


def make_case(args: argparse.Namespace) -> dict[str, Any]:
    raw_root = args.raw_root
    screen_path = args.screen
    screen = json.loads(screen_path.read_text())
    candidates = [item for item in screen["screening_candidates"] if item["event_id"] == args.event_id]
    if args.target_doy is not None:
        candidates = [item for item in candidates if item["target_doy"] == args.target_doy]
    if len(candidates) != 1:
        raise ValueError(f"Expected exactly one screened candidate for {args.event_id}, found {len(candidates)}")
    candidate = candidates[0]
    year = int(candidate["year"])
    target_doy = int(candidate["target_doy"])
    target_date = date(year, 1, 1) + timedelta(days=target_doy - 1)
    summary = daily_row(raw_root, args.event_id, year, target_doy)
    if summary["year"] != year:
        raise ValueError("CFSDS summary year does not match candidate year")

    raster_zip = raw_root / str(year) / f"{year}_fireDOYrasters.zip"
    source_member = candidate["source_raster"]
    with zipfile.ZipFile(raster_zip) as archive:
        member = next((name for name in archive.namelist() if Path(name).name == source_member), None)
        if member is None:
            raise FileNotFoundError(f"{source_member} missing from {raster_zip}")
        raster_bytes = archive.read(member)
    with rasterio.open(io.BytesIO(raster_bytes)) as src:
        source_crs = src.crs
        source_transform = Affine(*candidate["crop_transform"])
        source_window = Window(candidate["col_off"], candidate["row_off"], 23, 23)
        arrival = src.read(1, window=source_window)
        if arrival.shape != (23, 23):
            raise ValueError(f"CFSDS native window shape is {arrival.shape}, expected 23x23")

    observed = (arrival == target_doy) & (arrival < NODATA_ARRIVAL)
    previous = (arrival == target_doy - 1) & (arrival < NODATA_ARRIVAL)
    target_native = observed & binary_dilation(previous, structure=np.ones((3, 3), dtype=bool))
    # PROTOTYPE CAVEAT: this selects the n-1 front by looking at target day n.
    # The target geometry therefore leaks into InitialState.csv. Preserve this
    # only for reproducing existing cases; replace it with a preregistered,
    # target-blind n-1 front before any unbiased agent benchmark.
    front_native = previous & binary_dilation(target_native, structure=np.ones((3, 3), dtype=bool))
    scar_native = (arrival > 0) & (arrival <= target_doy - 1) & (arrival < NODATA_ARRIVAL) & ~front_native
    if not target_native.any() or not front_native.any() or int(target_native.sum()) != int(observed.sum()):
        raise ValueError("Selected day pair failed adjacency / no-long-range-spotting checks")

    # Center a 20x20 100 m grid inside the candidate's 23x23 native 90 m crop.
    # This preserves the model's fixed 2 km policy footprint without silently
    # changing the trained policy's cell size.
    model_transform = Affine(
        MODEL_CELL_M, 0, source_transform.c + (23 * 90 - MODEL_SIZE * MODEL_CELL_M) / 2,
        0, -MODEL_CELL_M, source_transform.f - (23 * 90 - MODEL_SIZE * MODEL_CELL_M) / 2,
    )
    fractions: dict[str, np.ndarray] = {}
    for name, mask in (("scar", scar_native), ("front", front_native), ("target", target_native)):
        destination = np.zeros((MODEL_SIZE, MODEL_SIZE), dtype=np.float32)
        reproject(
            mask.astype(np.float32), destination,
            src_transform=source_transform, src_crs=source_crs,
            dst_transform=model_transform, dst_crs=source_crs,
            src_nodata=None, dst_nodata=0,
            resampling=Resampling.average,
        )
        fractions[name] = np.clip(destination, 0.0, 1.0)

    # Initial state is a majority-area decision on the 100 m grid. Keep the
    # continuous next-day coverage outside the input folder for evaluation.
    burnt = fractions["scar"] >= 0.5
    burning = fractions["front"] >= 0.5
    target_binary = fractions["target"] >= 0.5
    if np.any(burnt & burning) or np.any((burnt | burning) & target_binary):
        raise ValueError("Resampling caused mutually exclusive historical states to overlap")
    if not target_binary.any() or not burning.any():
        raise ValueError("No target or active-front cells remain after resampling")
    structure = np.ones((3, 3), dtype=bool)
    if np.any(target_binary[[0, -1], :]) or np.any(target_binary[:, [0, -1]]):
        raise ValueError("Target day touches the 20x20 simulator grid edge")
    if np.any(burning[[0, -1], :]) or np.any(burning[:, [0, -1]]):
        raise ValueError("Active front touches the 20x20 simulator grid edge")
    if not np.any(burning & binary_dilation(target_binary, structure=structure)):
        raise ValueError("Resampled active front is no longer adjacent to the resampled target")

    lookup_path = args.lookup
    with zipfile.ZipFile(args.fuel_zip) as archive:
        rat = read_dbf_value_labels(archive.read("nat_fbpfuels_2014b.tif.vat.dbf"))
    fuel_mapping, mapping_report = build_fuel_mapping(rat, lookup_path)
    fuel_vsi = f"/vsizip/{args.fuel_zip.resolve()}/nat_fbpfuels_2014b.tif"
    with rasterio.open(fuel_vsi) as fuel_src:
        source_fuel = np.zeros((MODEL_SIZE, MODEL_SIZE), dtype=np.uint16)
        reproject(
            rasterio.band(fuel_src, 1), source_fuel,
            src_transform=fuel_src.transform, src_crs=fuel_src.crs,
            dst_transform=model_transform, dst_crs=source_crs,
            src_nodata=fuel_src.nodata, dst_nodata=0,
            resampling=Resampling.nearest,
        )
        fuel_resolution = [float(value) for value in fuel_src.res]
        fuel_crs = fuel_src.crs.to_string()
    missing_codes = sorted(int(code) for code in np.unique(source_fuel) if int(code) not in fuel_mapping)
    if missing_codes:
        raise ValueError(f"2014b fuel map contains unhandled code(s) in selected window: {missing_codes}")
    forest = np.vectorize(fuel_mapping.__getitem__, otypes=[np.uint16])(source_fuel)
    if np.any((burnt | burning | target_binary) & np.isin(forest, [101, 102, 105])):
        raise ValueError("A historical burned/front/target cell maps to non-fuel or water")

    weather_rows, weather_info = get_weather_rows(args.weather_json, target_date)
    data_summary = summary
    if any(data_summary[key] is None for key in ("ffmc", "dmc", "dc", "isi", "bui", "fwi")):
        raise ValueError("CFSDS day summary is missing a required daily FWI component")

    weather_path = args.weather_json
    weather_payload = json.loads(weather_path.read_text())
    requested_lat, requested_lon = float(data_summary["lat"]), float(data_summary["lon"])
    api_lat, api_lon = float(weather_payload["latitude"]), float(weather_payload["longitude"])
    mean_lat = math.radians((requested_lat + api_lat) / 2)
    distance_km = math.sqrt(
        ((requested_lat - api_lat) * 111.32) ** 2
        + ((requested_lon - api_lon) * 111.32 * math.cos(mean_lat)) ** 2
    )

    transformer = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
    lat_grid = np.zeros((MODEL_SIZE, MODEL_SIZE), dtype=np.float64)
    lon_grid = np.zeros((MODEL_SIZE, MODEL_SIZE), dtype=np.float64)
    for row in range(MODEL_SIZE):
        for col in range(MODEL_SIZE):
            x = model_transform.c + (col + 0.5) * MODEL_CELL_M
            y = model_transform.f - (row + 0.5) * MODEL_CELL_M
            lon_grid[row, col], lat_grid[row, col] = transformer.transform(x, y)

    dem_path = args.dem_vrt
    dem_source_path = dem_path if str(dem_path).startswith("/vsi") else (
        "/vsicurl/" + str(dem_path) if str(dem_path).startswith("https://") else str(dem_path)
    )
    elevation = np.full((MODEL_SIZE, MODEL_SIZE), np.nan, dtype=np.float32)
    with rasterio.open(dem_source_path) as dem:
        reproject(
            rasterio.band(dem, 1), elevation,
            src_transform=dem.transform, src_crs=dem.crs,
            src_nodata=dem.nodata, dst_transform=model_transform, dst_crs=source_crs,
            dst_nodata=np.nan, resampling=Resampling.bilinear,
        )
        dem_crs = dem.crs.to_string()
        dem_resolution = [float(value) for value in dem.res]
    if not np.isfinite(elevation).all():
        raise ValueError("MRDEM reprojection returned missing elevation values")

    # Cell2Fire expects percent slope and uses SAZ as an uphill bearing (0=N,
    # 90=E); derive both from the same 100 m resampled elevation surface.
    dz_drow, dz_dcol = np.gradient(elevation.astype(np.float64))
    grad_north = -dz_drow / MODEL_CELL_M
    grad_east = dz_dcol / MODEL_CELL_M
    slope_percent = np.hypot(grad_east, grad_north) * 100.0
    slope_percent = np.clip(slope_percent, 0, 70)
    slope_degrees = np.degrees(np.arctan(slope_percent / 100.0))
    upslope_aspect = np.degrees(np.arctan2(grad_east, grad_north)) % 360.0
    upslope_aspect[slope_percent < 0.1] = 0.0
    slope_grid = np.rint(slope_percent).astype(np.int16)
    aspect_grid = np.rint(upslope_aspect).astype(np.int16) % 360
    elevation_grid = np.rint(elevation).astype(np.int32)

    out_root = args.out
    out_root.mkdir(parents=True, exist_ok=False)
    input_root = out_root / "input"
    truth_root = out_root / "truth"
    input_root.mkdir()
    truth_root.mkdir()
    (input_root / "fbp_lookup_table.csv").write_bytes(lookup_path.read_bytes())
    for name, grid in (("Forest.asc", forest), ("elevation.asc", elevation_grid), ("slope.asc", slope_grid), ("saz.asc", aspect_grid)):
        write_ascii(input_root / name, grid, model_transform)

    # Create Data.csv directly. The upstream helper uses chained pandas
    # assignment that silently stops populating GFL/PC/PDF/cur under current
    # pandas releases; spelling the small standard parameter table out here
    # avoids shipping NaNs into Cell2Fire.
    lookup = pd.read_csv(lookup_path)
    lookup.columns = [str(column).strip() for column in lookup.columns]
    fuel_type_by_grid = {
        int(row.grid_value): str(row.fuel_type).replace("-", "").replace(" ", "")
        for row in lookup.itertuples(index=False)
    }
    gfl_by_type = {
        "C1": 0.75, "C2": 0.8, "C3": 1.15, "C4": 1.2, "C5": 1.2,
        "C6": 1.2, "C7": 1.2, "O1a": 0.35, "O1b": 0.35,
    }
    data_fuel = [fuel_type_by_grid[int(value)] for value in forest.ravel()]
    gfl_values: list[float] = []
    pc_values: list[float] = []
    pdf_values: list[float] = []
    curing_values: list[float] = []
    for fuel_type in data_fuel:
        normalized = fuel_type.replace("-", "")
        if normalized.startswith(("M1", "M2")):
            if args.mixedwood_percent_conifer is None:
                raise ValueError(
                    "This map has M1/M2 cells but no per-cell conifer percentage. "
                    "Supply --mixedwood-percent-conifer only when a documented value is available."
                )
            pc_values.append(float(args.mixedwood_percent_conifer))
        else:
            pc_values.append(np.nan)
        if normalized.startswith(("M3", "M4")):
            if args.dead_fir_percent is None:
                raise ValueError(
                    "This map has M3/M4 cells but no per-cell dead-fir percentage. "
                    "Supply --dead-fir-percent only when a documented value is available."
                )
            pdf_values.append(float(args.dead_fir_percent))
        else:
            pdf_values.append(np.nan)
        if normalized in ("O1a", "O1b"):
            if args.grass_curing_percent is None:
                raise ValueError(
                    "This map has O1 grass cells but no curing measurement. "
                    "Supply --grass-curing-percent only when a documented value is available."
                )
            curing_values.append(float(args.grass_curing_percent))
        else:
            curing_values.append(np.nan)
        gfl_values.append(gfl_by_type.get(normalized, np.nan))
    data_csv = pd.DataFrame({
        "fueltype": data_fuel,
        "mon": target_date.month,
        "jd": target_doy,
        "M": "",
        "jd_min": 0,
        "lat": lat_grid.ravel(),
        "lon": lon_grid.ravel(),
        "elev": elevation_grid.ravel(),
        "ffmc": float(summary["ffmc"]),
        "ws": float(summary["ws"]),
        "waz": int(round((float(weather_rows[0]["WD"]) + 180.0) % 360.0)),
        "bui": float(summary["bui"]),
        "ps": slope_grid.ravel(),
        "saz": aspect_grid.ravel(),
        "pc": pc_values,
        "pdf": pdf_values,
        "gfl": gfl_values,
        "cur": curing_values,
        "time": 20,
        "pattern": "",
    })
    data_csv.to_csv(input_root / "Data.csv", index=False)

    weather_csv = input_root / "Weather.csv"
    with weather_csv.open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["Scenario", "datetime", "APCP", "TMP", "RH", "WS", "WD", "FFMC", "DMC", "DC", "ISI", "BUI", "FWI"])
        for item in weather_rows:
            writer.writerow([
                f"{args.event_id}_DOB{target_doy}", item["datetime"],
                f"{item['APCP']:.4f}", f"{item['TMP']:.3f}", f"{item['RH']:.3f}",
                f"{item['WS']:.3f}", item["WD"], f"{summary['ffmc']:.6f}",
                f"{summary['dmc']:.6f}", f"{summary['dc']:.6f}",
                f"{summary['isi']:.6f}", f"{summary['bui']:.6f}", f"{summary['fwi']:.6f}",
            ])

    with (input_root / "InitialState.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["state", "ncell"])
        for row in range(MODEL_SIZE):
            for col in range(MODEL_SIZE):
                cell = row * MODEL_SIZE + col + 1
                if burnt[row, col]:
                    writer.writerow(["burnt", cell])
                elif burning[row, col]:
                    writer.writerow(["burning", cell])

    write_ascii(truth_root / "target_next_day_fraction.asc", fractions["target"], model_transform, nodata=0)
    write_ascii(truth_root / "target_next_day_majority.asc", target_binary.astype(np.uint8), model_transform, nodata=0)
    write_ascii(truth_root / "initial_scar_fraction.asc", fractions["scar"], model_transform, nodata=0)
    write_ascii(truth_root / "initial_front_fraction.asc", fractions["front"], model_transform, nodata=0)
    (out_root / "fuel-code-mapping.json").write_text(json.dumps(mapping_report, indent=2, sort_keys=True) + "\n")
    (out_root / "model-grid.wkt").write_text(source_crs.to_wkt() + "\n")

    state_counts = {
        "burnt_cells_majority": int(burnt.sum()),
        "burnt_area_equivalent_ha": round(float(fractions["scar"].sum()), 4),
        "burning_cells_majority": int(burning.sum()),
        "burning_area_equivalent_ha": round(float(fractions["front"].sum()), 4),
        "target_cells_majority": int(target_binary.sum()),
        "target_area_equivalent_ha": round(float(fractions["target"].sum()), 4),
        "target_area_source_ha": round(float(target_native.sum()) * 0.81, 4),
        "initial_nonfuel_cells": 0,
        "target_nonfuel_cells": 0,
        "target_edge_cells": 0,
        "front_edge_cells": 0,
    }
    cfsds_manifest_path = Path("reports/real-fire-data/cfsds-download-manifest.json")
    cfsds_manifest = json.loads(cfsds_manifest_path.read_text())
    file_entries = {item["name"]: item for item in cfsds_manifest["entries"]}
    raster_entry = file_entries[raster_zip.name]
    group_zip = raw_root / str(year) / f"Firegrowth_groups_v1_1_{year}.zip"
    group_entry = file_entries[group_zip.name]
    fuel_entry = {
        "url": FBP_2014_URL,
        "sha256": sha256(args.fuel_zip),
        "resolution_m": fuel_resolution,
        "crs": fuel_crs,
        "release": "National FBP fuel-type grid v2014b",
    }
    model_weather = pd.DataFrame(weather_rows)
    weather_summary = {
        key: round(float(model_weather[key].mean()), 4)
        for key in ("TMP", "RH", "WS")
    }
    weather_summary["APCP_sum_mm"] = round(float(model_weather["APCP"].sum()), 4)
    case = {
        "case_id": f"{args.event_id}_dob{target_doy}_20x20",
        "split": candidate["split"],
        "dataset": {"name": "Canadian Fire Spread Dataset", "release": "v1.1", "url": CFSDS_OSF},
        "event": {
            "event_id": args.event_id,
            "year": year,
            "target_doy": target_doy,
            "target_date_local": target_date.isoformat(),
            "fire_day_number": int(summary["fireday"]),
            "reported_day_growth_ha": float(summary["firearea"]),
            "suppression_status": "unknown; no event-level agency record joined",
            "summary_weather": {key: summary[key] for key in ("ffmc", "dmc", "dc", "isi", "bui", "fwi", "prec", "tmax", "ws", "rh")},
            "summary_centroid_wgs84": {"lat": requested_lat, "lon": requested_lon},
        },
        "grid": {
            "rows": MODEL_SIZE,
            "cols": MODEL_SIZE,
            "cell_size_m": MODEL_CELL_M,
            "extent_m": MODEL_SIZE * MODEL_CELL_M,
            "crs_wkt": source_crs.to_wkt(),
            "native_cfsds_grid": {"rows": 23, "cols": 23, "cell_size_m": 90, "target_pixels": int(target_native.sum()), "front_pixels": int(front_native.sum()), "scar_pixels": int(scar_native.sum())},
            "alignment": "center 20x20 100m model grid within the screened 23x23 90m CFSDS crop",
            "historical_mask_resampling": "area-weighted fraction; model start state uses >=50% cell coverage; target truth fraction remains separate",
            "state_counts": state_counts,
        },
        "sources": {
            "cfsds_arrival_raster": {"name": raster_zip.name, "url": raster_entry["url"], "sha256": raster_entry["sha256"], "member": source_member},
            "cfsds_daily_summary": {"name": group_zip.name, "url": group_entry["url"], "sha256": group_entry["sha256"], "member": "single CSV"},
            "fuel_map": fuel_entry,
            "elevation": {"name": "NRCan Canadian Medium Resolution Digital Elevation Model DTM", "collection": "mrdem-30", "stac_url": "https://datacube.services.geo.ca/stac/api/collections/mrdem-30", "asset_url": str(dem_path), "crs": dem_crs, "resolution_m": dem_resolution, "resampling": "30m DTM bilinear to the 100m simulator grid", "retrieved_on": date.today().isoformat()},
            "weather": {**weather_info, "raw_json": str(weather_path), "raw_sha256": sha256(weather_path), "api_grid_distance_from_cfsds_centroid_km": round(distance_km, 3), "hourly_summary": weather_summary, "source_license_note": "Open-Meteo free API use requires attribution and is intended for non-commercial use; ERA5 data are Copernicus reanalysis."},
            "simulator_lookup": {"path": str(lookup_path), "sha256": sha256(lookup_path)},
        },
        "conversion": {
            "fbp_mapping": mapping_report,
            "non_fuel_rule": "Water remains Water; 2014b Non-fuel/Wetland/Urban map to generic Cell2Fire Non-fuel; Veg non-fuel maps to Cell2Fire Vegetated Non-fuel.",
            "terrain": "slope is percent rise/run, capped at the upstream FBP 70% limit; SAZ is the 0-359 degree uphill bearing derived from the 100m DEM.",
            "special_fuel_parameters": {
                "mixedwood_percent_conifer": args.mixedwood_percent_conifer,
                "dead_fir_percent": args.dead_fir_percent,
                "grass_curing_percent": args.grass_curing_percent,
            },
            "weather": "24 local-time hourly ERA5-Seamless weather rows; APCP mm, TMP Celsius, RH percent, WS km/h, WD converted from meteorological-from to simulator downwind bearing. Daily FWI codes are the CFSDS fire-day means and held constant across these 24 rows because CFSDS does not supply hourly FWI codes.",
            "initial_state": "burned scar and day n-1 active front are separate; the observed day n target is stored only in truth/ and is not copied into Cell2Fire input.",
        },
        "quality_gates": {
            "target_has_no_disconnected_spot_pixels": True,
            "active_front_adjacent_to_target_after_resampling": True,
            "all_initial_and_target_cells_on_burnable_fuel": True,
            "target_and_front_interior_to_simulator_grid": True,
            "weather_rows_complete": len(weather_rows) == 24,
            "historical_suppression_joined": False,
            "physical_validity_claimed": False,
        },
        "limitations": [
            "CFSDS day-of-burning is a satellite-hotspot interpolation, not a ground-truth hourly fire perimeter.",
            "Fuel map is 250m and was regridded to a 100m policy grid; this does not create 100m fuel detail.",
            "Weather is a roughly 9-25km reanalysis point estimate, several kilometres from the fire-growth centroid.",
            "Daily CFSDS FWI codes are held constant over the 24 hourly simulator weather rows.",
            "Suppression status is unknown, so this case is not proof of how a counterfactual response would have changed the actual fire.",
        ],
    }
    case_path = out_root / "case.json"
    case_path.write_text(json.dumps(case, indent=2, sort_keys=True) + "\n")
    return case


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-id", default="2018_747")
    parser.add_argument("--target-doy", type=int, default=228)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument("--screen", type=Path, default=Path("reports/real-fire-data/cfsds-cohort-screen.json"))
    parser.add_argument("--fuel-zip", type=Path, default=Path("data/raw/cwfis-fuels/National_FBP_Fueltypes_version2014b.zip"))
    parser.add_argument("--lookup", type=Path, default=Path("external/firehose/data/Sub20x20/fbp_lookup_table.csv"))
    parser.add_argument("--weather-json", type=Path, default=Path("data/raw/real-case/2018_747/era5_seamless_2018-08-16_local.json"))
    parser.add_argument("--dem-vrt", default=MRDEM_VRT)
    parser.add_argument("--mixedwood-percent-conifer", type=float)
    parser.add_argument("--dead-fir-percent", type=float)
    parser.add_argument("--grass-curing-percent", type=float)
    parser.add_argument("--out", type=Path, default=Path("runs/real-case/2018_747-day228"))
    args = parser.parse_args()
    case = make_case(args)
    print(json.dumps({
        "case_id": case["case_id"],
        "input_dir": str(args.out / "input"),
        "truth_dir": str(args.out / "truth"),
        "case_manifest": str(args.out / "case.json"),
        "state_counts": case["grid"]["state_counts"],
        "quality_gates": case["quality_gates"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
