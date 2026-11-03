---
type: Playbook
title: Handoff za nastavak projekta
---
# Handoff za nastavak projekta

Stanje **2026-11-03**. Ovaj dokument i linkovani izvještaji daju kolegi ili agentu
potreban kontekst bez prethodne chat historije.

## Aktivni cilj i status

Aktivna putanja je **SimFire + FPA-FOD početni uslovi + FEDS-CONUS opaženi obodi**.
Godine požara određuju split: train 2018/2019, validation 2023, test 2024. FLE/ICS-209
je samo mogući post-hoc operativni kontekst.

Širi unaprijed spremljeni FPA-FOD okvir daje 99 train i 20 validation slučajeva od
208/56 kandidata; svih 119 ima 48h FEDS niz. Taj data-coverage gate prolazi, uz
ograničenje da je okvir većih požara u deset zapadnih saveznih država i nije
reprezentativan. Originalna kohorta od 60 slučajeva daje 19/40 i 7/20 pa ne prolazi.

**SimFire no-op provjera na svih 99 TRAIN slučajeva je završena, ali gate je pao.** Osam
WAF kandidata nije nadmašilo obje reference (persistence i 2:1 elipsu) istovremeno po
mean IoU i grešci površine uz nula rubnih kontakata. Persistence IoU=.5343, elipsa
IoU=.5308, najbolji SimFire IoU=.4769. WAF i interni korak nisu izabrani. Pogledaj
[TRAIN no-op screen](reports/real-fire-data/feds-simfire-train-noop-screen-v1.json),
[STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md) i [ADR-022](docs/specs/DECISION_RECORDS.md).

Okruženje i TRAIN-only MaskablePPO putanja mogu se tehnički pokrenuti. 64-step PPO
smoke samo provjerava izvršavanje, save/load i rollout; nije benchmark, fizička
validacija niti dokaz RL koristi. Duži benchmark trening čeka dijagnostiku i prolaz
novog TRAIN-only no-op gatea. Validation rasteri nisu preuzeti; test 2024 nije učitan.

## Sljedeći posao

1. Pregledati po-požar izvještaje i dijagnosticirati ulazne/prostorne razloge nesklada:
   gridMET proxy, wind/moisture konverziju, rasterizaciju, LANDFIRE i dimenzije mreže.
2. Prije pokretanja zapisati mali skup zajedničkih TRAIN parametara. Ne podešavati po
   požaru i ne mijenjati persistence/elipsa pravila nakon gledanja rezultata.
3. Ponoviti no-op gate na istoj kohorti i kriterijima. Validation mape koristiti tek
   nakon prolaza TRAIN kandidata i zamrzavanja parametara.
4. Prije policy poređenja definisati akciju i osigurati iste scenarije, budžete,
   horizonte, informacije i seedove za sve politike. TEST otvoriti tek na kraju.

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

PR/grana `codex/fireline-simfire-benchmark` sadrži aktivni rad; PR je draft i nije
mergovan. Za novi klon:

```sh
git clone --branch codex/fireline-simfire-benchmark https://github.com/goralija/wildfire-rl-adaptation.git
cd wildfire-rl-adaptation
```

Prvo pročitaj [index](index.md), [AGENTS](AGENTS.md),
[projektni kontekst](knowledge/project-context.md), [STATUS](docs/STATUS.md),
[NEXT_SESSION](docs/NEXT_SESSION.md) i najnoviji ADR. FEDS/SimFire venv i veliki
inputi su lokalni u ignorisanom `.local/`; novi klon ih nema. Tačne pinove i obnovu
okruženja prati u `docs/research/SIMFIRE_ENVIRONMENT.md`. U ovom računaru SimFire
`bin/python` trenutno koristi kompatibilni Python 3.9.25 iz susjednog
`cfsds-train-qc` worktreea; ne uklanjati taj worktree dok se runtime ne zamijeni
samostalnom kopijom.

Validation rasteri i test split nisu dio setup preuzimanja. Ne commitovati `.local/`,
raw arhive, virtualna okruženja ili model težine. Izlazni run folderi trebaju imati
nov ID i ostati lokalni, osim ako mali manifest/report izričito pripada repo-u.

## Historijski rad

Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire i Firehose TASK-004c su raniji, odvojeni
trackovi. Njihovi runtime/no-action nalazi nisu SimFire validacija i ne određuju
trenutni naredni korak. Zadržani su u [experiment logu](docs/research/EXPERIMENT_LOG.md)
i pripadajućim historijskim dokumentima.
