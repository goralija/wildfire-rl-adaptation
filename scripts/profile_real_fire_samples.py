"""Rerun the bounded real-fire sample checks. Needs numpy and Pillow; no network.

Raw sample URLs/checksums: data/manifests/real-fire-candidates.json and
reports/real-fire-data/*download-manifest.json. Run from the repository root.
"""

import csv
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from PIL import Image


evidence = Path('reports/real-fire-data')
dogrib_manifest = json.loads((evidence / 'dogrib-download-manifest.json').read_text())
cfsds_manifest = json.loads((evidence / 'cfsds-sample-download-manifest.json').read_text())
for root, entries, key in (
    (Path('data/raw/dogrib-reference'), dogrib_manifest['files'], 'path'),
    (Path('data/raw/cfsds-sample-2020'), cfsds_manifest, 'name'),
):
    for entry in entries:
        content = (root / entry[key]).read_bytes()
        assert len(content) == entry['bytes']
        assert hashlib.sha256(content).hexdigest() == entry['sha256']
print('All 18 downloaded files match recorded sizes and SHA256 checksums.')

dogrib = Path('data/raw/dogrib-reference/dogrib')
forest = np.loadtxt(dogrib / 'Forest.asc', skiprows=6)
observed = np.loadtxt(dogrib / 'real_scar_dogrib.csv')  # whitespace, despite .csv
prometheus = np.loadtxt(dogrib / 'prometheus_dogrib.csv', delimiter=',')  # simulated
assert forest.shape == observed.shape == prometheus.shape == (223, 357)
assert set(np.unique(observed)) == {0, 1}
print('Dogrib observed-burn cells:', int(observed.sum()))
print('Observed-burn cells on fuel code101:', int(np.sum((observed == 1) & (forest == 101))))
for name in ('Forest.asc', 'elevation.asc', 'slope.asc', 'saz.asc'):
    large = np.loadtxt(dogrib / name, skiprows=6)
    small = np.loadtxt(Path('external/firehose/data/Sub20x20') / name, skiprows=6)
    print(name, 'Sub20 equals full-map array[0:20,20:40]:',
          bool(np.array_equal(large[:20, 20:40], small)))

sample = Path('data/raw/cfsds-sample-2020')
with zipfile.ZipFile(next(sample.glob('*groups*.zip'))) as archive:
    member = next(n for n in archive.namelist() if n.endswith('.csv'))
    rows = list(csv.DictReader(io.StringIO(archive.read(member).decode('utf-8-sig'))))
keys = Counter((row['ID'], row['DOB']) for row in rows)
ids = {row['ID'] for row in rows}
assert sum(v - 1 for v in keys.values()) == 0
print('CFSDS 2020 daily rows / fire IDs / columns:', len(rows), len(ids), len(rows[0]))
print('Missing BUI rows:', sum(r['bui'] in ('NA', '', 'NaN', 'nan') for r in rows))
print('Wind direction column:', any(c.lower() in ('wd', 'waz', 'wind_direction') for c in rows[0]))
with zipfile.ZipFile(next(sample.glob('*DOY*.zip'))) as archive:
    members = [n for n in archive.namelist() if n.endswith('.tif')]
    assert sum(i.file_size for i in archive.infolist()) < 30_000_000
    raster_ids = {n.replace('_krig.tif', '') for n in members}
    assert raster_ids == ids
    scales = set()
    for member in members:
        image = Image.open(io.BytesIO(archive.read(member)))
        scales.add(tuple(image.tag_v2[33550]))
    assert scales == {(90.0, 90.0, 0.0)}
print('CFSDS matched fire rasters:', len(members), 'at 90 m')
print('Sample checks passed; no simulator validation or policy training performed.')
