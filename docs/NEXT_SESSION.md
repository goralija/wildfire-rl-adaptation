---
type: Handoff
title: Nastavak nakon prvog stvarnog CFSDS replaya
---
# Naredna sesija

## Trenutno stanje

Najnoviji TASK-015 pomak: per-cell fuel QC za svih 20 train kandidata. Deset prolazi
**samo gorivni gate**, deset pada; svih 20 imaju geometrijski ispravan susjedni front/cilj
na 20×20 gridu. Od tri postojeća no-action replaya (`2018_747`, `2018_241`, `2018_1770`),
sva tri prolaze fuel-only provjeru. Nijedan kandidat time nije proglašen potpunim ili
fizički validiranim slučajem. Pogledati [metod i nalaz](research/CFSDS_TRAIN_QC.md) i
[detaljni JSON](../reports/real-fire-data/cfsds-train-fuel-qc.json). Audit je koristio
samo train događaje za overlay; zajednički screen JSON sa svim podjelama bio je učitan,
ali validation/test fuel i CFSDS rasteri nisu otvarani. Nije bilo simulator replays,
treniranja ni kalibracije.

Glavni pravac je izabran: **Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire**. Razlog je
kompatibilnost s simulatorom i postojećim 20×20 agentom. Tri train slučaja (`2018_747`,
`2018_241`, `2018_1770`) su pretvorena i pokrenuta bez intervencija i bez treniranja.
Za `2018_747` imamo šest seedova; druga dva zasad imaju po jedan.

No-action rezultat za `2018_747` je 66 ha prema 15.39 ha opaženih (IoU .2187); šest
seedova daje istu mapu, a predikcija dotiče rub. Za `2018_241` simulator je zahvatio
svih 400 ćelija i dodao 237 ha prema 12.15 ha (IoU .0376); za `2018_1770` dodao je
73 ha prema 12.15 ha (IoU .1361). Prva dva slučaja ponovljena su bez 20-minutnog
početnog zagrijavanja s istim završnim mjerama. Kandidat `2014_538` nije prošao
konverziju jer historijske ćelije padaju na vodu/ne-gorivo u FBP karti. Nepoznat status
gašenja ostaje moguć uzrok razlike, ali ovo nisu fizička validacija ni rezultat agenta.

Važni artefakti:

- [jednostavno X/Y objašnjenje i konverzija](../docs/research/REAL_CASE_PIPELINE.md)
- [izbor skupa i granice zaključaka](../docs/research/REAL_FIRE_DATASETS.md)
- [split manifest s preliminarnim fire ID-jevima](../data/manifests/cfsds-v1_1-pilot-cohort.json)
- [case ulazi i provenance](../reports/real-fire-data/2018_747-case.json)
- [replay mjere](../reports/real-fire-data/2018_747-day228-replay.json)
- [vizualna karta](../reports/real-fire-data/2018_747-day228.png)
- [dodatni train slučajevi, karte i fuel odbijanje](../reports/real-fire-data/README.md)

## Nastavak rada

1. Sljedeći je TASK-018: dijagnosticiraj veliko no-action širenje u tri postojeća
train replaya. Na njima nije nađen preklop s isključenim fuel kategorijama; to ne
isključuje neodgovarajući fuel vintage ili FBP postavke. Uporedi sačuvane case
manifest/hashove, FBP special parameters, vremenske jedinice/profil i FWI, početni
front te 20×20 domen. Prvo zabilježi šta ulazi kažu, zatim predloži male kontrolisane
train-only provjere. Ne podešavaj prema validation/test ciljevima i ne mijenjaj agente.
2. Odredi može li 20×20 prozor predstaviti događaj bez rubnog rezanja. Ako je potreban
40×40 model, to mijenja agentov ulaz i broj akcija; prvo uradi poseban feasibility check,
ne predstavljaj ga kao isti pretrained agent.
3. Prije heldout slučajeva pribavi FBP fuel vintages koji odgovaraju periodu:
2014 za train slučajeve 2014–2018, 2019 za validation 2019–2021, 2024 za test 2022–2024.
4. Pokušaj povezati fire ID-jeve sa službenim incident/suppression zapisima i označi
nepoznate slučajeve. Trenutni geometrijski screen daje do pet kandidata godišnje i nije
iscrpan; pun benchmark tek treba usaglasiti.
5. Proširi TASK-004c: pouzdan cumulative-damage export i terminalni razlog (containment
naspram isteka vremenskih ulaza). TASK-017 initial-state import i tri TASK-016 konverzije
su ostvareni.
6. Dodaj/validiraj još train-only FireCaseove nakon zatvaranja njihovih ulaznih gateova.
7. Pokreni glavni agent benchmark/fine-tuning tek kad no-action ponašanje prođe gate na
više train požara i heldout ID-jevi budu zamrznuti.

## Lokalno okruženje

Moderni Python 3.12.4 `.venv` ima GIS i knowledge pakete. Legacy Firehose radi u zasebnom
Linux ARM64 Docker imageu. Sirovi CFSDS, DEM i FBP fajlovi su u Git-ignorisanom
`data/raw/`; generisani simulator paketi su pod `runs/`. U čistom checkoutu pribavi ih
prema [manifestu preuzimanja](../reports/real-fire-data/cfsds-download-manifest.json)
i ponovi build skriptom. Ne instaliraj legacy pakete u moderni venv.

Prije predaje pokreni testove, synthetic CLI smoke i `python3 scripts/validate_knowledge.py --strict`.
