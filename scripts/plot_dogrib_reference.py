#!/usr/bin/env python3
"""Create a georeferenced QA plate for the public Dogrib/Cell2Fire sample.

This is a data-alignment and visualization fixture, not a simulator replay.
It intentionally draws both published ignition representations so an origin or
row/column convention mismatch cannot be hidden by the plot.
"""

from __future__ import annotations

import argparse
import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch, Rectangle
from pyproj import CRS, Transformer
from shapely.geometry import Polygon
from shapely import transform as transform_geometry


REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data/raw/dogrib-reference"
DEFAULT_OUT = REPO / "reports/real-fire-data/dogrib-reference-alignment.png"


def read_asc(path: Path) -> tuple[np.ndarray, dict[str, float]]:
    with path.open() as stream:
        header = {}
        for _ in range(6):
            key, value = stream.readline().split()[:2]
            header[key.lower()] = float(value)
        values = np.loadtxt(stream)
    expected = (int(header["nrows"]), int(header["ncols"]))
    if values.shape != expected:
        raise ValueError(f"{path}: expected {expected}, received {values.shape}")
    return values, header


def projected_kml_geometry(path: Path, transformer: Transformer):
    root = ET.parse(path).getroot()
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    polygons = []
    for polygon_node in root.findall(".//k:Polygon", ns):
        outer = polygon_node.find("k:outerBoundaryIs/k:LinearRing/k:coordinates", ns)
        if outer is None or not outer.text:
            continue
        exterior = [tuple(map(float, item.split(",")[:2])) for item in outer.text.split()]
        holes = []
        for inner in polygon_node.findall("k:innerBoundaryIs/k:LinearRing/k:coordinates", ns):
            if inner.text:
                holes.append([tuple(map(float, item.split(",")[:2])) for item in inner.text.split()])
        polygon = Polygon(exterior, holes)
        polygons.append(transform_geometry(polygon, transformer.transform, interleaved=False))
    if not polygons:
        raise ValueError(f"No KML polygons found in {path}")
    return polygons


def ignition_point(path: Path, transformer: Transformer) -> tuple[float, float]:
    root = ET.parse(path).getroot()
    ns = {"k": "http://www.opengis.net/kml/2.2"}
    node = root.find(".//k:Point/k:coordinates", ns)
    if node is None or not node.text:
        raise ValueError(f"No KML point found in {path}")
    longitude, latitude = map(float, node.text.strip().split(",")[:2])
    return transformer.transform(longitude, latitude)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=RAW)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    dogrib = args.data_dir / "dogrib"
    vectors = args.data_dir / "Dogrib_v624"
    layers = {}
    header = None
    for name in ("Forest.asc", "elevation.asc", "slope.asc", "saz.asc"):
        layer, layer_header = read_asc(dogrib / name)
        if header is not None and layer_header != header:
            raise ValueError(f"Header mismatch in {name}")
        header = layer_header
        layers[name] = layer
    assert header is not None
    observed = np.loadtxt(dogrib / "real_scar_dogrib.csv")
    supplied_prediction = np.loadtxt(dogrib / "prometheus_dogrib.csv", delimiter=",")
    if observed.shape != layers["Forest.asc"].shape or supplied_prediction.shape != observed.shape:
        raise ValueError("Observed scar, supplied comparison, and terrain grids must align")

    # This companion file is an Arc/Info-style projection description, not WKT.
    # Its parameters identify a custom Transverse Mercator centred on 115°W.
    crs = CRS.from_proj4(
        "+proj=tmerc +lat_0=0 +lon_0=-115 +k=0.9992 +x_0=500000 +y_0=0 "
        "+datum=NAD83 +units=m +no_defs +type=crs"
    )
    to_projected = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    point_x, point_y = ignition_point(vectors / "ignition_point_20011016_1300.kml", to_projected)
    kml_row = int(np.floor((header["yllcorner"] + header["nrows"] * header["cellsize"] - point_y) / header["cellsize"]))
    kml_col = int(np.floor((point_x - header["xllcorner"]) / header["cellsize"]))
    if not (0 <= kml_row < int(header["nrows"]) and 0 <= kml_col < int(header["ncols"])):
        raise ValueError("Projected KML ignition falls outside the raster extent")

    with (dogrib / "Ignitions.csv").open(newline="") as stream:
        ignition_row = next(csv.DictReader(stream))
    ignition_ncell = int(ignition_row["Ncell"])
    csv_row, csv_col = divmod(ignition_ncell - 1, int(header["ncols"]))
    cell_center_x = header["xllcorner"] + (kml_col + 0.5) * header["cellsize"]
    cell_center_y = header["yllcorner"] + (header["nrows"] - kml_row - 0.5) * header["cellsize"]
    point_to_cell_center_m = float(np.hypot(point_x - cell_center_x, point_y - cell_center_y))

    initial = projected_kml_geometry(vectors / "perimeter_rwf085_20011016_1300.kml", to_projected)
    final = projected_kml_geometry(vectors / "perimeter_rwf085_20011017_1152.kml", to_projected)

    west = header["xllcorner"]
    east = west + header["ncols"] * header["cellsize"]
    south = header["yllcorner"]
    north = south + header["nrows"] * header["cellsize"]
    extent = (west, east, south, north)
    fuel = layers["Forest.asc"].astype(int)
    with (dogrib / "fbp_lookup_table.csv").open(newline="") as stream:
        reader = csv.DictReader(stream, skipinitialspace=True)
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        lookup = list(reader)
    color_by_code = {
        int(row["grid_value"]): np.array([int(row["r"]), int(row["g"]), int(row["b"])]) / 255.0
        for row in lookup
    }
    name_by_code = {int(row["grid_value"]): row["fuel_type"] for row in lookup}
    unknown = set(map(int, np.unique(fuel))) - set(color_by_code)
    for code in unknown:
        color_by_code[code] = np.array(mcolors.to_rgb("#e5e5e5" if code == int(header["nodata_value"]) else "#ff00ff"))
    if int(header["nodata_value"]) in unknown:
        name_by_code[int(header["nodata_value"])] = "NoData"

    fuel_rgb = np.zeros((*fuel.shape, 3), dtype=float)
    for code in np.unique(fuel):
        fuel_rgb[fuel == code] = color_by_code[int(code)]
    true_positive = (observed > 0) & (supplied_prediction > 0)
    false_positive = (observed == 0) & (supplied_prediction > 0)
    false_negative = (observed > 0) & (supplied_prediction == 0)
    difference_rgb = np.zeros((*observed.shape, 3), dtype=float)
    difference_rgb[true_positive] = mcolors.to_rgb("#3a923a")
    difference_rgb[false_positive] = mcolors.to_rgb("#e58b2b")
    difference_rgb[false_negative] = mcolors.to_rgb("#b45583")

    sub20 = Rectangle((west + 20 * 100, north - 20 * 100), 20 * 100, 20 * 100,
                      fill=False, edgecolor="white", linewidth=1.8, linestyle="--")
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    axes = axes.ravel()

    axes[0].imshow(fuel_rgb, extent=extent, origin="upper", interpolation="nearest")
    axes[0].add_patch(sub20)
    axes[0].set_title("A. Stvarno gorivo + 2×2 km primjer prozora")
    axes[0].text(0.015, 0.02, "Isprekidano: blok 20×20, 100 m/ćelija\n(prozor za ilustraciju, nije potvrđen replay)",
                 transform=axes[0].transAxes, color="white", fontsize=8,
                 bbox={"facecolor": "black", "alpha": 0.65, "pad": 4})
    fuel_handles = [Patch(facecolor=color_by_code[code], label=f"{name_by_code.get(code, 'nepoznato')} ({code})")
                    for code in sorted(map(int, np.unique(fuel)))]
    axes[0].legend(handles=fuel_handles, loc="upper left", fontsize=6, ncol=2, framealpha=0.9)

    elevation = layers["elevation.asc"]
    im = axes[1].imshow(elevation, extent=extent, origin="upper", cmap="terrain", interpolation="nearest")
    fig.colorbar(im, ax=axes[1], fraction=0.045, pad=0.02, label="metri nad morem")
    axes[1].set_title("B. Visina terena + granice iz KML-a")
    for polygon in initial:
        x, y = polygon.exterior.xy
        axes[1].plot(x, y, color="#ffbf00", linewidth=1.5, label="početni KML perimetar")
    for polygon in final:
        x, y = polygon.exterior.xy
        axes[1].plot(x, y, color="#111111", linewidth=1.1, label="završni KML perimetar")
    axes[1].scatter([point_x], [point_y], marker="*", s=130, color="#d7191c", edgecolor="white",
                    linewidth=0.8, label="tačka paljenja iz KML-a", zorder=5)
    handles, labels = axes[1].get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    axes[1].legend(unique.values(), unique.keys(), loc="upper right", fontsize=7, framealpha=0.9)

    axes[2].imshow(observed, extent=extent, origin="upper", cmap=mcolors.ListedColormap(["#e9ecef", "#cc3d3d"]),
                   vmin=0, vmax=1, interpolation="nearest")
    axes[2].scatter([point_x], [point_y], marker="*", s=125, color="#0066cc", edgecolor="white",
                    linewidth=0.8, label=f"KML tačka → red {kml_row + 1}, kol. {kml_col + 1}", zorder=5)
    csv_x = west + (csv_col + 0.5) * header["cellsize"]
    csv_y = north - (csv_row + 0.5) * header["cellsize"]
    axes[2].scatter([csv_x], [csv_y], marker="x", s=90, color="#111111", linewidth=2,
                    label=f"Ignitions.csv → red {csv_row + 1}, kol. {csv_col + 1}", zorder=6)
    axes[2].set_title("C. Opaženi scar + dvije objavljene lokacije paljenja")
    axes[2].legend(loc="upper right", fontsize=7, framealpha=0.9)

    axes[3].imshow(difference_rgb, extent=extent, origin="upper", interpolation="nearest")
    axes[3].set_title("D. U paketu priložen Prometheus raster i scar")
    axes[3].legend(handles=[
        Patch(facecolor="#3a923a", label="poklapanje"),
        Patch(facecolor="#e58b2b", label="samo Prometheus"),
        Patch(facecolor="#b45583", label="samo opaženi scar"),
        Patch(facecolor="black", label="nema u oba sloja"),
    ], loc="upper left", fontsize=8, framealpha=0.9)

    for ax in axes:
        ax.set_xlim(west, east)
        ax.set_ylim(south, north)
        ax.set_aspect("equal")
        ax.set_xlabel("istočno (m, custom Transverse Mercator NAD83)")
        ax.set_ylabel("sjeverno (m)")
        ax.ticklabel_format(style="plain", axis="both", useOffset=False)
        ax.tick_params(axis="x", labelrotation=20, labelsize=7)
        ax.tick_params(axis="y", labelsize=7)

    scar_cells = int(np.count_nonzero(observed))
    nonfuel_scar_cells = int(np.count_nonzero((observed > 0) & (fuel == 101)))
    supplied_prediction_cells = int(np.count_nonzero(supplied_prediction))
    weather_rows = list(csv.DictReader((dogrib / "Weather.csv").open(newline="")))
    weather_start = np.datetime64(weather_rows[0]["datetime"])
    weather_end = np.datetime64(weather_rows[-1]["datetime"])
    weather_sample_span_h = float((weather_end - weather_start) / np.timedelta64(1, "h"))
    metadata = {
        "fixture": "Dogrib 2001 Cell2Fire public sample",
        "purpose": "geospatial input and visualization QA only; not a simulator replay or independent holdout",
        "source_commit": "84e3c817ad866358d8db28e87c9445b42aaf7908",
        "crs_wkt": crs.to_wkt(),
        "crs_source_definition": (vectors / "fbp_fuel_type.prj").read_text(),
        "grid": {"shape_rc": list(fuel.shape), "cell_size_m": header["cellsize"],
                 "extent_xy_m": [west, south, east, north], "row_order": "north_to_south"},
        "observed_scar_cells": scar_cells,
        "observed_scar_cells_on_nonfuel_101": nonfuel_scar_cells,
        "supplied_prometheus_cells": supplied_prediction_cells,
        "supplied_prometheus_time_alignment": "not established; shown only as a source-package visual layer",
        "ignition": {
            "kml_cell_rc_zero_based": [kml_row, kml_col],
            "kml_cell_rc_one_based": [kml_row + 1, kml_col + 1],
            "csv_ncell_one_based_row_major": ignition_ncell,
            "csv_cell_rc_zero_based": [csv_row, csv_col],
            "csv_cell_rc_one_based": [csv_row + 1, csv_col + 1],
            "cell_delta_csv_minus_kml": [csv_row - kml_row, csv_col - kml_col],
            "kml_point_to_containing_cell_center_m": round(point_to_cell_center_m, 3),
        },
        "weather": {"rows": len(weather_rows), "start": weather_rows[0]["datetime"],
                    "end": weather_rows[-1]["datetime"], "sample_span_hours": weather_sample_span_h,
                    "perimeter_interval": "2001-10-16 13:00 to 2001-10-17 11:52",
                    "perimeter_interval_hours": 22 + 52 / 60,
                    "warning": "the package weather samples span only the first 7 hours between timestamps; final perimeter is 22 h 52 min after start"},
        "firehose_sub20_overlay": {
            "illustrative_full_raster_array_origin_zero_based": [0, 20],
            "warning": "fuel/elevation match this array block, but slope/aspect differ and legacy geospatial origin is not validated",
        },
        "plot": str(args.out.relative_to(REPO)) if args.out.is_relative_to(REPO) else str(args.out),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.suptitle("Dogrib: šta imamo, kako se poravnava i šta još nije potvrđeno", fontsize=16)
    fig.text(0.5, -0.02,
             f"223×357 ćelija × 100 m; scar={scar_cells:,} ćelija, od toga {nonfuel_scar_cells:,} na kodu 101. "
             f"Weather: {len(weather_rows)} satnih zapisa; KML i CSV ignition prikazi se razlikuju za "
             f"{abs(csv_row-kml_row)} red i {abs(csv_col-kml_col)} kolonu. Weather pokriva 7 h između uzoraka, "
             "a perimetri su razmaknuti 22 h 52 min. QC karta; nije naš simulator rezultat.",
             ha="center", va="top", fontsize=9)
    fig.savefig(args.out, dpi=190, bbox_inches="tight")
    plt.close(fig)
    receipt_path = args.out.with_suffix(".json")
    receipt_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"image": str(args.out), "receipt": str(receipt_path),
                      "scar_cells": scar_cells, "nonfuel_scar_cells": nonfuel_scar_cells,
                      "kml_ignition_cell": [kml_row, kml_col], "csv_ignition_cell": [csv_row, csv_col],
                      "weather_rows": len(weather_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
