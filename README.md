---
type: Project Overview
title: Wildfire RL adaptation — MPVI
---
# Wildfire RL adaptation — MPVI

Istražujemo može li prilagodba unaprijed treniranog RL agenta **različitim budžetima
intervencija** smanjiti opožarenu površinu u odnosu na početni agent i heuristike,
uz posebno ispitivanje zaštite prioritetnih područja.

**Stanje (2026-11-19):** glavni pravac je SimFire + FPA-FOD/FEDS-CONUS: 98 TRAIN
požara 2018/19, 20 VALIDATION 2023; TEST 2024 zatvoren. Raniji ADR-022–028 rezultati
su poništeni zbog greške u vremenskim podacima. Na ispravljenim ulazima growth gate
prolazi prema slaboj elipsi, uz WAF 0.10 / ROS 1.0 (ADR-031); to nije fizička validacija.
Studija s 10 PPO seedova ne nalazi razliku prema jednostavnim pravilima ni mjerljivu
korist fine-tuninga budžetu (ADR-032; intervali su široki).

**Novi rad na grani `codex/simfire-policy-iterations`:** TASK-028–030 su završeni:
oba obračuna štete, 98×33 provjerena ishoda i osam TRAIN LOO metoda. Nijedna metoda
ne prelazi unaprijed zadani prag za nastavak. [Izvještaj](docs/research/SIMFIRE_B1_EXPLORATION.md)
objašnjava podatke, rezultate i granice; [NEXT_SESSION](docs/NEXT_SESSION.md) čuva
predloženi TASK-034. Rad je lokalni, bez novog PPO/CA, VALIDATION/TEST ili remote objave.
Cell2Fire/Firehose su odvojeni historijski pravci; simulatorski učinak nije dokaz
stvarnog učinka gašenja.

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
2. Pogledaj [istraživački protokol](docs/research/PROTOCOL.md),
   [provjeru simulatora](docs/research/SIMULATOR_AUDIT.md) i [odluke](docs/specs/DECISION_RECORDS.md).
3. Za aktivni pravac vidi [crosswalk](docs/research/FPA_FEDS_CROSSWALK.md),
   [growth gate ADR-031](reports/real-fire-data/feds-simfire-train-growth-gate-v1.json),
   [benchmark ADR-032](reports/real-fire-data/feds-simfire-budget-benchmark-adr030-v1.json)
   i [novi B=1 ciklus ADR-034](docs/research/SIMFIRE_B1_EXPLORATION.md).
   Stari TRAIN no-op screen nije važeći nalaz (ADR-029). CFSDS/Cell2Fire replayi su
   historija u [starom X/Y pipelineu](docs/research/REAL_CASE_PIPELINE.md).

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

[Legacy Firehose runtime nalaz](docs/research/FIREHOSE_VERIFICATION.md): 12 uspješnih kratkih
rollouta, ponovljiv seed, budžetski no-op i nepromijenjene težine. [Docker runbook](docker/firehose/README.md)
čuva build i inference komande. Nije bilo treniranja.

[Dataset data card](docs/research/DATASET.md): postojeća mapa 400 ćelija, terrain/fuel
inputi i 130 weather fajlova; zadani test koristi samo bazni Weather.csv. RL iskustvo
nastaje interakcijom. Taj legacy pilot nije aktivna zamrznuta FEDS kohorta opisana iznad.

## Šta se računa kao intervencija

Ovaj legacy/synthetic ugovor tretira jednu gorivu ili aktivno zapaljenu ćeliju: trajno je uklanja iz
širenja; cijena je jedna jedinica budžeta. Nema putovanja ekipa, trajanja gradnje,
probabilističkog neuspjeha ni realističnog utroška vode. No-op je besplatan i uvijek
dostupan. Nakon potrošnje budžeta simulacija nastavlja do gašenja ili horizonta.
Sva ikad zapaljena površina ostaje u šteti, čak i kada se kasnije ugasi.
Aktivni SimFire koristi odvojenu akciju linije uz front, u osam smjerova, sa istim
48h horizontom i nastavkom nakon trošenja budžeta. Implementacija i oba obračuna su u
[SimFire B=1 izvještaju](docs/research/SIMFIRE_B1_EXPLORATION.md); gate je ADR-031,
a opis u starom [FEDS crosswalk protokolu](docs/research/FPA_FEDS_CROSSWALK.md) je historijski.
Legacy detalji: [pravila](docs/specs/BUSINESS_RULES.md).

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
