#!/usr/bin/env python3
"""Fetch a fixed fire-location LANDFIRE tile and cache it for SimFire.

The SimFire 2.0.1 dependency uses the retired pre-2025 LANDFIRE endpoint. This
project-owned bridge requests a fixed-size tile around the recorded event location
from the current LFPS v2 API and puts it in SimFire's operational-data cache.
The tile is derived from the recorded location only: later fire perimeters and fireline
locations are deliberately not used to choose its bounds. A real request needs
the caller's own LANDFIRE_EMAIL; --dry-run makes no network call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ARCHIVE_SHA256 = (
    "4eefcbfdabce4966d68e0009e8a4b88dd34294a2cb5dee6aea84dd017eb334c7"
)
LFPS_BASE = "https://lfps.usgs.gov"
LFPS_SUBMIT = f"{LFPS_BASE}/api/job/submit"
LFPS_STATUS = f"{LFPS_BASE}/api/job/status"
LFPS_API_DOCS = f"{LFPS_BASE}/docs/api"
DEGREES_PER_30M = 0.00027777777803598015
# SimFire 2.0.1 adds this value to its lower-right corner. Despite the upstream
# comment calling it about 90 m, 100 arc-seconds are about 3.1 km north-south.
# Keep the exact value so our cache key and requested AOI match SimFire.
SIMFIRE_LOWER_RIGHT_PADDING_DEGREES = DEGREES_PER_30M * 100
DEFAULT_TILE_HEIGHT_M = 3840  # 128 cells × 30 m, as in the published SimHarness example
DEFAULT_TILE_WIDTH_M = 3840


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mineral_ignition(archive_path: Path) -> tuple[float, float, str]:
    """Return recorded latitude, longitude and verified source checksum."""
    try:
        import geopandas as gpd
    except ImportError as exc:  # pragma: no cover - platform setup message
        raise RuntimeError(
            "geopandas is required. Use the isolated SimFire environment described "
            "in docs/research/SIMFIRE_ENVIRONMENT.md."
        ) from exc

    archive_path = archive_path.expanduser().resolve()
    source_sha256 = sha256_file(archive_path)
    if source_sha256 != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(
            "BurnMD archive SHA-256 does not match the official LFS pointer: "
            f"{source_sha256}"
        )

    member = "BurnMD/California/2020/fires/Mineral/Mineral_POLYGONS.shp"
    frame = gpd.read_file(f"zip://{archive_path}!{member}")
    if frame.crs is None or frame.crs.to_epsg() != 4326:
        raise ValueError(f"Expected Mineral ignition layer in EPSG:4326; received {frame.crs}")
    if "FireInitPo" not in frame.columns or frame.empty:
        raise ValueError(f"No BurnMD ignition coordinate found in {member}")
    raw_position = str(frame.iloc[0]["FireInitPo"])
    try:
        longitude, latitude = (float(part.strip()) for part in raw_position.split(","))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Could not parse Mineral FireInitPo: {raw_position!r}") from exc
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError(f"Mineral ignition coordinate is outside WGS84: {raw_position!r}")
    return latitude, longitude, source_sha256


def scenario_location(manifest_path: Path) -> tuple[float, float, int, int, int, str, str, str]:
    """Read event point/date/grid from a common scenario manifest."""
    payload = json.loads(manifest_path.expanduser().read_text(encoding="utf-8"))
    event = payload.get("event", {})
    point = event.get("location_wgs84", {})
    grid = payload.get("grid", {})
    latitude = point.get("latitude")
    longitude = point.get("longitude")
    value = event.get("discovery_time", {}).get("value")
    if latitude is None or longitude is None or not value:
        raise ValueError("Scenario manifest needs a reported event location and discovery date.")
    try:
        event_year = datetime.fromisoformat(str(value)[:10]).year
        height_m = int(grid["rows"] * grid["resolution_m"])
        width_m = int(grid["columns"] * grid["resolution_m"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Scenario manifest needs a valid ISO date and grid rows/columns/resolution.") from exc
    if grid.get("resolution_m") != 30:
        raise ValueError("This SimFire LANDFIRE bridge currently expects a 30 m scenario grid.")
    top_left_latitude = grid.get("top_left_latitude")
    top_left_longitude = grid.get("top_left_longitude")
    if top_left_latitude is None or top_left_longitude is None:
        raise ValueError("Scenario manifest needs its fixed grid's top-left coordinates.")
    expected_top_left = simfire_operational_aoi(
        float(latitude), float(longitude), height_m, width_m
    )[-1]
    if (
        abs(expected_top_left[0] - float(top_left_latitude)) > 1e-9
        or abs(expected_top_left[1] - float(top_left_longitude)) > 1e-9
    ):
        raise ValueError("Scenario grid does not match the fixed-size event-location rule.")
    return (
        float(latitude),
        float(longitude),
        event_year,
        height_m,
        width_m,
        str(payload.get("scenario_id", "unspecified")),
        str(event.get("source_record_id", "unspecified")),
        str(point.get("role", "unknown")),
    )


def simfire_operational_aoi(
    latitude: float,
    longitude: float,
    height_m: int,
    width_m: int,
) -> tuple[float, float, float, float, tuple[float, float]]:
    """Return W,S,E,N bounds plus SimFire's operational top-left point.

    SimFire converts metres to degrees with a fixed 30 m angular increment and
    pads only the lower-right corner. Mirror that calculation exactly so the
    returned cache directory is the one its ``LandFireLatLongBox`` will read.
    """
    if height_m <= 0 or width_m <= 0 or height_m % 30 or width_m % 30:
        raise ValueError("Tile height and width must be positive multiples of 30 m")
    lat_span = (height_m / 30) * DEGREES_PER_30M
    lon_span = (width_m / 30) * DEGREES_PER_30M
    top_lat = latitude + lat_span / 2
    top_lon = longitude - lon_span / 2
    bottom_lat = top_lat - lat_span
    right_lon = top_lon + lon_span
    padding = SIMFIRE_LOWER_RIGHT_PADDING_DEGREES
    return (
        top_lon,
        bottom_lat - padding,
        right_lon + padding,
        top_lat,
        (top_lat, top_lon),
    )


def cache_directory(
    sf_home: Path,
    event_year: int,
    top_left: tuple[float, float],
    height_m: int,
    width_m: int,
) -> Path:
    latitude, longitude = top_left
    lat_span = (height_m / 30) * DEGREES_PER_30M
    lon_span = (width_m / 30) * DEGREES_PER_30M
    bottom_lat = latitude - lat_span
    right_lon = longitude + lon_span
    padding = SIMFIRE_LOWER_RIGHT_PADDING_DEGREES
    # Mirrors LandFireLatLongBox.product_layers_path in pinned SimFire 2.0.1.
    stem = (
        f"lf_{abs(longitude)}_{latitude}_"
        f"{abs(right_lon + padding)}_{bottom_lat - padding}"
    )
    return sf_home / "landfire" / str(event_year) / stem


def fetch_lfps(
    bounds: tuple[float, float, float, float],
    layers: list[str],
    email: str,
    output_zip: Path,
    poll_seconds: float,
    timeout_minutes: float,
) -> dict[str, object]:
    try:
        import requests
    except ImportError as exc:  # pragma: no cover - platform setup message
        raise RuntimeError("Install requests in the isolated SimFire environment.") from exc

    west, south, east, north = bounds
    params = {
        "Email": email,
        "Layer_List": ";".join(layers),
        "Area_of_Interest": f"{west:.12f} {south:.12f} {east:.12f} {north:.12f}",
        "Output_Projection": "4326",
        "Include_Layer_List_XML_File": "false",
    }
    response = requests.get(LFPS_SUBMIT, params=params, timeout=60)
    response.raise_for_status()
    submit = response.json()
    job_id = submit.get("jobId")
    if not job_id:
        raise RuntimeError(f"LANDFIRE accepted no job ID: {json.dumps(submit, sort_keys=True)}")

    deadline = time.monotonic() + timeout_minutes * 60
    last_status: dict[str, object] = submit
    output_url: str | None = None
    while time.monotonic() < deadline:
        status_response = requests.get(
            LFPS_STATUS, params={"JobId": job_id}, timeout=60
        )
        status_response.raise_for_status()
        last_status = status_response.json()
        status = str(last_status.get("status", "")).casefold()
        if status in {"succeeded", "success", "completed", "complete"}:
            output_url = last_status.get("outputFile")
            if not output_url:
                raise RuntimeError(
                    "LANDFIRE job succeeded but did not return outputFile: "
                    f"{json.dumps(last_status, sort_keys=True)}"
                )
            break
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise RuntimeError(
                f"LANDFIRE job ended as {status}: {json.dumps(last_status, sort_keys=True)}"
            )
        print(
            f"LANDFIRE job {job_id}: {last_status.get('status', 'unknown')} "
            f"(queue {last_status.get('queuePosition', 'unknown')})",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(poll_seconds)
    if output_url is None:
        raise TimeoutError(
            f"LANDFIRE job {job_id} did not finish within {timeout_minutes:g} minutes; "
            f"last status: {json.dumps(last_status, sort_keys=True)}"
        )

    download_url = urljoin(LFPS_BASE + "/", str(output_url))
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    partial = output_zip.with_suffix(output_zip.suffix + ".part")
    try:
        with requests.get(download_url, stream=True, timeout=300) as download:
            download.raise_for_status()
            with partial.open("wb") as stream:
                for chunk in download.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        stream.write(chunk)
        with ZipFile(partial) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise BadZipFile(f"Invalid member inside LANDFIRE zip: {bad_member}")
            tif_members = [
                info.filename
                for info in archive.infolist()
                if not info.is_dir() and PurePosixPath(info.filename).suffix.lower() in {".tif", ".tiff"}
            ]
            if len(tif_members) != 1:
                raise RuntimeError(
                    "Expected exactly one multi-band GeoTIFF in LANDFIRE response; "
                    f"found {tif_members}"
                )
        partial.replace(output_zip)
    except Exception:
        partial.unlink(missing_ok=True)
        raise

    return {
        "job_id": job_id,
        "status": str(last_status.get("status")),
        "output_url": download_url,
        "zip_bytes": output_zip.stat().st_size,
        "zip_sha256": sha256_file(output_zip),
        "tif_member": tif_members[0],
    }


def install_simfire_cache(output_zip: Path, cache_path: Path) -> list[str]:
    cache_path.mkdir(parents=True, exist_ok=True)
    with ZipFile(output_zip) as archive:
        extracted = []
        for info in archive.infolist():
            suffix = PurePosixPath(info.filename).suffix.lower()
            if info.is_dir() or suffix not in {".tif", ".tiff", ".tfw", ".xml"}:
                continue
            target = cache_path / PurePosixPath(info.filename).name
            with archive.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted.append(str(target))
    if not any(Path(path).suffix.lower() in {".tif", ".tiff"} for path in extracted):
        raise RuntimeError("No GeoTIFF was installed in the SimFire cache.")
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive", type=Path, default=ROOT / "data/raw/burnmd/BurnMD.zip"
    )
    parser.add_argument(
        "--sf-home", type=Path, default=ROOT / ".local/simfire-mineral-2020"
    )
    parser.add_argument(
        "--scenario-manifest",
        type=Path,
        help="use an event/grid from a scenario JSON instead of the default Mineral case",
    )
    parser.add_argument("--event-year", type=int, help="override cache year for the Mineral case only")
    parser.add_argument("--height-m", type=int, help="override tile height for the Mineral case only")
    parser.add_argument("--width-m", type=int, help="override tile width for the Mineral case only")
    parser.add_argument(
        "--layers",
        nargs=2,
        default=["LF2016_FBFM13", "LF2020_Elev"],
        metavar=("FUEL_LAYER", "ELEVATION_LAYER"),
        help="ordered bands: fuel first (SimFire expects band 1 fuel, band 2 elevation)",
    )
    parser.add_argument("--email", default=os.environ.get("LANDFIRE_EMAIL"))
    parser.add_argument("--poll-seconds", type=float, default=20)
    parser.add_argument("--timeout-minutes", type=float, default=45)
    parser.add_argument("--dry-run", action="store_true", help="print bounds and cache path; do not contact LANDFIRE")
    args = parser.parse_args()

    if args.poll_seconds < 5:
        parser.error("--poll-seconds must be at least 5 to avoid polling too frequently")
    if args.timeout_minutes <= 0:
        parser.error("--timeout-minutes must be positive")
    if not args.dry_run and not args.email:
        parser.error(
            "LANDFIRE requires the requester's email. Set LANDFIRE_EMAIL or pass --email; "
            "do not use a fabricated address. Use --dry-run to preview the AOI without contact."
        )

    if args.scenario_manifest:
        manifest_path = args.scenario_manifest.expanduser().resolve()
        try:
            (
                latitude,
                longitude,
                event_year,
                height_m,
                width_m,
                scenario_id,
                source_record_id,
                location_role,
            ) = scenario_location(manifest_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            parser.error(str(exc))
        if args.event_year is not None and args.event_year != event_year:
            parser.error("--event-year cannot override the year stored in --scenario-manifest.")
        if args.height_m is not None and args.height_m != height_m:
            parser.error("--height-m must match the grid stored in --scenario-manifest.")
        if args.width_m is not None and args.width_m != width_m:
            parser.error("--width-m must match the grid stored in --scenario-manifest.")
        source_sha256 = None
    else:
        latitude, longitude, source_sha256 = mineral_ignition(args.archive)
        event_year = args.event_year if args.event_year is not None else 2020
        height_m = args.height_m if args.height_m is not None else DEFAULT_TILE_HEIGHT_M
        width_m = args.width_m if args.width_m is not None else DEFAULT_TILE_WIDTH_M
        scenario_id = "mineral-2020"
        source_record_id = "BurnMD / Mineral_POLYGONS.shp / FireInitPo"
        location_role = "reported_ignition"

    west, south, east, north, top_left = simfire_operational_aoi(
        latitude, longitude, height_m, width_m
    )
    bounds = (west, south, east, north)
    sf_home = args.sf_home.expanduser().resolve()
    cache_path = cache_directory(
        sf_home, event_year, top_left, height_m, width_m
    )
    output_zip = cache_path / f"{cache_path.name}.zip"
    request_preview = {
        "service": LFPS_SUBMIT,
        "api_documentation": LFPS_API_DOCS,
        "scenario_id": scenario_id,
        "source_record_id": source_record_id,
        "source_archive_sha256": source_sha256,
        "scenario_manifest_path": str(manifest_path) if args.scenario_manifest else None,
        "scenario_basis": "fixed-size tile around the recorded event location; later perimeters and lines do not set the AOI",
        "event_location_role": location_role,
        "event_location_wgs84": {"latitude": latitude, "longitude": longitude},
        "tile_size_m": {"height": height_m, "width": width_m},
        "simfire_operational_top_left_lat_lon": list(top_left),
        "area_of_interest_order": "west south east north; WGS84/EPSG:4326",
        "area_of_interest": [round(value, 12) for value in bounds],
        "layers_in_output_band_order": args.layers,
        "output_projection": "EPSG:4326",
        "simfire_cache_directory": str(cache_path),
        "output_zip": str(output_zip),
        "fuel_vintage_note": (
            f"LF2016_FBFM13 is {event_year - 2016} years older than the event year {event_year}. "
            "It is a pre-event technical fallback, not a vetted fuel-vintage choice; verify "
            "its class mapping and suitability before scientific use."
        ),
        "simfire_padding_note": (
            "The pinned upstream code adds 100 arc-seconds (about 3.1 km north-south) "
            "to its lower-right cache/request bounds despite a source comment describing "
            "about 90 m. This adapter mirrors the code exactly."
        ),
    }
    if args.dry_run:
        request_preview["email_set"] = bool(args.email)
        print(json.dumps(request_preview, indent=2, sort_keys=True))
        return 0

    if output_zip.exists() or any(cache_path.glob("*.tif")):
        parser.error(
            f"SimFire cache already exists at {cache_path}; inspect it before replacing or re-requesting."
        )

    print("Submitting AOI to current public LANDFIRE service; email is not written to receipt.", file=sys.stderr)
    receipt = fetch_lfps(
        bounds=bounds,
        layers=list(args.layers),
        email=args.email,
        output_zip=output_zip,
        poll_seconds=args.poll_seconds,
        timeout_minutes=args.timeout_minutes,
    )
    extracted = install_simfire_cache(output_zip, cache_path)
    receipt.update(request_preview)
    receipt.update(
        {
            "kind": "landfire_aoi_download",
            "event_year": event_year,
            "email_included": True,
            "email_saved": False,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "extracted_simfire_cache_files": extracted,
        }
    )
    receipt_path = cache_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
