---
type: Playbook
title: Handoff za nastavak projekta
---
# Handoff za nastavak projekta

Stanje 2026-10-31. Ovaj dokument je dovoljan ulaz bez prethodne chat historije.
Istraživačko pitanje: može li prilagodba postojećeg RL agenta različitim budžetima
intervencija poboljšati rezultate u odnosu na zamrznuti model i heuristike?

**Odabrana putanja: Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire.** Korisnik je rekao
da geografija nije ograničenje i da odaberemo najkompatibilnije. CFSDS daje mnogo
stvarnih kanadskih dnevnih požara; model goriva odgovara simulatoru koji već imamo.
Geometrijski screen izabrao je 44 kandidata (najviše pet po godini): 20 train, 9
validation, 15 test po godini događaja. To je preliminarni, neiscrpan spisak; nije
benchmark zamrznut za konačnu evaluaciju.

Tri train slučaja (`2018_747`, `2018_241`, `2018_1770`) već su prevedena u Firehose ulaze
i pokrenuta u stvarnom C++ simulatoru; multi-cell početno stanje radi. No-action
prognoze su 66/237/73 ha prema opaženih 15.39/12.15/12.15 ha, uz rubni kontakt; za
`2018_747` šest seedova dalo je istu završnu mapu. Geometrijski kandidat `2014_538` je
odbijen jer dio historijskih ćelija pada na water/nonfuel. Dakle pipeline se izvršava,
ali simulator još ne prolazi reality-check. Nema treniranja, fizičke validacije ni
dokaza da bi agent smanjio stvarnu štetu. Pročitaj [X/Y pipeline](docs/research/REAL_CASE_PIPELINE.md),
[dataset pregled](docs/research/REAL_FIRE_DATASETS.md) i
[cohort manifest](data/manifests/cfsds-v1_1-pilot-cohort.json).

Najnoviji korak je TASK-018 train-only dijagnostika no-action rasta. Sačuvani gridovi
analizirani su na fiksnim minutnim presjecima, ulazi/hashovi su upoređeni, a pogrešan
probe horizon metapodatak ispravljen. Požari rastu različitim brzinama, svi dodiruju rub
20×20 mreže, suppression nije poznat, a tačan uzrok nije izolovan. Svi izvještaji su u
[dijagnozi](docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md) i
[timeline receiptu](reports/real-fire-data/cfsds-no-action-timeline.json). Validation/test
ishodi nisu korišteni.

## Baza znanja u repozitoriju

Repo je jedan OKF 0.2 bundle. [Root index](index.md) vodi do
[sažetog konteksta](knowledge/project-context.md), [mape koda/zadataka](knowledge/code-map.md),
[kanonskih dokumenata](docs/index.md) i dokaza. [Održavanje](knowledge/maintenance.md)
opisuje gdje zabilježiti nalaze, odluke i otvorene teme; [OKF profil](knowledge/okf-format.md)
opisuje format/provjere. Za nastavak nisu potrebni chat ni vanjska baza znanja.

Agent ulazi AGENTS.md/CLAUDE.md/GEMINI.md/.github/copilot-instructions.md daju isti
redoslijed čitanja. Sadržaj se učitava progresivno; relevantni izvori ostaju dostupni
u repou. Lokalni veliki/raw artefakti i privatni originali imaju odvojenu granicu ispod.

## Preuzimanje i prvo pokretanje

Bootstrap je već spojen u `main`. Za trenutno objavljenu narednu task granu:

```sh
git clone --branch main https://github.com/goralija/wildfire-rl-adaptation.git mpvi
cd mpvi
mkdir -p .worktrees
git worktree add --track -b research/cfsds-train-qc .worktrees/cfsds-train-qc origin/research/cfsds-train-qc
cd .worktrees/cfsds-train-qc
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m wildfire_rl.cli --config configs/smoke.json --out runs/handoff-smoke
```

Komande za kreiranje worktreea iznad su za nov klon; u postojećem koristi
`git worktree list` i nastavi na odgovarajućoj putanji. [Workspace raspored](knowledge/workspace-layout.md)
opisuje glavni klon i lokalne ignorirane radne artefakte. `main` već sadrži bootstrap.

Treba Python >=3.11; osnovni paket nema dodatnih zavisnosti. Bez RL biblioteka
prolaze 22 testa, a 4 optional RL testa se preskaču. Smoke pravi CSV/JSON/SVG izlaze.
Izlazni direktorij mora biti nov pri ponavljanju. Nakon mergea isti sadržaj je na
`main`; za novi rad napravi zasebnu granu i worktree od najnovijeg `origin/main`.

Za moderni optional Gymnasium/SB3 i GIS converter environment, bez dugog treniranja:

```sh
.venv/bin/python -m pip install -e '.[rl,geo]' -r requirements/knowledge.txt
.venv/bin/python -m unittest discover -s tests -v
```

U najnovijem lokalnom modernom environmentu prolazi svih 26 testova. Environment receipt
bilježi Python 3.12.4/macOS ARM64 i kombinovani GIS+RL freeze u
`requirements/research-macos-arm64-py312.freeze.txt`; RL-only snapshots su u
`requirements/rl-macos-py312.freeze.txt` i `requirements/rl-macos-py313.freeze.txt`.
Nijedan nije univerzalan cross-platform lock.
Optional suite uključuje kratko učenje radi provjere save/load.

## Šta je već urađeno

| Dio | Dokaz i granica |
| --- | --- |
| Baza znanja | [Indeks](docs/index.md), zahtjevi/rubrika, protokol, specifikacije, odluke i backlog |
| Sintetički pilot | engine, pet baseline politika, budžet/no-op, kumulativna šteta, paired evaluacija; [300 baseline epizoda](reports/pilot/README.md) |
| Moderni RL smoke | novi mali PPO u sintetičkom engineu; [manifest](reports/rl-smoke/README.md), nije adaptacija Firehose modela |
| Firehose/Cell2Fire runtime | originalni C++ kompajliran na Linux ARM64; oba postojeća 20×20 checkpointa izvršena bez treniranja; [12 kratkih rollouta](docs/research/FIREHOSE_VERIFICATION.md) |
| Podaci | [Sub20 input inventar](docs/research/DATASET.md), [Dogrib/CFSDS/MedEU poređenje i mali uzorci](docs/research/REAL_FIRE_DATASETS.md), URL/verzije/hashovi |
| Provjere | [Nezavisni pregledi](docs/REVIEW.md), testovi i postojeći GitHub Actions core workflow za Python 3.11/3.13 |

**Nisu urađeni:** glavni fine-tuning, zamrznut istraživački test skup, dokaz prednosti
RL adaptacije, fizička validacija na historijskim požarima ili validacija za BiH.
Sintetički pilot i runtime provjera nisu glavni istraživački rezultati.

## Trenutni projektni zadatak: TASK-015 train-only input QC

TASK-004c episode adapter je završen lokalno. C++ terminal receipt i Python `FireEnv`
sada čuvaju kumulativno pogođene ID-jeve nakon tretiranja, odvojeni scar/aktivni front,
početni reset state i razlog završetka. Fixture + 12/12 inference slučajeva prolaze.
Checkpoint ugovor RGB 3×20×20 / `Discrete(400)`, legacy no-op `-1`, action head i reward
nisu mijenjani. Sažeti dokaz i eksplicitne granice su u
[adapter receiptu](reports/firehose-verification/task004c-adapter-smoke.json).

Train-only input QC sada mjeri 3/20 dostupnih FireCase paketa. Sve tri 20×20/100 m
terrain mape su poravnate; dnevni FWI se ponavlja kroz 24 sata; weather reanalysis tačke
su 2.4–5.2 km od summary centroida. 2014b nema pixel-level cutoff dokaz, 2019 CanFG je
razvojni/NBAC-zasnovan, izvorni DEM tile hash/date i potpuna weather field mapping nisu
sačuvani, a suppression je unknown za svih 20. Čitaj
[detaljni input QC](docs/research/CFSDS_TRAIN_INPUT_QC.md) i
[mašinski receipt](reports/real-fire-data/cfsds-train-input-qc.json).

Train-only pre-target mask proof za `2018_747` i C++ NF-scar characterization fixture su
završeni; pogledati mask receipt, importer receipt i ADR-020. To nije godišnja fuel mapa:
2014b nema potvrđen pixel cutoff, v20191114 succession tree nije transkribovan/validiran,
a C++ importer odbija `burnt` inicijalno stanje na NF ćeliji. Također, trenutni builder
bira n-1 active front prema targetu n, pa agent dobija buduću target geometriju. Prije
benchmarka definisati target-blind front, pribaviti vjerodostojna fuel pravila, odlučiti
importer/damage contract, pa tek onda napraviti godišnju kartu. Zatim popuniti train
terrain/weather provenance i suppression evidence prije preregistrovanog replay gatea.
Ne birati per-event trajanje iz targeta.
No-action gate nije prošao: ne koristiti heldout ishode za kalibraciju, ne pokretati
benchmark ili fine-tuning i ne tvrditi fizičku validaciju/agenta boljeg od baselinea.

TASK-014 Python 3.12.4/macOS ARM64, Linux ARM64 legacy Docker i geospatial ETL venv
navedeni su u [environment receiptu](reports/environment-setup/README.md). Venv,
`external/` i Docker image su ignorisani i lokalni.

## Ograničenja završene TASK-004c adapter faze

U 12-case batchu svaka epizoda završila je na `weather_horizon`; C++ grane
`front_extinguished`, `grid_exhausted` i `no_ignition` nisu direktno izvršene u toj matrici.
Adapter consistency nije fire-behavior validation. Stari CFSDS no-action replays i dalje
previše rastu/dotiču crop edge, uz unknown suppression i dnevni satelitski target.
Prije benchmarka i dalje trebaju TASK-015 input QC, train-only no-action replay gate i
event-level heldout freeze. [BACKLOG](docs/BACKLOG.md) čuva redoslijed TASK-005/006.
TASK-010 je poznata manja CLI greška za root JSON `null`, ne blokira validne runove.

## Legacy runtime na drugom računaru

Moderni `.venv` i legacy Firehose su odvojeni. Za postojeće checkpointove treba
Docker i javni pinovani upstream izvori; pratiti [Docker runbook](docker/firehose/README.md).
On sadrži clone/commit, build i kratke inference komande. Nemoj instalirati Gym 0.21
u moderni environment ili učitavati legacy pickle checkpoint na hostu.

Lokalni tag `wildfire-firehose-probe:20261028` nije objavljen u registryju niti dolazi
sa Git klonom. Image treba izgraditi; build koristi mrežu, inference je bez mreže.
Provjeren je Linux ARM64 CPU runtime (Python 3.8, SB3/contrib 1.5.0, Torch 1.13.1).
x86/GPU/Colab nisu zasebno potvrđeni. Ne objavljivati image/težine/raw podatke prije
provjere njihovih licenci. [Environment manifest](reports/firehose-verification/environment.json)
i package freeze čuvaju verzije ranijeg uspješnog izvršavanja.

## Šta Git klon ne sadrži i kako nastaviti s podacima

- `external/`: treći kod i checkpointovi; preuzimaju se po Docker runbooku i
  [upstream manifestu](data/manifests/upstream.json).
- `data/raw/`: 16 odabranih Dogrib fajlova i dva CFSDS ZIP-a, ukupno 3.68 MB.
  Svaki javni URL, ciljna relativna putanja, veličina i SHA256 su u
  [Dogrib manifestu](reports/real-fire-data/dogrib-download-manifest.json) i
  [CFSDS manifestu](reports/real-fire-data/cfsds-sample-download-manifest.json).
  Dogrib `path` dodaj na `data/raw/dogrib-reference/`, a CFSDS `name` na
  `data/raw/cfsds-sample-2020/`. Zatim, uz NumPy/Pillow i Firehose Sub20 inpute,
  pokreni `python3 scripts/profile_real_fire_samples.py`; skripta provjerava hashove
  i ponavlja zabilježene kontrole. Referentne verzije: Python 3.12.14,
  NumPy 2.3.5 i Pillow 12.3.0.
- FireSpread_MedEU v2 ZIP (2.75 MB), Natural Earth 1:110m country boundary i EFFIS
  European Fuel Map ZIP (18.2 MB) su dodatno skinuti u ignorisani `data/raw/` za prvi
  BiH screen. Nijedan nije u Git-u. Hashovi, 7 kandidat EFFIS ID-jeva, NFFL fuel overlay,
  kvaliteta, licence i scale ograničenja su u
  [medeu-spatial-screen.json](reports/real-fire-data/medeu-spatial-screen.json).
- `runs/`, `.venv/`, Docker image i veliki lokalni logovi: ponovo se generišu;
  mali provjereni rezultati i manifesti su u `reports/`.
- `private/`: originalna prepiska/slika rubrike ostaju privatni; javni sažetak
  zahtjeva je dovoljan za tehnički nastavak. Ne tražiti ih za setup/testove.

Dogrib služi početnom historijskom slučaju, ali dijeli fuel/elevation blok sa Sub20,
pa nije nezavisan test generalizacije. Njegov puni raster nije direktno kompatibilan
s 400-action politikom. CFSDS je najbliži postojećem Canadian FBP. FireSpread_MedEU
ima lokalne BiH kandidate, ali ne Canadian FBP goriva, a najbolji local case prelazi
postojeći 20×20 extent. Dnevni historijski front zahtijeva simulator state importer.
Ne preuzimati cijelu 48.4 GB WildfireSpreadTS arhivu.

## Spreman prompt za kolegu ili coding agenta

> Nastavi na research/cfsds-train-qc. Pročitaj STATUS, NEXT_SESSION, BACKLOG,
> ADR-019, CFSDS_TRAIN_INPUT_QC, CFSDS_TRAIN_QC i CFSDS_NO_ACTION_DIAGNOSIS. Napravi
> mali leak-safe train fuel-vintage proof of concept, prvo dodaj fixture za interakciju
> scar/nonfuel i importer, pa snimi per-case terrain/weather provenance i suppression
> evidence. Zatim preregistruj zajednički no-action replay gate. Ne otvaraj heldout
> ishode za tuning i ne treniraj dok gate ne prođe.
