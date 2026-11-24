---
type: Integration Review
title: Sažeta integracija SimFire i CA jezgre
---
# Manja grana za integraciju

## Opseg prije izmjena — 2026-11-24, ADR-058

Korisnik traži da izbacimo maksimalno nerelevantnih promjena. Istraživačka grana
`codex/separate-clip-pilot` na `c4062a84` ostaje sačuvana. Nova
`codex/ca-core-integration` polazi direktno iz `origin/main=f96f744f`.
Glavni klon i postojeći lokalni podaci/modeli se ne prepisuju.

**Pretpostavka:** za merge trebaju radni interfejsi i provjerene ispravke; historija
svake optimizer probe i sve per-case tabele ne trebaju biti dio integracijskog diffa.
**Provjerljivi cilj:** oko50fajlova i nekoliko hiljada dodanih redova, umjesto
228fajlova/345.775redova. Stara grana ima324.652dodanih redova u83report fajla.

Ostaju: TRAIN-only weather filtriranje, sigurna inicijalizacija output direktorija,
kategorijsko/lokalno/terrain opažanje i nonfuel maska, zajednička B1 akcija/nagrada,
CA bridge, osnovni MaskablePPO/numeric NPZ interfejs i relevantni regresijski testovi.
Native CA opservacijski ugovor ostaje kao priprema daljeg rada, bez tvrdnje o parity.

Izostaju: offline model pretrage, centrirani reward i zasebni clipping eksperimenti,
njihovi runneri/plot/bundle alati, velike tabele i duplirani startup/status zapisi.
Oni ostaju na arhivskoj grani i u njenom `.local` prostoru. Modeli se ne promoviraju.

Zavisnost encoder-a od starih offline learnera uklanja se izdvajanjem samo postojećeg
terrain536 zapisa. Prije predaje traži se identičnost njegovih vrijednosti sa
sačuvanim v2 opažajima, puni testovi, synthetic i native smoke, knowledge checker
i mali provenance sažetak. Originalni simulatori, četiri odluke, no-op i kumulativna
šteta ostaju isti. TEST2024 i novi VALIDATION/futureFEDS ostaju zatvoreni.

## Provjeren rezultat i naredni korak

TASK-046 je završio6×512koraka za18,49min. Sačuvani trening i384clipupdatea,12modela,
96native putanja i nezavisni procentni obračun prolaze lokalni audit. Ovo nije novi
freshfullrestore svih96putanja. Nema aktivnog računanja ili nove optimizer iteracije.

Isti14požara s pozitivnim vlastitim no-op rastom, prosjek3model seeda unutar požara:

| Metoda,512koraka/model | SimFire saved% | CA saved% |
| --- | ---: | ---: |
| Originalni PPO |6,75|6,36|
| Centrirana nagrada |3,16|7,93|
| Zaseban actor/critic clipping |5,11|6,36|
| Tačno uniformna prva legalna linija |5,23|6,20|
| Heuristika fronta |11,29|3,35|

Nijedna nova varijanta ne prolazi oba unaprijed zadana uslova: opisna donja95%granica
iznad0 prema original512 i uniformnom referentu. Model seedovi nisu dodatni požari.
TRAIN45/16je razvojni uzorak, nije nezavisan test. Raniji ADR022–028nalazi ostaju
nevažeći po ADR029; navedeni brojevi potiču iz kasnijih korigovanih eksperimenata.

[Kompaktan rezultat/provenance](../../reports/real-fire-data/ca-core-summary-v1.json)
zamjenjuje stotine hiljada redova u integracijskom diffu. Puni planovi, ADR033–057,
runneri i raniji izvještaji ostaju u [arhivi c4062a84](https://github.com/goralija/wildfire-rl-adaptation/tree/c4062a84a8454f17baa3d6ac8a7cb6f39aa0c3d8).
TASK046final analysis/NPZ i lokalni audit ostaju u starom worktreeu pod
`.local/separate-clip-v1/`; nisu uploadovani. Reprodukcija starih eksperimenata koristi
arhivski checkout i njegove provjerene ulaze, a ne obrisane research drivere u ovoj grani.

**Integracijske provjere:**326pinned/0skip,311modern/3skip,248core/35skip. Encoder je
byte-exact na svih456sačuvanih opažaja (98SF×4 i16CA×4), maksimalna razlika0. Native
smoke na jednom TRAINslučaju u oba backend-a ponavlja svih10no-op stanja i završne
burned/line maske iz stare tabele. Nema nove fizičke validacije ili treniranja.
Zadržani su svi testovi baze i testovi preostalih runtime komponenti; izostavljeni su
samo testovi izostavljenih research modula.

## Kako koristiti malu jezgru

Za osnovni synthetic smoke nije potreban SimFire ili PyTorch:

```sh
PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out .local/core-smoke-NEW
```

Za jedan postojeći TRAINslučaj, uz pinovano okruženje i provjerene lokalne ulaze:

```sh
nice -n 19 .local/simfire-venv/bin/python scripts/smoke_common_control.py \
  --backend both --scenario-id fpa-fod-400303584-goldstone \
  --out .local/common-control-NEW.json
```

CLI najprije računa vlastiti no-op samo za obračun nagrade, potom četiri pune odluke
s prvom legalnom linijom. Nema učenja ili future FEDS-a. `--policy noop` provjerava
no-op kontrolu. Izlaz je mali JSONreceipt; postojeći rezultat se ne prepisuje.

`control_factory.native_env` daje oba v2backend-a bez uvoza research runnera.
`CommonControlEnv` izlaže terrain536/Discrete9/B1/4×12h i charged reward;
`common_control_rl` čuva osnovni PPO i guardovani numeric NPZ save/load.
`CAObservationV2` je zaseban native-unit ugovor sa perfectly-current forcingom;
common-line bridge koristi lagged forcing. Njihova native parity nije ovdje riješena.

Ova B1/optimizer faza je završena s ograničenim negativnim nalazom. Sljedeće je review
**ove manje grane** i odluka o mergeu. Dalji CA control/native parity dizajn je nova
faza, s novim opsegom prije treninga. Stvarni VALIDATION/TEST2024 ostaju zatvoreni.
