---
type: Project Overview
title: Wildfire RL adaptation — MPVI
---
# Wildfire RL adaptation — MPVI

Istražujemo da li se RL agent može naučiti da bolje planira **vatrogasne linije** na
scenarijima izvedenim iz historijskih požara, uz isti ograničeni budžet za početnog agenta,
fine-tunirani agent i jednostavne kontrole.

**Trenutni dizajn:** konvertovati stvarne lokacije/datume požara u reproducibilne
SimFire scenarije sa odgovarajućim gorivom, terenom i vremenom; zatim uporediti osnovnog i
fine-tuniranog agenta unutar iste simulacije. Historijski završni obod ili akcije nisu
agentova nagrada. Tvrdnje su o simulatoru, ne o garantovanom smanjenju stvarnih hektara.
Praktični izvor prijavljenih lokacija požara je USFS FPA-FOD; prvi zapis (Dixie Fire 2021) već je pretvoren
u malu probnu scenario-karticu. Njegova tačka nije potvrđeno mjesto paljenja, a fuel, terrain
i historijsko vrijeme još nedostaju. SimFire 2.0.1 radi u izolovanom Python 3.9.25
okruženju, ali RL trening nije postavljen.
[Laički workflow](docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md),
[SimFire funkcionalni demo](reports/environment-setup/simfire-functional-demo/functional-fire.gif).

Sintetički pilot i raniji Firehose/Cell2Fire eksperimenti ostaju zapisani kao prethodna
tehnička osnova; oni nisu rezultati novog istraživačkog pitanja.

Tim: Amar Hodžić, Belmin Durmo, Harun Goralija. Predmet MPVI.

## Nastavak za pet minuta

Lokalni raspored je **glavni klon → `.worktrees/` → task checkout**, uz ignorisani
`.local/` za radne CSV-ove/grafove/backupe. [Workspace runbook](knowledge/workspace-layout.md)
opisuje rad i trenutni main/PR odnos.

Repo je samostalan **OKF 0.2 knowledge bundle**. [Glavni index.md](index.md) je ulaz
za ljude i agente; [kratki kontekst](knowledge/project-context.md) razlikuje dokaze,
prijedloge i otvorene odluke. [Pravila održavanja](knowledge/maintenance.md) i
[format/provjera](knowledge/okf-format.md) čuvaju isti kontekst kroz naredne sesije.

1. Za novi računar/kolegu počni od [HANDOFF](HANDOFF.md); zatim pročitaj
   [trenutno stanje](docs/STATUS.md) i [upute za narednu sesiju](docs/NEXT_SESSION.md).
2. Pogledaj [trenutni dizajn](docs/DESIGN.md), [scenario pipeline](docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md)
   i [ADR-040](docs/specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01).
3. Sljedeći cilj je dobiti provjeren fuel/terrain/weather za Dixie scenario, napraviti
   real-input kartu, pa onda veći reproducibilni USFS FPA-FOD uzorak i RL runtime.
   [STATUS](docs/STATUS.md) i
   [NEXT_SESSION](docs/NEXT_SESSION.md) imaju tačan redoslijed i lokalna ograničenja.

## Pokretanje bez dodatnih biblioteka

Python >=3.11. Najnoviji lokalni environment receipt koristi Python 3.12.4/macOS
ARM64; u repozitoriju postoji i raniji Python 3.13 snapshot.
Iz korijena repozitorija:

```sh
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m wildfire_rl.cli --config configs/smoke.json --out runs/smoke-001
PYTHONPATH=src .venv/bin/python -m wildfire_rl.cli --config configs/pilot.json --out runs/pilot-001
```

Svaki izlazni direktorij mora biti nov. RL testovi se preskaču bez optional extra.
Standardni pilot obuhvata 5 politika × 5 budžeta × 12 seedova = **300 epizoda**.
Izlazi: `episodes.csv`, `summary.csv`, `manifest.json`, `budget_damage.svg`.
Primjer provjerenog izlaza je u [reports/pilot](reports/pilot/README.md).

## Opcionalna moderna RL provjera

```sh
.venv/bin/python -m pip install -e '.[rl]'
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m wildfire_rl.train --steps 1024 --out runs/rl-smoke-001
```

Ovo trenira novi mali MaskablePPO u sintetičkom okruženju na CPU-u.
**Ne učitava Firehose težine, ne implementira glavno istraživanje i ne tvrdi poboljšanje.**
Za tačne verzije i platformu vidi kombinovani GIS+RL lock
`requirements/research-macos-arm64-py312.freeze.txt`, raniji RL-only lock
`requirements/rl-macos-py312.freeze.txt`, `requirements/rl-macos-py313.freeze.txt` i
[`environment setup receipt`](reports/environment-setup/README.md).

Za GIS raster/weather obradu instaliraj dodatni `geo` extra zajedno s RL-om:

```sh
.venv/bin/python -m pip install -e '.[rl,geo]' -r requirements/knowledge.txt
```

To daje `rasterio`, `geopandas`, `pyproj`, `xarray`, `rioxarray`, `netCDF4` i CDS API
klijent u istom modernom `.venv`; GIS paketi nisu potrebni legacy Firehose Dockeru.

## Postojeći model i dataset

[Firehose runtime nalaz](docs/research/FIREHOSE_VERIFICATION.md): 12 uspješnih kratkih
rollouta, ponovljiv seed, budžetski no-op i nepromijenjene težine. [Docker runbook](docker/firehose/README.md)
čuva build i inference komande. Nije bilo treniranja.

[Prethodna CFSDS/Firehose putanja](docs/STATUS_CFSDS_ARCHIVE.md) čuva dataset kartice,
inpute, hashove i tri no-action replaya. Trenutni izvor događaja je USFS FPA-FOD; prvi
probni zapis i scenario-kartica su u
[candidate manifestu](data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json).
BurnMD ostaje opcioni izvor ljudskih linija; njegova posebna data licenca je neriješena.

## Šta se računa kao intervencija u novom dizajnu

SimFire agent se kreće i postavlja liniju na mapu; RL budžet će ograničiti broj ili dužinu
linijskih poteza. Nećemo ih predstavljati kao stvarne crew-hours dok BurnMD ne potvrdi
vremena i resurse. Za prvi prototip fokusiramo se na fireline, najbližu vrstu akcije
historijskim linijskim podacima. Staro pravilo „jedna akcija izbriše jednu ćeliju“ pripada
Firehose/Cell2Fire tracku i novom simulatoru se ne pripisuje.

## Sadržaj repozitorija

| Putanja | Namjena |
| --- | --- |
| `src/wildfire_rl/` | sintetički engine, baseline politike, evaluacija, optional Gym/RL |
| `tests/` | budžet, šteta, statistika, reproducibilnost, Gym i kratko učenje |
| `configs/` | male JSON konfiguracije i predloženi splitovi |
| `data/manifests/` | porijeklo, verzije i hash vrijednosti; bez velikih podataka |
| `docs/specs/` | cilj, zahtjevi, arhitektura, pravila i odluke |
| `docs/research/` | literatura, protokol, simulator audit, rubrika |
| `reports/` | mali provjereni rezultati i plan postera |
| `requirements/` | tačne verzije provjerenog optional environmenta |
| `external/`, `runs/`, `artifacts/` | lokalni ignorisani kod trećih strana, izlazi i modeli |
| `private/` | ignorisani originalni mail i slika rubrike; ne objavljivati |

[Glavni indeks znanja](index.md) povezuje cijeli repo; [docs indeks](docs/index.md)
grupiše istraživanje/specifikacije. Agent ulazi su AGENTS.md, CLAUDE.md, GEMINI.md
i .github/copilot-instructions.md, s istim kanonskim pravilima u AGENTS.md.
Ne stavljati `.venv`, cijeli Firehose, težine, privatnu prepisku, velike rastere ili
neprovjerene rezultate u Git. Ne biramo licencu za tim bez njegove odluke;
Firehose/Cell2Fire imaju vlastite licence, vidi [provenance](data/README.md).

## Pošteno tumačenje

Pozitivan nalaz nije unaprijed obećan. Nulti i negativni rezultati su prihvatljivi uz
ispravan protokol. Prioritetna zaštita postoji već u Firehose radu: doprinos treba
vezati za prilagodbu budžetima i pažljivo mjerenje kompromisa, ne samo novu nagradu.
