---
type: Playbook
title: Handoff za nastavak projekta
---
# Handoff za nastavak projekta

Stanje 2026-10-28. Ovaj dokument je dovoljan ulaz bez prethodne chat historije.
Istraživačko pitanje: može li prilagodba postojećeg RL agenta različitim budžetima
intervencija poboljšati rezultate u odnosu na zamrznuti model i heuristike?

**Aktuelni fokus: TASK-012 — dataset refinement.** Izvori i mali uzorci su pregledani;
uloga stvarnih podataka, konačni izbor i obim evaluacije još nisu usaglašeni.
Dogrib/CFSDS su kandidati i prijedlog, ne zamrznut istraživački dataset.

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

Dok PR nije spojen, preuzmi implementacijsku granu:

```sh
git clone --branch main https://github.com/goralija/wildfire-rl-adaptation.git mpvi
cd mpvi
printf '\n/.worktrees/\n/.local/\n' >> .git/info/exclude
mkdir -p .worktrees
git worktree add --track -b feature/project-bootstrap .worktrees/project-bootstrap origin/feature/project-bootstrap
cd .worktrees/project-bootstrap
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m wildfire_rl.cli --config configs/smoke.json --out runs/handoff-smoke
```

Komande za kreiranje worktreea iznad su za nov klon; u postojećem koristi
`git worktree list` i nastavi na već registrovanoj putanji. [Workspace raspored](knowledge/workspace-layout.md)
opisuje glavni klon, prazan main dok PR čeka merge i `.local/` za radne artefakte.

Treba Python >=3.11; osnovni paket nema dodatnih zavisnosti. Bez RL biblioteka
prolaze 22 testa, a 4 optional RL testa se preskaču. Smoke pravi CSV/JSON/SVG izlaze.
Izlazni direktorij mora biti nov pri ponavljanju. Nakon mergea isti sadržaj je na
`main`; prije nastavka svog zadatka napravi vlastitu granu/worktree od PR grane ili maina.

Za moderni optional Gymnasium/SB3 environment, bez dugog treniranja:

```sh
.venv/bin/python -m pip install -e '.[rl]'
.venv/bin/python -m unittest discover -s tests -v
```

Na postojećem lokalnom modernom environmentu prolazi svih 26 testova. Tačne
zabilježene verzije su u `requirements/rl-macos-py313.freeze.txt`; to nije univerzalan
cross-platform lock. Optional suite uključuje kratko učenje radi provjere save/load.

## Šta je već urađeno

| Dio | Dokaz i granica |
| --- | --- |
| Baza znanja | [Indeks](docs/index.md), zahtjevi/rubrika, protokol, specifikacije, odluke i backlog |
| Sintetički pilot | engine, pet baseline politika, budžet/no-op, kumulativna šteta, paired evaluacija; [300 baseline epizoda](reports/pilot/README.md) |
| Moderni RL smoke | novi mali PPO u sintetičkom engineu; [manifest](reports/rl-smoke/README.md), nije adaptacija Firehose modela |
| Firehose/Cell2Fire runtime | originalni C++ kompajliran na Linux ARM64; oba postojeća 20×20 checkpointa izvršena bez treniranja; [12 kratkih rollouta](docs/research/FIREHOSE_VERIFICATION.md) |
| Podaci | [Sub20 input inventar](docs/research/DATASET.md), [Dogrib/CFSDS preporuka i mali uzorci](docs/research/REAL_FIRE_DATASETS.md), URL/verzije/hashovi |
| Provjere | [Nezavisni pregledi](docs/REVIEW.md), testovi i postojeći GitHub Actions core workflow za Python 3.11/3.13 |

**Nisu urađeni:** glavni fine-tuning, zamrznut istraživački test skup, dokaz prednosti
RL adaptacije, fizička validacija na historijskim požarima ili validacija za BiH.
Sintetički pilot i runtime provjera nisu glavni istraživački rezultati.

## Prvi zadatak: TASK-012 — dataset refinement

Počni od [trenutnog stanja podataka i otvorenih odluka](docs/research/REAL_FIRE_DATASETS.md).
Dosad imamo inventar Firehose simulator inputa, male Dogrib/CFSDS uzorke i provjere
njihove strukture. To još ne definiše glavni eksperimentalni skup.

Refinement treba dati kratak prijedlog koji razdvaja potvrđeno od otvorenog:

1. Uloga svakog sloja: ulazi/scenariji simulatora, iskustvo za RL i historijske
   reference. Odrediti koje tvrdnje želimo podržati stvarnim podacima.
2. Kandidati i obim: Dogrib, mali CFSDS podskup ili drugi opravdan izvor; konkretni
   događaji/mape, potrebni inputi, licence i realan trošak pripreme.
3. Veza s modelom: domen, rezolucija, vremenski korak i šta stvarno može koristiti
   postojeća 20×20/400-action politika. Puna historijska mapa nije automatski RL scenarij.
4. Evaluacija: jedinica scenarija, razdvajanje kalibracije/train/validation/test,
   metrike i granice generalizacije. Označiti šta nedostaje za izabrani pristup.

Prihvat: dokumentovan prijedlog obima i jasne otvorene odluke za usaglašavanje.
Status izbora ostaje provisional dok dogovor nije zabilježen. Preuzeti uzorak i
uspješan parser nisu potvrda da je dataset spreman. Tehnički plan prilagoditi tom obimu.

## Tehnički nastavak nakon refinementa: TASK-004c

Prvo pročitaj [STATUS](docs/STATUS.md), [runtime nalaze](docs/research/FIREHOSE_VERIFICATION.md),
[protokol](docs/research/PROTOCOL.md) i [odluke](docs/specs/DECISION_RECORDS.md).
Ne treba ponovo istraživati da li checkpointovi uopšte rade — to je već ostvareno.
Treba formalni adapter i C++ export koji ispravljaju potvrđene probleme:

1. Upstream reset vraća prazno početno opažanje iako warmup ima 7 pogođenih ćelija.
   Dijagnostički `--sync-reset` učitava stvarno stanje; još nije konačan adapter.
2. Kumulativna šteta može izostaviti početnu ćeliju: provjeren primjer 206 naspram
   207 iz historije rastera. Tretman prethodno zapaljene ćelije ne smije izbrisati štetu.
3. C++ grid kod 1 spaja aktivno i ranije gorjelo. Potreban je eksplicitan active/burnt
   export za mjerenje fronte i smisleno tumačenje heuristika.
4. `done` ne razlikuje containment od isteka weather horizonta. Dodati reason i
   odvojiti termination/truncation, uključujući timeout i cleanup subprocessa.

Sačuvati **RGB 3×20×20 i Discrete(400)** checkpoint kontrakt. Legacy no-op je `-1`,
prisiljen poslije B intervencija; nije naučena 401. akcija. Istu semantiku dati svim
politikama. Prihvat: regresijski testovi za warmup/207 ćelija, budžet, deterministički
replay, cleanup i containment/weather-horizon razliku. Ne mijenjati reward i glavu
modela usput bez zasebne odluke i kontrola.

Nakon usaglašenog obima i odgovarajućeg adaptera: zamrznuti scenarije/splitove,
izmjeriti trošak kratkog benchmarka, pa
tek planirati fine-tuning. [BACKLOG](docs/BACKLOG.md) čuva TASK-005/006 i dalje.
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
- `runs/`, `.venv/`, Docker image i veliki lokalni logovi: ponovo se generišu;
  mali provjereni rezultati i manifesti su u `reports/`.
- `private/`: originalna prepiska/slika rubrike ostaju privatni; javni sažetak
  zahtjeva je dovoljan za tehnički nastavak. Ne tražiti ih za setup/testove.

Dogrib služi početnom historijskom slučaju, ali dijeli fuel/elevation blok sa Sub20,
pa nije nezavisan test generalizacije. Njegov puni raster nije direktno kompatibilan
s 400-action politikom. CFSDS uzorak je dnevni, na 90 m, i traži dodatne FBP/weather
inpute; rad iz 2024 opisuje drugo, 180 m izdanje. [TASK-011 i detalji](docs/research/REAL_FIRE_DATASETS.md)
čuvaju vremenska/prostorna ograničenja. Ne preuzimati cijelu 48.4 GB WildfireSpreadTS arhivu.

## Spreman prompt za kolegu ili coding agenta

> Nastavi wildfire-rl-adaptation od TASK-012 — dataset refinement. Pročitaj HANDOFF,
> STATUS, DATASET, REAL_FIRE_DATASETS i PROTOCOL. Imamo inventar simulator inputa
> i pregledane male Dogrib/CFSDS uzorke; konačni izbor, uloga i obim nisu usaglašeni.
> Pripremi prijedlog izvora/podskupa, veze sa 20×20 modelom, vremenske/prostorne
> rezolucije, scenarija/splitova, metrika i granica zaključaka. Odvoji preporuke od
> odluka. Firehose runtime je već provjeren; TASK-004c je poznati tehnički nastavak
> nakon refinementa. Ne pokreći dugo treniranje, velika preuzimanja, plaćeni compute
> ili merge bez naloga. Nalaze i otvorene odluke zapiši u bazu znanja.
