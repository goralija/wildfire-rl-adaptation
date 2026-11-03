#!/usr/bin/env python3
"""Fetch checksum-pinned FEDS-CONUS layers for the train/validation years only."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from urllib.request import Request, urlopen

try:  # Import works both as ``python scripts/fetch_feds_archive.py`` and in tests.
    from scripts.audit_feds_fpa_fle_crosswalk import FEDS_FILE_MD5, FEDS_FILE_URL, _md5_file
except ModuleNotFoundError:
    from audit_feds_fpa_fle_crosswalk import FEDS_FILE_MD5, FEDS_FILE_URL, _md5_file


ALLOWED_YEARS = tuple(sorted(set().union(*(checksums for checksums in FEDS_FILE_MD5.values()))))
DEFAULT_CACHE = Path(__file__).resolve().parents[1] / ".local/feds-conus"


def fetch_archive(year: int, layer: str, output_dir: Path) -> Path:
    """Download one allowed archive and atomically install it after MD5 verification."""
    if layer not in FEDS_FILE_MD5:
        raise ValueError(f"Unsupported FEDS layer: {layer}")
    expected_md5 = FEDS_FILE_MD5[layer].get(year)
    if expected_md5 is None:
        raise ValueError(
            f"Year {year} is not in the approved train/validation archive set "
            f"({', '.join(map(str, ALLOWED_YEARS))}); test-year data are not fetched."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"feds_{year}_lf_{layer}.fgb"
    destination = output_dir / filename
    if destination.is_file() and _md5_file(destination) == expected_md5:
        print(f"verified cache exists: {destination}")
        return destination

    partial = destination.with_suffix(destination.suffix + ".partial")
    url = FEDS_FILE_URL.format(year=year, layer=layer)
    request = Request(url, headers={"User-Agent": "wildfire-rl-adaptation-feds-fetch/1.0"})
    digest_size = 0
    with urlopen(request, timeout=180) as response, partial.open("wb") as stream:
        content_length = response.headers.get("Content-Length")
        expected_size = int(content_length) if content_length else None
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            stream.write(block)
            digest_size += len(block)

    actual_md5 = _md5_file(partial)
    if expected_size is not None and digest_size != expected_size:
        raise ValueError(
            f"Incomplete download for {filename}: {digest_size} bytes, "
            f"expected {expected_size}. Partial file retained at {partial}."
        )
    if actual_md5 != expected_md5:
        raise ValueError(
            f"Checksum mismatch for {filename}: {actual_md5} != {expected_md5}. "
            f"Partial file retained at {partial}."
        )

    os.replace(partial, destination)
    print(f"fetched {filename}: {digest_size} bytes; md5={actual_md5}")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, choices=ALLOWED_YEARS, nargs="+", required=True)
    parser.add_argument("--layer", choices=tuple(FEDS_FILE_MD5), default="perimeter")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_CACHE)
    args = parser.parse_args(argv)
    try:
        for year in args.year:
            fetch_archive(year, args.layer, args.out_dir)
    except Exception as exc:
        print(f"FEDS fetch failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
