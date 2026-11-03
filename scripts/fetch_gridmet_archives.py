#!/usr/bin/env python3
"""Fetch selected, public gridMET annual NetCDF inputs into ignored `.local/` cache."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen


ALLOWED_YEARS = (2018, 2019, 2023)
ALLOWED_VARIABLES = ("th", "vs", "fm100")
BASE_URL = "https://www.northwestknowledge.net/metdata/data/{variable}_{year}.nc"
DEFAULT_CACHE = Path(__file__).resolve().parents[1] / ".local/gridmet"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_gridmet_variable(dataset, abbreviation: str):
    """Return a native NetCDF variable whose published name is the gridMET abbreviation.

    The annual files use descriptive NetCDF variable names (for example
    ``wind_speed``), while the short gridMET abbreviation is retained in the
    variable's ``long_name``/``standard_name`` metadata.
    """
    matches = []
    for name, variable in dataset.variables.items():
        labels = {
            str(getattr(variable, attribute, "")).strip().lower()
            for attribute in ("long_name", "standard_name")
        }
        if abbreviation.lower() in labels and variable.ndim >= 3:
            matches.append((name, variable))
    if len(matches) != 1:
        raise ValueError(
            f"Expected one gridMET variable labeled {abbreviation!r}; found "
            f"{[name for name, _ in matches]}."
        )
    return matches[0]


def validate_gridmet_archive(path: Path, year: int, abbreviation: str) -> str:
    """Check the daily coordinate, source variable and a final data slab."""
    from netCDF4 import Dataset

    with Dataset(path) as dataset:
        native_name, gridmet_var = find_gridmet_variable(dataset, abbreviation)
        expected_days = 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365
        if gridmet_var.shape[0] != expected_days:
            raise ValueError(
                f"NetCDF archive {path.name} has {gridmet_var.shape[0]} daily slices; expected {expected_days}."
            )
        if "day" not in dataset.variables or dataset.variables["day"].shape[0] != expected_days:
            raise ValueError(f"NetCDF archive {path.name} lacks the expected daily coordinate.")
        # Touch a final-day slab so truncated HDF5 downloads cannot pass on header metadata alone.
        gridmet_var[-1, 0:1, 0:1]
    return native_name


def fetch_archive(year: int, variable: str, output_dir: Path) -> tuple[Path, str]:
    if year not in ALLOWED_YEARS:
        raise ValueError(f"Year {year} is outside the approved train/validation years {ALLOWED_YEARS}.")
    if variable not in ALLOWED_VARIABLES:
        raise ValueError(f"Unsupported gridMET variable {variable!r}; expected {ALLOWED_VARIABLES}.")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{variable}_{year}.nc"
    sidecar = destination.with_suffix(".nc.sha256")
    if destination.is_file() and sidecar.is_file():
        expected = sidecar.read_text(encoding="ascii").strip()
        actual = sha256_file(destination)
        if actual == expected:
            return destination, actual

    partial = destination.with_suffix(destination.suffix + ".partial")
    request = Request(
        BASE_URL.format(variable=variable, year=year),
        headers={"User-Agent": "wildfire-rl-adaptation-gridmet-fetch/1.0"},
    )
    if partial.is_file():
        try:
            head = urlopen(Request(request.full_url, method="HEAD", headers=dict(request.header_items())), timeout=60)
            with head:
                expected_size = head.headers.get("Content-Length")
            if expected_size and partial.stat().st_size == int(expected_size):
                validate_gridmet_archive(partial, year, variable)
                actual_hash = sha256_file(partial)
                os.replace(partial, destination)
                sidecar.write_text(actual_hash + "\n", encoding="ascii")
                return destination, actual_hash
        except Exception:
            # A stale or unverifiable partial is replaced by the checksum-recorded GET below.
            pass
    digest = hashlib.sha256()
    total = 0
    with urlopen(request, timeout=180) as response, partial.open("wb") as stream:
        expected_size = response.headers.get("Content-Length")
        expected_size = int(expected_size) if expected_size else None
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            stream.write(block)
            digest.update(block)
            total += len(block)
    if total < 1024 * 1024:
        raise ValueError(f"Unexpectedly small gridMET archive: {total} bytes for {variable}_{year}.")
    if expected_size is not None and total != expected_size:
        raise ValueError(f"Incomplete gridMET archive: {total} bytes; expected {expected_size}.")

    try:
        validate_gridmet_archive(partial, year, variable)
    except ImportError as exc:  # pragma: no cover - depends on the isolated GIS runtime
        raise RuntimeError("Install netCDF4 in the isolated SimFire environment before fetching gridMET.") from exc

    actual_hash = digest.hexdigest()
    os.replace(partial, destination)
    sidecar.write_text(actual_hash + "\n", encoding="ascii")
    return destination, actual_hash


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, choices=ALLOWED_YEARS, nargs="+", required=True)
    parser.add_argument("--variable", choices=ALLOWED_VARIABLES, nargs="+", default=ALLOWED_VARIABLES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_CACHE)
    args = parser.parse_args(argv)
    try:
        for year in args.year:
            for variable in args.variable:
                path, checksum = fetch_archive(year, variable, args.out_dir)
                print(f"verified {path.name}: {path.stat().st_size} bytes; sha256={checksum}")
    except Exception as exc:
        print(f"gridMET fetch failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
