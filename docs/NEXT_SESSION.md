---
type: Handoff
title: Nastavak — provjeriti mjerodavnost SimFire okruženja
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/BACKLOG.md
  - resource: /docs/research/SIMFIRE_FPA_COHORT.md
  - resource: /docs/research/SIMFIRE_RL_ADAPTER.md
---
# Nastavak rada

## Trenutna osnova

Aktivna kohorta je `fpa-fod-western-us-2018-2024-v2`: 80 stvarnih požara, podijeljenih po
cijelim incidentima na 40 train / 20 validation / 20 test. Fuel i terrain su preuzeti i
provjereni za svih 80. Ne trenirati koristeći historijsku finalnu površinu ili perimetar kao
nagradu. Vidi [dataset opis](research/SIMFIRE_FPA_COHORT.md).

SimFire 2.0.1 je u `external/simfire` na commitu
`04905b19fe8c10dc08d64faddd00303e0561bb66`. RL adapter je
[`src/wildfire_rl/simfire_gym_env.py`](../src/wildfire_rl/simfire_gym_env.py), CNN politika
je u [`simfire_policy.py`](../src/wildfire_rl/simfire_policy.py). Smoke za train/validation/test
je prošao, ali nije trenirao težine: vidi
[`simfire-cohort-v2-gym-smoke`](../reports/real-fire-data/simfire-cohort-v2-gym-smoke/).

**Trenutno:** weather je preuzet i pretvoren u dnevni proxy za svih 80 slučajeva; no-op i
adapter smoke receipti prolaze. SimFire koristi 15 jednominutnih koraka po zapaljenoj ćeliji
jer stock 4 nije bilo dovoljno za neke fronte preko 30 m rastera. Ta postavka je tehnička,
ne fizički kalibrisana. Vjetar/vlaga su otvorene aproksimacije; policy nije treniran. Pogledati
[`mapping receipt`](../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json),
[80-case QC](../reports/real-fire-data/simfire-cohort-v2-gridmet-summary.json) i
[weather figure](../reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png), te
[no-op probe](../reports/real-fire-data/simfire-cohort-v2-gridmet-noop-horizon/).

**Poredbena pravila su unaprijed zapisana** u
[`SIMFIRE_EVALUATION_PROTOCOL.md`](research/SIMFIRE_EVALUATION_PROTOCOL.md), a inference-only
runner je `scripts/evaluate_simfire_benchmark.py`. Preflight provjerava samo VALIDATION i ne
pokreće simulacijski korak. Samo 40 TRAIN incidenata smije se koristiti za učenje; 20
VALIDATION bira checkpoint; 19 test incidenata ostaje rezervisano za finalnu uparenu
procjenu. Larch Creek je već korišten u smoke-u i izbačen iz završnog benchmarka. Nijedna
train komanda nije pokrenuta.

Evaluation membership je zabilježen u
[`simfire-fpa-fod-evaluation-membership-v1.json`](../data/manifests/simfire-fpa-fod-evaluation-membership-v1.json).
Ovaj manifest zamrzava članstvo; benchmark ugovor, seedovi, metrike, checkpoint pravilo i
runner su u `configs/simfire/evaluation-v1.json` i protokolu iznad.

## Lokalni environment

macOS ARM64, Python 3.9.25, `.local/simfire-venv` (ignorisan):

```sh
git clone https://github.com/mitrefireline/simfire.git external/simfire
git -C external/simfire checkout 04905b19fe8c10dc08d64faddd00303e0561bb66
python3.9 -m venv .local/simfire-venv
.local/simfire-venv/bin/python -m pip install -r requirements/simfire-macos-arm64-py39.freeze.txt
.local/simfire-venv/bin/python -m pip install -r requirements/simfire-rl-macos-arm64-py39.freeze.txt
.local/simfire-venv/bin/python -m pip install ./external/simfire
```

RL paketi su Gymnasium 1.1.1, PyTorch 2.3.1, SB3 2.7.1 i sb3-contrib 2.7.1. SB3 2.7.1
je posljednja verzija te biblioteke koja podržava Python 3.9; ovo nije recept za Linux ili
Windows.

## Podaci i komande

Ponoviti manifest iz sačuvanih izvora (offline rebuild), preuzeti karte goriva/terena ako
lokalni raw folder nedostaje, pa riješiti start ćelije:

```sh
.local/simfire-venv/bin/python scripts/build_simfire_fpa_cohort.py --offline
.local/simfire-venv/bin/python scripts/fetch_simfire_cohort_inputs.py --workers 3 --skip-weather
.local/simfire-venv/bin/python scripts/resolve_simfire_seed_cells.py
.local/simfire-venv/bin/python scripts/fetch_gridmet_cohort_weather.py --workers 4
.local/simfire-venv/bin/python scripts/summarize_gridmet_cohort.py
python3 scripts/map_gridmet_weather_to_simfire.py --wind-adjustment-factor 0.3
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy
.local/simfire-venv/bin/python scripts/smoke_simfire_noop_horizon.py --splits train validation
```

`fetch_gridmet_cohort_weather.py` čuva originalne dnevne point vrijednosti; mapping skripta
zatim pravi odvojeni proxy za SimFire. Tačan satni replay ne postoji. WAF osjetljivost 0.1,
0.3 i 0.5 je tehnički smoke-testirana; fizička ispravnost pretpostavki nije potvrđena.

Raw rasteri i eventualni vremenski JSON ostaju u ignorisanom `.local/`; manifesti, source
snapshotovi, hashovi, mali receiptovi i pregledne slike idu u Git.

## Šta je sljedeće

1. Lokalni validation preflight je već prošao 20/20 ulaznih paketa bez napredovanja
   simulacije. Na drugom računaru/klonu ponoviti instalaciju i podatke, pa pokrenuti:
   `.local/simfire-venv/bin/python scripts/evaluate_simfire_benchmark.py --preflight-only`.
2. Prije treninga definisati base PPO trening recept, fine-tuning budžet i raspored čuvanja
   checkpointa; pregledati vremenske i spread pretpostavke.
3. Trening/fine-tuning tek nakon posebne izričite odluke. Koristiti samo TRAIN za učenje,
   VALIDATION za izbor, a test za finalnu uparenu procjenu.
4. Sačuvati CSV/JSON epizode, checkpoint hashove i georeferencirane mape/animacije.

**Još nije urađeno:** agent trening, fine-tuning, held-out policy rezultat ili fizička
validacija. Pogledati [status](STATUS.md), [backlog](BACKLOG.md) i
[adapter spec](research/SIMFIRE_RL_ADAPTER.md).
