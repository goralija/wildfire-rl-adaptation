#!/usr/bin/env python3
"""Fetch or checksum-verify the small, pinned public Dogrib/Cell2Fire fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "reports/real-fire-data/dogrib-download-manifest.json"
DEFAULT_OUT = REPO / "data/raw/dogrib-reference"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--verify-only", action="store_true", help="check local files without using the network")
    parser.add_argument("--overwrite", action="store_true", help="replace a local file that does not match the pinned manifest")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    entries = manifest["files"]
    root = args.out_dir.resolve()
    results = []
    for entry in entries:
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe manifest path: {relative}")
        destination = (root / relative).resolve()
        if destination != root and root not in destination.parents:
            raise ValueError(f"Manifest path escapes output folder: {relative}")

        if destination.exists():
            matches = destination.stat().st_size == entry["bytes"] and sha256(destination) == entry["sha256"]
            if matches:
                results.append({"path": str(relative), "status": "verified-existing"})
                continue
            if args.verify_only:
                raise ValueError(f"Local file does not match pinned manifest: {relative}")
            if not args.overwrite:
                raise ValueError(f"File exists but differs; pass --overwrite to replace it: {relative}")

        if args.verify_only:
            raise FileNotFoundError(f"Local file is missing: {relative}")
        if not entry["url"].startswith("https://"):
            raise ValueError(f"Refusing non-HTTPS data URL: {entry['url']}")
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "wildfire-rl-adaptation-data-fetch/1.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read(entry["bytes"] + 1)
        if len(payload) != entry["bytes"]:
            raise ValueError(f"Byte count mismatch for {relative}: expected {entry['bytes']}, got {len(payload)}")
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"SHA-256 mismatch for {relative}; refusing to save it")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".download")
        try:
            temporary.write_bytes(payload)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        results.append({"path": str(relative), "status": "downloaded-and-verified"})

    print(json.dumps({"manifest_commit": manifest["repository_commit"],
                      "files": len(results), "total_bytes": manifest.get("total_bytes"),
                      "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
