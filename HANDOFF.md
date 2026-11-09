---
type: Playbook
title: Handoff za nastavak projekta
---
# Handoff za nastavak projekta

Stanje **2026-11-04**. Ovaj dokument i linkovani izvještaji daju kolegi ili agentu
potreban kontekst bez prethodne chat historije.

## Aktivni cilj i status

Aktivna putanja je **SimFire + FPA-FOD početni uslovi + FEDS-CONUS opaženi obodi**.
Godine požara određuju split: train 2018/2019, validation 2023, test 2024. FLE/ICS-209
je samo mogući post-hoc operativni kontekst.

Širi unaprijed spremljeni FPA-FOD okvir daje 99 train i 20 validation slučajeva od
208/56 kandidata; svih 119 ima 48h FEDS niz. Taj data-coverage gate prolazi, uz
ograničenje da je okvir većih požara u deset zapadnih saveznih država i nije
reprezentativan. Originalna kohorta od 60 slučajeva daje 19/40 i 7/20 pa ne prolazi.

**Koraci 5–8 su izvedeni 2026-11-04 (ADR-023–027).** TRAIN no-op gate je nakon dijagnoze
i preregistrovane mreže ponovo **FAIL**: persistence je jaka jer mnogi FEDS požari ne
rastu, dok slobodno-goreći SimFire raste. Gate zapis je zamrznut kao `FAIL_exploratory`,
a validation je skoriran jednom po zapisu. Intervencije, heuristike i PPO prilagodba
budžetu rađene su na zasebno označenom free-burn stress zapisu. Osnovni PPO smanjuje
štetu u odnosu na no-op, fine-tuning po budžetu nema mjerljive koristi, a downwind
heuristika je jednako dobra ili bolja. Sve je simulatorski i eksploratorno. Pogledaj
[STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md),
[benchmark sažetak](reports/real-fire-data/feds-simfire-policy-benchmark-v1.json) i
[ADR-027](docs/specs/DECISION_RECORDS.md). TEST 2024 nije učitan.

## Sljedeći posao

1. Timska odluka: growth-aware gate ili model zaustavljanja prije tvrdnje o kalibraciji;
   da li stress scenarij ostaje radni simulator za predaju.
2. Ako se nastavlja: nova preregistracija s jačim signalom budžeta i više seedova;
   TASK-007 (prioritetna područja); TASK-009 (poster).
3. TEST 2024 otvoriti tek na kraju, sa zaključanim politikama i istim protokolom.

**IoU** mjeri preklapanje simulirane i FEDS opožarene površine (1 je potpuno
preklapanje, 0 je bez preklapanja; nije procenat tačnosti). **WAF** je Wind Adjustment
Factor, SimFireov faktor koji podešava uticaj vjetra na širenje. FEDS je satelitska
procjena, a gridMET je grubi vremenski proxy, pa gate ne predstavlja fizičku validaciju.

## Gdje naći izvorne dokaze

- [SimFire/FEDS environment record](docs/research/SIMFIRE_ENVIRONMENT.md): runtime,
  setup, komande, inputi, no-op rezultati i PPO ograničenja.
- [FPA-FOD/FEDS crosswalk](docs/research/FPA_FEDS_CROSSWALK.md): cohort izbor,
  join pravilo, data gate i kasnije izmjene.
- [Experiment log](docs/research/EXPERIMENT_LOG.md): redoslijed i granice runova.
- [Mapa koda](knowledge/code-map.md): skripte, paketi i testovi.
- [Backlog](docs/BACKLOG.md): sljedeći taskovi; posljednja odluka ima prednost.

## Klon i lokalni environment

Grana `codex/overnight-steps-5-8` (izvedena iz PR #3 grane
`codex/fireline-simfire-benchmark`) sadrži korake 5–8; nijedna nije spojena. Za novi klon:

```sh
git clone --branch codex/overnight-steps-5-8 https://github.com/goralija/wildfire-rl-adaptation.git
cd wildfire-rl-adaptation
```

Prvo pročitaj [index](index.md), [AGENTS](AGENTS.md),
[projektni kontekst](knowledge/project-context.md), [STATUS](docs/STATUS.md),
[NEXT_SESSION](docs/NEXT_SESSION.md) i najnoviji ADR. FEDS/SimFire venv i veliki
inputi su lokalni u ignorisanom `.local/`; novi klon ih nema. Tačne pinove i obnovu
okruženja prati u `docs/research/SIMFIRE_ENVIRONMENT.md`. Na Harunovom računaru je venv samostalan
(`.local/uv-python` + `.local/simfire-venv`); obnova iz javnih izvora traje oko 30 min
i daje iste hashove ulaza.

Validation rasteri se preuzimaju s `--fetch-split validation` tek uz commitan freeze zapis; test split se ne preuzima. Ne commitovati `.local/`,
raw arhive, virtualna okruženja ili model težine. Izlazni run folderi trebaju imati
nov ID i ostati lokalni, osim ako mali manifest/report izričito pripada repo-u.

## Historijski rad

Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire i Firehose TASK-004c su raniji, odvojeni
trackovi. Njihovi runtime/no-action nalazi nisu SimFire validacija i ne određuju
trenutni naredni korak. Zadržani su u [experiment logu](docs/research/EXPERIMENT_LOG.md)
i pripadajućim historijskim dokumentima.
