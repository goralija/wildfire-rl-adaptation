#!/usr/bin/env python3
"""Inventory the official BurnMD ZIP without extracting the full dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


EXPECTED_SHA256 = "4eefcbfdabce4966d68e0009e8a4b88dd34294a2cb5dee6aea84dd017eb334c7"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(path: Path) -> dict[str, object]:
    path = path.resolve()
    digest = sha256_file(path)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"BurnMD archive SHA-256 mismatch: {digest}")

    with ZipFile(path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        names = [entry.filename for entry in entries]
        source_entries = [
            entry
            for entry in entries
            if not entry.filename.startswith("__MACOSX/")
            and not PurePosixPath(entry.filename).name == ".DS_Store"
        ]
        suffix_counts = Counter(
            PurePosixPath(entry.filename).suffix.lower() or "<none>"
            for entry in source_entries
        )
        state_counts: Counter[str] = Counter()
        year_counts: Counter[str] = Counter()
        events: set[tuple[str, str, str]] = set()
        shapefiles: list[str] = []
        license_names: list[str] = []
        for entry in source_entries:
            parts = PurePosixPath(entry.filename).parts
            if len(parts) >= 2 and parts[0] == "BurnMD":
                state_counts[parts[1]] += 1
                if len(parts) >= 3 and parts[2].isdigit():
                    year_counts[parts[2]] += 1
                if len(parts) >= 5 and parts[3] == "fires":
                    events.add((parts[1], parts[2], parts[4]))
            if entry.filename.lower().endswith(".shp"):
                shapefiles.append(entry.filename)
            if any(
                marker in PurePosixPath(entry.filename).name.lower()
                for marker in ("license", "licence", "notice", "readme", "citation")
            ):
                license_names.append(entry.filename)

        mineral_prefix = "BurnMD/California/2020/fires/Mineral/"
        mineral_files = [
            {"path": entry.filename, "bytes": entry.file_size}
            for entry in source_entries
            if entry.filename.startswith(mineral_prefix)
        ]
        return {
            "record_type": "burnmd_archive_inventory",
            "inventory_scope": "ZIP directory and file names; no full extraction",
            "archive_name": path.name,
            "archive_bytes": path.stat().st_size,
            "sha256": digest,
            "expected_lfs_sha256": EXPECTED_SHA256,
            "sha256_matches_lfs_pointer": True,
            "archive_file_entries_including_macos_sidecars": len(entries),
            "archive_uncompressed_bytes_including_macos_sidecars": sum(
                entry.file_size for entry in entries
            ),
            "source_file_entries_excluding_macos_sidecars_and_ds_store": len(
                source_entries
            ),
            "source_uncompressed_bytes": sum(
                entry.file_size for entry in source_entries
            ),
            "source_file_extensions": dict(sorted(suffix_counts.items())),
            "state_directory_file_counts": dict(sorted(state_counts.items())),
            "year_directory_file_counts": dict(sorted(year_counts.items())),
            "event_directory_count": len(events),
            "shapefile_count": len(shapefiles),
            "archive_member_names_matching_license_notice_readme_citation": license_names,
            "mineral_fire_member_files": mineral_files,
            "first_30_burnmd_members": [
                name for name in names if name.startswith("BurnMD/")
            ][:30],
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="local BurnMD ZIP")
    parser.add_argument("--out", type=Path, help="optional JSON receipt path")
    args = parser.parse_args()
    result = inventory(args.archive)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
