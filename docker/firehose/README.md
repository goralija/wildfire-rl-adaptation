---
type: Runbook
title: Izolovana Firehose provjera bez treniranja
---
# Izolovana Firehose provjera bez treniranja

Testirano na lokalnom Docker Desktopu, Linux ARM64. Legacy runtime nije projektni
Python >=3.11 paket: probe se izvršava kao zaseban fajl u Python 3.8 kontejneru.
Image sadrži originalni GPL Firehose izvor i checkpointove; ne objavljivati ga bez
provjere licenci za uključene podatke i modele.

## Izvori za čisti checkout

```sh
git clone https://github.com/aidan-curtis/firehose.git external/firehose
git -C external/firehose checkout e49a52a9a987a1585d25ddca2f711222ca500ffb
git clone https://github.com/williamshen-nz/stable-baselines3-contrib.git external/sb3-contrib-legacy
git -C external/sb3-contrib-legacy checkout 43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3
```

Za postojeći sparse checkout Firehose moraju biti uključeni `cell2fire/Cell2FireC`,
`cell2fire/firehose`, `cell2fire/utils`, `data/Sub20x20` i dva 20×20 model ZIP-a.
Raw izvori i težine ostaju u ignorisanom external/ direktoriju.

Docker build primjenjuje lokalni patch
[`cfsds_initial_state.patch`](cfsds_initial_state.patch) na pinovani upstream izvor.
Opcioni `InitialState.csv` podržava dnevni historical case i ima format
`state,ncell`, gdje je `state` `burnt` ili `burning`, a `ncell` je one-based
row-major ID. Aktivna ivica i starija opožarena površina ostaju odvojene u C++
stanju i gridovima. Kada fajl nedostaje, postojeći Firehose slučajevi zadržavaju
dosadašnju logiku i izgled opažanja.

## Build i provjera

Iz korijena projekta:

```sh
docker build --file docker/firehose/Dockerfile --tag wildfire-firehose-probe:20261030-initial-state .
mkdir -p runs/firehose-new-check
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --read-only   --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m   --cap-drop ALL --security-opt no-new-privileges -e MPLCONFIGDIR=/tmp/mpl   -v "$PWD/runs/firehose-new-check:/outputs"   wildfire-firehose-probe:20261030-initial-state timeout 300 python /opt/firehose_verify_batch.py
```

Folder `/outputs/final` mora biti nov. 12 kratkih rollouta ima pojedinačni limit 90 s;
ukupan command cap je 300 s. Nema `learn()` poziva. Raw gridovi i logovi su lokalni,
a mali JSON sažeci i manifesti idu u Git. Runtime nema mrežu i vidi samo output mount.
Build ima mrežu za zvanične Debian/PyPI zavisnosti; `.dockerignore` isključuje privatne
fajlove i moderni .venv iz build contexta.

Za jedan model:

```sh
docker run --rm --network none --cpus 2 --memory 2g --read-only   --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m   -e MPLCONFIGDIR=/tmp/mpl -v "$PWD/runs/firehose-new-check:/outputs"   wildfire-firehose-probe:20261030-initial-state timeout 100 python /opt/firehose_probe.py   --policy ppo-fixed --seed 123 --budget 8 --sync-reset --out /outputs/one-model
```

## Početni historijski front

Ovaj kratki inference-only check provjerava import jedne stare opožarene ćelije i
dva aktivna fronta. Pokreće se unutar imagea, nakon Docker builda:

```sh
mkdir -p runs/initial-state-check
docker run --rm --network none --cpus 2 --memory 2g --pids-limit 128 --read-only \
  --tmpfs /tmp:rw,nosuid,size=256m --tmpfs /opt/firehose/input:rw,nosuid,size=128m \
  --cap-drop ALL --security-opt no-new-privileges -e MPLCONFIGDIR=/tmp/mpl \
  -v "$PWD/runs/initial-state-check:/outputs" \
  wildfire-firehose-probe:20261030-initial-state python /opt/firehose_verify_initial_state.py
```

Provjeravač učitava malu fixturesku mapu: 1 ranije izgorjela ćelija i 2 aktivne
ćelije ruba. Bez RL modela i bez intervencija provjerava da C++ prijavi isto stanje,
da se Python početna slika poklapa s C++ gridom i da se proces uredno završi.
Fixture potvrđuje sam C++ import sa minimalnom mapom, ne stvarnu požarnu fiziku.
Dodatno je pokrenut pravi CFSDS slučaj `2018_747`: 175 ranije izgorjelih ćelija i 31
aktivna ćelija na frontu. Šest no-action C++ ponavljanja, bez treninga i intervencija,
dalo je istu završnu mapu: 66 ha prema 15.39 ha opaženih; svih šest dotaklo je rub
modelskog prozora. To je mismatch dijagnostika, ne fizička validacija. Vidi [case
manifest](../../reports/real-fire-data/2018_747-case.json), [replay report](../../reports/real-fire-data/2018_747-day228-replay.json),
[seed ponavljanja](../../reports/real-fire-data/2018_747-seed-sweep.json) i
[mapu](../../reports/real-fire-data/2018_747-day228.png). Fixture sažetak,
Docker image ID i hashovi su u
[`initial-state-import-smoke.json`](../../reports/real-fire-data/initial-state-import-smoke.json).

Prvi istorijski `InitialState.csv` sada je izvezen i C++ importer ga učitava. Standardni
Sub20 `FireEnv` reset/damage i termination reason još nisu potpuno popravljeni: opcija
`--sync-reset` je zasebna dijagnostička korekcija, ne konačan TASK-004c adapter. Sljedeći
korak je provjeriti poravnanje/mismatch kroz više train slučajeva i dovršiti terminalni
state/cumulative-damage export.
Za drugu arhitekturu/OS potrebno je zasebno provjeriti build i wheel dostupnost;
postojeći freeze nije obećanje x86/GPU/Colab kompatibilnosti.
