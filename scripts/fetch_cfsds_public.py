#!/usr/bin/env python3
"""Catalog and download the public CFSDS annual fire rasters and day summaries.

This intentionally excludes the much larger pixel-level feature tables. Source
metadata and checksums come from the public OSF API; downloaded files are verified
before they are moved into the ignored raw-data directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


OSF_NODE = "f48ry"
OSF_API = f"https://api.osf.io/v2/nodes/{OSF_NODE}/files/osfstorage/"
FOLDERS = {
    "arrival_rasters": "Fire growth rasters",
    "daily_summaries": "Fire growth daily summaries",
}
DEFAULT_YEARS = list(range(2002, 2025))


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "wildfire-rl-adaptation/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def list_all(url: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    while url:
        page = fetch_json(url)
        items.extend(page.get("data", []))
        url = page.get("links", {}).get("next") or ""
    return items


def catalog(years: set[int]) -> list[dict[str, Any]]:
    root = list_all(OSF_API)
    folders: dict[str, dict[str, Any]] = {}
    for item in root:
        name = item.get("attributes", {}).get("name")
        for kind, folder_name in FOLDERS.items():
            if name == folder_name:
                folders[kind] = item
    if set(folders) != set(FOLDERS):
        missing = sorted(set(FOLDERS) - set(folders))
        raise RuntimeError(f"OSF folder(s) missing: {', '.join(missing)}")

    entries = []
    for kind, folder in folders.items():
        href = folder["relationships"]["files"]["links"]["related"]["href"]
        for item in list_all(href + "?page%5Bsize%5D=100"):
            attr = item.get("attributes", {})
            name = attr.get("name", "")
            match = re.search(r"(20\d{2})", name)
            if not match or int(match.group(1)) not in years or not name.endswith(".zip"):
                continue
            hashes = attr.get("extra", {}).get("hashes", {})
            download = item.get("links", {}).get("download")
            if not attr.get("size") or not hashes.get("sha256") or not download:
                raise RuntimeError(f"Incomplete OSF metadata for {name}")
            entries.append({
                "kind": kind,
                "name": name,
                "year": int(match.group(1)),
                "osf_file_id": item["id"],
                "url": download,
                "bytes": attr["size"],
                "md5": hashes.get("md5"),
                "sha256": hashes["sha256"],
                "date_modified": attr.get("date_modified"),
            })
    entries.sort(key=lambda item: (item["year"], item["kind"]))
    expected = {(year, kind) for year in years for kind in FOLDERS}
    found = {(item["year"], item["kind"]) for item in entries}
    missing = sorted(expected - found)
    if missing:
        missing_text = ", ".join(f"{year}/{kind}" for year, kind in missing)
        raise RuntimeError(f"Annual CFSDS file(s) missing from OSF: {missing_text}")
    return entries


def download_and_verify(entry: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    dest = raw_dir / str(entry["year"]) / entry["name"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        if dest.stat().st_size == entry["bytes"] and digest == entry["sha256"]:
            return {"path": str(dest), "status": "already_verified"}

    temp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(entry["url"], headers={"User-Agent": "wildfire-rl-adaptation/0.1"})
    digest = hashlib.sha256()
    md5 = hashlib.md5()
    size = 0
    try:
        with urllib.request.urlopen(request, timeout=180) as response, temp.open("wb") as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
                digest.update(chunk)
                md5.update(chunk)
                size += len(chunk)
        if size != entry["bytes"]:
            raise RuntimeError(f"{entry['name']}: size {size} != expected {entry['bytes']}")
        if digest.hexdigest() != entry["sha256"]:
            raise RuntimeError(f"{entry['name']}: SHA256 mismatch")
        if entry.get("md5") and md5.hexdigest() != entry["md5"]:
            raise RuntimeError(f"{entry['name']}: MD5 mismatch")
        temp.replace(dest)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    return {"path": str(dest), "status": "downloaded_and_verified"}


def parse_years(values: list[str] | None) -> set[int]:
    if not values:
        return set(DEFAULT_YEARS)
    years: set[int] = set()
    for value in values:
        if "-" in value:
            start_text, end_text = value.split("-", 1)
            start, end = int(start_text), int(end_text)
            if end < start:
                raise ValueError(f"Invalid year range: {value}")
            years.update(range(start, end + 1))
        else:
            years.add(int(value))
    if min(years) < 2002 or max(years) > 2024:
        raise ValueError("CFSDS v1.1 annual files span 2002 through 2024")
    return years


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", nargs="+", help="Years or inclusive ranges; default: 2002-2024")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/cfsds-v1_1"))
    parser.add_argument("--manifest", type=Path, default=Path("reports/real-fire-data/cfsds-download-manifest.json"))
    parser.add_argument("--catalog-only", action="store_true", help="Write OSF metadata without downloading files")
    args = parser.parse_args()
    try:
        years = parse_years(args.years)
        entries = catalog(years)
        manifest: dict[str, Any] = {
            "dataset": "Canadian Fire Spread Dataset (CFSDS)",
            "release": "v1.1",
            "osf_project": "https://osf.io/f48ry/",
            "osf_node_id": OSF_NODE,
            "catalogued_on": date.today().isoformat(),
            "years": sorted(years),
            "included_products": list(FOLDERS),
            "excluded_products": ["Fire growth points (large pixel-level tables)"],
            "entries": entries,
        }
        if not args.catalog_only:
            total = sum(item["bytes"] for item in entries)
            print(f"Downloading {len(entries)} archives ({total:,} bytes) for {len(years)} years", flush=True)
            for index, entry in enumerate(entries, start=1):
                result = download_and_verify(entry, args.raw_dir)
                entry.update(result)
                print(f"[{index}/{len(entries)}] {entry['year']} {entry['kind']}: {result['status']}", flush=True)
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(f"Manifest: {args.manifest}")
        print(f"Verified archive count: {sum('path' in item for item in entries)}")
        return 0
    except (OSError, urllib.error.URLError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        print(f"CFSDS retrieval failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
