---
type: Environment Record
title: Environment bootstrap — 2026-10-30
sources:
  - resource: /docs/research/DATASET.md
  - resource: /docs/research/FIREHOSE_VERIFICATION.md
  - resource: /docs/specs/OPERATIONS.md
---
# Environment bootstrap — 2026-10-30

Ovo je lokalna provjera u korisnikovom checkoutu `feature/project-bootstrap`
(`/Users/belmindurmo/Desktop/mpvi/wildfire-rl-adaptation`), na bazi commita
`149989039e1d6809bbf18c637473ba4ce1839cbe`. Moderni Python venv je ovdje ponovo
napravljen iz pinovanog GIS+RL freezea. Legacy Firehose Docker je odvojen, kako se
stari checkpoint runtime ne bi miješao s novim Gym/SB3 bibliotekama.

## Prošlo

| Provjera | Rezultat |
| --- | --- |
| Moderni Python | Python 3.12.4, macOS 14.2 ARM64; `.venv` lokalno, nije dio Git-a |
| Moderni paketi | Project editable + `.[rl,geo]` + pinovani freeze; [`research-macos-arm64-py312.freeze.txt`](../../requirements/research-macos-arm64-py312.freeze.txt); RL-only freeze [`rl-macos-py312.freeze.txt`](../../requirements/rl-macos-py312.freeze.txt) |
| Aplikacijski testovi | 26/26 prolaze u `feature/project-bootstrap`, uključujući Gym/PPO save/load/short-learning provjere |
| Knowledge testovi | 15/15 prolaze; strict validator: 67 Markdown fajlova prolazi |
| Synthetic CLI smoke | Prošao; run `runs/dataset-refinement-smoke-20261030/`, config hash prefix `18e0d28b3c93`; ponovljen u `/private/tmp/wildfire-feature-branch-smoke-20261030/` |
| Optional modern PPO smoke | Ponovljen u ovom checkoutu: 1,024 CPU koraka; save/load i masked rollout prošli. Nije Firehose niti transfer-learning rezultat. Ignorisani izlaz `runs/dataset-refinement-feature-rl-smoke-20261030/synthetic-smoke.zip`, SHA256 `9d3dd23ffc3035abaaa71b33c4f0f36b95b86e6a813fad897c4dfd2175332ff7` |
| GIS i vizualizacija | `rasterio 1.4.4`, `geopandas 1.2.0`, `pyproj 3.8.0`, `xarray 2026.9.0`, `rioxarray 0.23.0`, `netCDF4 1.7.2`, `scipy 1.18.1`, `shapely 2.2.0`, `matplotlib 3.11.2`, `cdsapi 0.7.7`, `pyogrio 0.13.0`, `pandas 3.1.0` instalirani |
| GIS library smoke | svi moduli importuju; memory GeoTIFF reprojection `EPSG:4326→32611` nearest-neighbour prolazi; `Forest.asc` se čita 20×20, ali nema CRS metadata |
| FireSpread_MedEU spatial-screen input | javni v2 ZIP od 2,751,019 bajtova preuzet samo radi BiH spatial screening; SHA256 i 7 EFFIS candidates u [`medeu-spatial-screen.json`](../real-fire-data/medeu-spatial-screen.json); ostaje lokalno u Git-ignorisanom `data/raw/` |
| EFFIS fuel map | 18,226,545 bajtova preuzeto; EPSG:3035 NFFL/Anderson raster 250 m pregledan direktno iz ZIP-a bez izdvajanja 622 MB GeoTIFF-a; BiH overlay i SHA256 u istom spatial-screen izvještaju; lokalni fajl je Git-ignorisan |
| Firehose image | Linux ARM64 real-case build; tag `wildfire-firehose-probe:20261030-real-case`, ID `sha256:bf250dd34cebdff5f38e17056c73ef2f914055bdde29b0d6fea9afc16cbd10a3`; base image Python 3.8.20 digest je pinovan u Dockerfile |
| Legacy inference | 12/12 Sub20 slučajeva uspješno ponovljeno na novom imageu; runtime bez mreže/treninga, 2 CPU / 2 GiB; [receipt](../firehose-verification/real-case-image-regression.json) |
| CFSDS podaci i slučajevi | 46 godišnjih ZIP-ova/102,405,239 bajtova checksum-verifikovano; tri train slučaja pretvorena i C++ no-action replayana, jedan kandidat odbijen na fuel checku; [pregled slučajeva](../real-fire-data/README.md) |

## Šta ovaj setup dokazuje

Repo se može razvijati i pokretati u modernom Python venvu. Historijski Firehose
checkpointi se mogu učitati u zasebnom Python 3.8 kontejneru, a C++ simulator se može
izgraditi na ovom Linux ARM64 targetu. Pinovani upstream commitovi su Firehose
`e49a52a9a987a1585d25ddca2f711222ca500ffb` i contrib
`43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3`. Runtime image i `external/` klonovi ostaju
lokalni; kolega treba ponoviti build na svom Docker hostu prema
[`docker/firehose/README.md`](../../docker/firehose/README.md).

Ovo **ne** potvrđuje fizičku tačnost Firehosea, kvalitet politike, generalizaciju ili
RL prednost. Batch je ponovio poznati problem: fiksni PPO rollout ima 207 opaženih
zahvaćenih ćelija, ali upstream brojač 206; eksplicitni `sync-reset` dijagnostički
slučaj daje 207/207. Dakle okruženje je spremno za TASK-004c rad, ne za glavni rezultat.
Svi Firehose slučajevi su imali 58 odluka do weather horizonta; to nije dokaz da je
vatra ugašena. Tri no-action train replays daju 66/237/73 ha naspram 15.39/12.15/12.15
ha opaženih i dotiču rub 2×2 km domena; suppression status je nepoznat.

## Komande za ponavljanje

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[rl,geo]' -r requirements/research-macos-arm64-py312.freeze.txt -r requirements/knowledge.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s tests/knowledge -v
.venv/bin/python scripts/validate_knowledge.py --strict
PYTHONPATH=src .venv/bin/python -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW_ID
.venv/bin/python -m wildfire_rl.train --steps 1024 --out runs/NEW_ID
```

Legacy build/inference zahtijeva pinovane, ignorisane upstream cloneove prema
[`docker/firehose/README.md`](../../docker/firehose/README.md). Izgrađeni image koristi
Python 3.8/SB3 1.5/Gym 0.21/Torch 1.13.1. Kombinovani GIS+RL freeze je za Python
3.12/macOS ARM64 i nije Colab/Linux lock. Rasterio je ograničen na 1.4.x zbog kompatibilnog
macOS 14 ARM64 wheel-a; netCDF4 1.7.2 je dostupan wheel za ovaj host/Python.
C++ `apt-get update` zavisnosti još nisu zaključane na
Debian snapshot; za identičan trenutni runtime koristimo image digest iznad, a budući
čisti rebuild može rezolvirati novije Debian pakete.

`cdsapi` je instaliran, ali pilot weather je preuzet iz Open-Meteo Historical API-ja
(ERA5-Seamless) bez CDS konfiguracije. FireCase builder i multi-cell initial-front import
sada postoje i korišteni su za jedan CFSDS događaj. Početni 44-event crop screen i
splitovi su preliminarni; fuel/weather/suppression QC i 2019/2024 FBP vintage pripreme
ostaju. MedEU/EFFIS sloj je i dalje samo prostorno pregledan: NFFL/Anderson nije direktan
input Canadian FBP buildu, a MedEU licence/event IDs nisu potvrđeni za regionalni pilot.
