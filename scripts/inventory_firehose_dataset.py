"""Inspectable, stdlib-only source inventory for the Firehose dataset data card."""

import argparse
import collections
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output already exists')
    root = args.root
    files = sorted(p for p in root.rglob('*') if p.is_file())
    rasters = {}
    for path in sorted(root.glob('*.asc')):
        lines = path.read_text().splitlines()
        header = {line.split()[0].lower(): float(line.split()[1]) for line in lines[:6]}
        grid = [[float(v) for v in line.split()] for line in lines[6:] if line.strip()]
        rasters[path.name] = dict(header=header, row_count=len(grid),
                                 widths=sorted(set(map(len, grid))),
                                 shape_matches_header=(len(grid) == header['nrows'] and
                                                       all(len(r) == header['ncols'] for r in grid)))
        if path.name == 'Forest.asc':
            rasters[path.name]['value_counts'] = dict(collections.Counter(v for row in grid for v in row))
    weather = []
    for path in sorted(root.glob('Weathers/*.csv')) + [root / 'Weather.csv']:
        with path.open() as file:
            rows = list(csv.DictReader(file))
        weather.append(dict(file=str(path.relative_to(root)), rows=len(rows),
                            columns=list(rows[0]) if rows else [],
                            sha256=sha256(path.read_bytes()).hexdigest(),
                            invalid_ws_rh_rows=sum(float(r['WS']) < 0 or
                                                  not 0 <= float(r['RH']) <= 100 for r in rows)))
    with (root / 'Data.csv').open() as file:
        raw = list(csv.reader(file))
    with (root / 'Data.csv').open() as file:
        rows = list(csv.DictReader(file))
    missing = {col: sum(row[col] is None or row[col].strip() == '' for row in rows) for col in raw[0]}
    with (root / 'fbp_lookup_table.csv').open() as file:
        lookup = list(csv.DictReader(file, skipinitialspace=True))
    known = {r['grid_value'].strip() for r in lookup}
    observed = {str(int(float(k))) for k in rasters['Forest.asc']['value_counts']}
    try:
        commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                         text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = None
    report = dict(dataset='Firehose Sub20x20', source_commit=commit,
                  files=len(files), bytes=sum(p.stat().st_size for p in files), rasters=rasters,
                  rasters_aligned=len({json.dumps(v['header'], sort_keys=True) for v in rasters.values()}) == 1,
                  missing_fuel_lookup_codes=sorted(observed - known),
                  weather_files=len(weather),
                  weather_row_counts=dict(collections.Counter(r['rows'] for r in weather)),
                  weather_unique_content_hashes=len({r['sha256'] for r in weather}),
                  data_csv_rows=len(rows), data_csv_column_count=len(raw[0]),
                  data_csv_row_widths=dict(collections.Counter(map(len, raw[1:]))),
                  data_csv_missing_by_column=missing, reward_mask_present=(root / 'Reward.asc').exists(),
                  weather=weather, file_manifest=[dict(path=str(p.relative_to(root)),
                  bytes=p.stat().st_size, sha256=sha256(p.read_bytes()).hexdigest()) for p in files])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print('Wrote dataset inventory:', args.out)


if __name__ == '__main__':
    main()
