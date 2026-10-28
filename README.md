# Wildfire RL adaptation — MPVI

Istražujemo može li prilagodba unaprijed treniranog RL agenta **različitim budžetima
intervencija** smanjiti opožarenu površinu u odnosu na početni agent i heuristike,
uz posebno ispitivanje zaštite prioritetnih područja.

**Stanje:** istraživačka osnova i sintetički pilot; Cell2Fire je kompajliran, a oba
postojeća 20×20 Firehose modela izvršena su u izolovanom legacy kontejneru.
Fine-tuning i glavna evaluacija još nisu izvedeni.
Pilot ne predviđa stvarne požare i nije dokaz uspješnosti RL pristupa.

Tim: Amar Hodžić, Belmin Durmo, Harun Goralija. Predmet MPVI.

## Nastavak za pet minuta

1. Za novi računar/kolegu počni od [HANDOFF](HANDOFF.md); zatim pročitaj
   [trenutno stanje](docs/STATUS.md) i [upute za narednu sesiju](docs/NEXT_SESSION.md).
2. Pogledaj [istraživački protokol](docs/research/PROTOCOL.md),
   [provjeru simulatora](docs/research/SIMULATOR_AUDIT.md) i [odluke](docs/specs/DECISION_RECORDS.md).
3. Pokreni testove i pilot ispod. Glavni sljedeći korak je **TASK-012: dataset refinement**
   — uloga, izbor i obim podataka još nisu usaglašeni. TASK-004c je naredni poznati
   tehnički posao nakon tog razjašnjenja.

## Pokretanje bez dodatnih biblioteka

Python >=3.11. Referentni lokalni interpreter je Python 3.13.
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
Za zabilježene tačne verzije vidi `requirements/rl-macos-py313.freeze.txt`.

## Postojeći model i dataset

[Firehose runtime nalaz](docs/research/FIREHOSE_VERIFICATION.md): 12 uspješnih kratkih
rollouta, ponovljiv seed, budžetski no-op i nepromijenjene težine. [Docker runbook](docker/firehose/README.md)
čuva build i inference komande. Nije bilo treniranja.

[Dataset data card](docs/research/DATASET.md): postojeća mapa 400 ćelija, terrain/fuel
inputi i 130 weather fajlova; zadani test koristi samo bazni Weather.csv. RL iskustvo
nastaje interakcijom, a train/validation/test scenariji tek trebaju biti zamrznuti.

## Šta se računa kao intervencija

Jedna akcija tretira jednu gorivu ili aktivno zapaljenu ćeliju: trajno je uklanja iz
širenja; cijena je jedna jedinica budžeta. Nema putovanja ekipa, trajanja gradnje,
probabilističkog neuspjeha ni realističnog utroška vode. No-op je besplatan i uvijek
dostupan. Nakon potrošnje budžeta simulacija nastavlja do gašenja ili horizonta.
Sva ikad zapaljena površina ostaje u šteti, čak i kada se kasnije ugasi.
Detalji i razlike u odnosu na Firehose: [pravila](docs/specs/BUSINESS_RULES.md).

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

[Indeks znanja](docs/INDEX.md) povezuje sve dokumente.
Ne stavljati `.venv`, cijeli Firehose, težine, privatnu prepisku, velike rastere ili
neprovjerene rezultate u Git. Ne biramo licencu za tim bez njegove odluke;
Firehose/Cell2Fire imaju vlastite licence, vidi [provenance](data/README.md).

## Pošteno tumačenje

Pozitivan nalaz nije unaprijed obećan. Nulti i negativni rezultati su prihvatljivi uz
ispravan protokol. Prioritetna zaštita postoji već u Firehose radu: doprinos treba
vezati za prilagodbu budžetima i pažljivo mjerenje kompromisa, ne samo novu nagradu.
