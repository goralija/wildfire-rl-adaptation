---
type: Data Quality Audit
title: FPA-FOD, FEDS-CONUS i FLE — crosswalk i pre-agent gate
status: current
sources:
  - resource: /data/manifests/fireline-benchmark-cohort-v1.json
  - resource: /reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json
  - resource: https://zenodo.org/records/22921773
  - resource: https://www.ess.uci.edu/~uci-nasa-firetracking/
  - resource: https://www.fs.usda.gov/rds/archive/catalog/RDS-2025-0011
---
# FPA-FOD, FEDS-CONUS i FLE — crosswalk i pre-agent gate

## Trenutna odluka — 2026-11-03

**Originalna 60-case FPA-FOD kohorta ne prolazi prag:** lokalni audit nad kompletnim,
checksum-verifikovanim FEDS arhivama nalazi 19/40 train i 7/20 validation slučajeva.
Pošto je train za jedan slučaj ispod praga 20, ta kohorta nije dovoljna za planirani
benchmark.

Uveden je odvojeno označen, unaprijed spremljen širi candidate frame: svi 264 zapisa iz
FPA-FOD screenova za iste dozvoljene godine (208 train iz 2018/2019; 56 validation iz
2023). Koristi se isti godišnji split i nepromijenjeno pravilo datuma, tačke, radijusa,
jedinstvenosti i minimuma. Rezultat je **99/208 train** i **20/56 validation**; svih
119 odabranih događaja ima pet uzastopnih FEDS stanja od početnog opaženog stanja do
48 sati. Širi frame doseže unaprijed postavljene pragove 20/8 i njegov pre-agent
coverage gate je **PASS**. Ova promjena candidate-universe je dokumentovana u
[ADR-018](../specs/DECISION_RECORDS.md), bez tihog mijenjanja kriterija ili testa.

| Kohorta | Split | Screen slučajevi | Jedinstven rani FEDS match + ≥2 stanja | Pun 48h niz | Prag |
| --- | --- | ---: | ---: | ---: | ---: |
| Originalna kohorta | Train | 40 | 19 | 19 | ≥20 |
| Originalna kohorta | Validation | 20 | 7 | 7 | ≥8 |
| Prošireni candidate frame | Train | 208 | 99 | 99 | ≥20 |
| Prošireni candidate frame | Validation | 56 | 20 | 20 | ≥8 |

Proširenje je formirano prije FEDS spajanja iz cijelog sačuvanog godišnjeg FPA-FOD
screen okvira za dozvoljene godine. Frame zahtijeva poznat datum i lokaciju, MTBS ID i
prijavljenu površinu ≥5.000 acres u deset zapadnih saveznih država; zato rezultat nije
reprezentativan za sve američke požare. Ta površina utiče samo na unaprijed definisani
screen incidenata. Ne ulazi u FEDS fireID join, početno stanje, nagradu ili izbor
checkpointa. MTBS ID, završni obod, FLE rezultat i 2024 test ne biraju FEDS događaj.

FEDS-CONUS nema FPA-FOD ID. Fiksno pravilo traži FEDS `t_st` datum od 1 dan prije do
2 dana poslije FPA-FOD datuma otkrića, te barem jedan obod najviše 3 km od FPA-FOD
referentne tačke između `t_st` i `t_st + 24 h` uključivo. Kandidat se koristi samo ako
je jedinstven. Nakon identifikacije `fireID`, audit pročita cijeli njegov vremenski niz,
uključujući obode koji su kasnije otišli izvan početnog radijusa. Episode manifest
zatim zadržava samo požare s pet tačnih 12h stanja od prvog kvalifikovanog početnog
opažanja do +48h. FPA tačka/datum imaju nepoznatu događajsku nesigurnost; crosswalk je
provisional veza, ne ground truth.

Prethodni rezultat 13/40 train i 7/20 validation koristio je udaljeni `/vsicurl/`
pristup, a validation postfilter sačuvanih kandidata. Nakon preuzimanja cijelih FEDS
perimeter arhiva sa službenim checksummima, lokalni pregled iste originalne kohorte
otkrio je još šest jedinstvenih train podudaranja iz 2019. Stari izvještaj ostaje kao
istorijski trag, dok [lokalno ponovljen izvještaj](../../reports/real-fire-data/fpa-feds-original-cohort-crosswalk-local-v1.json)
predstavlja aktuelni rezultat za originalni 60-case uzorak.

Godišnji FEDS perimetri 2018, 2019. i 2023. su preuzeti lokalno, MD5 je potvrđen prema
Zenodo manifestu, a sirovi fajlovi ostaju u ignorisanom `.local/feds-conus/`. Njihov
ukupni sadržaj nije stavljen u Git. [FPA-FEDS candidate-frame report](../../reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json)
i [episode manifest](../../data/manifests/feds-episode-cohort-v1.json) sadrže male
rezultate/provenance.

FLE incidentni join iz starog audit-a postoji za 0/40 train i 13/20 validation zapisa;
to je agregirani incidentni sažetak, ne line-level geometrija. Prošireni crosswalk je
namjerno rađen sa `--skip-fle`; line-level operativne podatke i njihove ishode treba
pribaviti odvojeno, uz očuvanje istih train/validation godina. FEDS `lf_fireline` je
satelitski opažen aktivni front, a ne USFS izgrađena suppression linija. Završni FLE
ishod je post-hoc i nije uzročna procjena ishoda linije u counterfactual epizodi.

Izvorni i novi redovi su sačuvani u [originalnom crosswalk-u](../../reports/real-fire-data/fpa-feds-original-cohort-crosswalk-local-v1.json),
[proširenom candidate-frame crosswalk-u](../../reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json),
[train split-u](../../reports/real-fire-data/fpa-feds-candidate-frame-train-v1.json)
i [validation split-u](../../reports/real-fire-data/fpa-feds-candidate-frame-validation-v1.json).
Reproducibilne skripte su
[`audit_feds_fpa_fle_crosswalk.py`](../../scripts/audit_feds_fpa_fle_crosswalk.py),
[`fetch_feds_archive.py`](../../scripts/fetch_feds_archive.py) i
[`build_feds_episode_manifest.py`](../../scripts/build_feds_episode_manifest.py).
Naredbe za lokalni checksum-aware audit:

```sh
python scripts/fetch_feds_archive.py --year 2018 2019 2023 --layer perimeter
python scripts/audit_feds_fpa_fle_crosswalk.py --cohort data/manifests/fpa-feds-candidate-frame-v1.json --split train --skip-fle --out reports/real-fire-data/fpa-feds-candidate-frame-train-v1.json
python scripts/audit_feds_fpa_fle_crosswalk.py --cohort data/manifests/fpa-feds-candidate-frame-v1.json --split validation --skip-fle --out reports/real-fire-data/fpa-feds-candidate-frame-validation-v1.json
python scripts/audit_feds_fpa_fle_crosswalk.py --combine-split-reports reports/real-fire-data/fpa-feds-candidate-frame-train-v1.json reports/real-fire-data/fpa-feds-candidate-frame-validation-v1.json --out reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json
python scripts/build_feds_episode_manifest.py
```

**Jedan zapis po FEDS požaru (ADR-030 §6, TASK-027, 2026-11-09).** Crosswalk je za FPA
zapise `fpa-fod-400305302-sugar-pine` i `fpa-fod-400389825-columbus` izabrao isti FEDS požar
(fireID 58826, isti start), pa bi ista epizoda ušla dvaput u TRAIN. Generator manifesta sada
zadržava zapis s najnižim `fod_id` po FEDS požaru i isključene zapise upisuje u
`deduplication.excluded_records`; FEDS požar spojen sa zapisima iz dva splita zaustavlja
generator. Pravilo je u generatoru, a ne ručna izmjena manifesta, da bi se manifest mogao
ponovo izgraditi iz candidate-framea i crosswalka (provjereno: prije izmjene generator je
reprodukovao stari manifest bajt po bajt osim `created_utc`). Rezultat: 118 epizoda,
98 TRAIN i 20 VALIDATION. Coverage, preflight i input izvještaji izrađeni ranije i dalje
navode 119 zapisa; skripte uzimaju slučajeve iz manifesta, pa višak zapisa ne ulazi u run.

## Izvori i šta oni podržavaju

- FEDS-CONUS arhiva je verzija v1 objavljena 2026-10-02, 2012–2025; `lf_perimeter`
  fajlovi sadrže postprocesirane obode velikih požara preko 4 km² na 12-satnim
  koracima, izvedene iz VIIRS aktivnih detekcija rezolucije 375 m. Zenodo metapodaci
  daju CC BY 4.0 i checksume korištenih fajlova. [FEDS arhiva](https://zenodo.org/records/22921773),
  [zvanični FEDS pregled](https://www.ess.uci.edu/~uci-nasa-firetracking/).
- Zvanični NRT OGC servis nije zamjena za ovu arhivu kroz sve godine: njegova
  dokumentacija navodi 2018–2021 za Western US i 2025–danas za North America; 2023
  slučajevi zato dolaze iz objavljene arhive. [FEDS NRT FAQ](https://earth-information-system.github.io/fireatlas/docs/nrt.html).
- FLE RDS izdanje obuhvata linije i ishode iz NIFC operativnih podataka 2017–2024;
  Forest Service navodi da se podaci mogu koristiti bez naknade ili dodatne dozvole.
  Ovdje korišten ArcGIS sloj daje grupisane sažetke. Za prostorni obračun linija treba
  odvojeno pribaviti i provjeriti RDS geometrije. [RDS-2025-0011](https://doi.org/10.2737/RDS-2025-0011),
  [opis istraživačkog izdanja](https://www.fs.usda.gov/rds/archive/catalog/RDS-2025-0011).
- GOFER daje satne obode i aktivne linije, ali objavljeni pilot je 28 vrlo velikih
  požara u Kaliforniji 2019–2021, uz grublju GOES prostornu rezoluciju oko 2 km;
  odličan je dodatni vremenski izvor gdje postoji, ali ne pokriva validation 2023 i
  nije tiha zamjena za kohortu. [GOFER studija](https://essd.copernicus.org/articles/16/1395/2024/).
- FEDS-MTBS je alternativni način identifikacije preko MTBS ID-ja, ali FEDS tracking
  je ograničen konačnim Landsat/MTBS obodom; dokumentacija navodi da završni obod
  ograničava tracking. To je prikladno za ograničenu vizualnu rekonstrukciju, ne za
  nezavisni no-action gate niti kao isti benchmark. [FEDS-MTBS opis](https://www.ess.uci.edu/~uci-nasa-firetracking/),
  [arhiva](https://zenodo.org/records/20187963).
- ICS-209-PLUS daje dnevni kontekst o incidentu i resursima (1999–2020), ali nema
  dokaz da je određeni broj ljudi/opreme radio na određenoj liniji. Zato se u
  counterfactual benchmarku koriste jednaki standardizirani budžeti za sve politike;
  ICS podaci mogu biti samo incidentni kontekst za godine pokrivenosti. [USFS ICS-209-PLUS](https://research.fs.usda.gov/firelab/products/dataandtools/ics-209-plus).
- SimFire/SimHarness rad opisuje agentni simulator i akcije intervencije, ali ne
  pretvara runtime test u fizičku validaciju. Predloženi zaključak ostaje ograničen
  na politiku unutar kalibrisanog simulatora. [SimFire i SimHarness rad](https://arxiv.org/abs/2311.15925).
- W.I.S.E. evaluacija poredi mnogo 12-satnih oboda i eksplicitno prikazuje koliko se
  metrika može uljepšati ako se trajanje biranja oboda odabere po najboljem F1 za
  svaki posmatrani dan. Ovdje zato nema podešavanja svakog požara prema njegovom
  završnom obodu. [W.I.S.E. evaluacija](https://doi.org/10.1071/WF26072).

## Gateovi i sadašnje stanje

Završena je checksum-verifikacija FEDS `lf_fireline` sloja za 2018/2019/2023. Tačan
početni front postoji za 119/119 epizoda; fronti se nalaze unutar jedne 375m izvorne
ćelije od odgovarajućeg FEDS perimetra. Pogledaj
[active-front audit](../../reports/real-fire-data/feds-active-front-coverage-v1.json).
FEDS front je satelitski aktivni front, ne izgrađena suppression linija.

Preflight je potvrdio da svih 119 početnih geometrija stane u dogovorenu 256×256×180m
mapu. FEDS poligon postaje istorijski scar; linija istog `fireID+t` postaje višestruko
aktivno stanje. [Preflight izvještaj](../../reports/real-fire-data/feds-simfire-grid-preflight-v1.json)
ne koristi buduće obode za kreiranje starta. LANDFIRE LF2016/LF2022 FBFM13 i LF2020
terrain izvatci provjereni su na jednom train požaru; bulk mapiranje svih train
slučajeva ostaje otvoreno.

gridMET `th`, `vs`, `fm100` arhive za 2018/2019/2023 su checksum-verifikovane i
uzorkovane na četiri 12h segmenta za svih 119 slučajeva. WAF nije kalibrisan, a daily
historijski forcing ostaje skriven od policy observacija. Jedan kratki SimFire no-op
smoke sa demo vjetrom/vlagom potvrđuje samo integraciju inputa; to nije spread validacija.
Detalji su u [environment record](SIMFIRE_ENVIRONMENT.md) i
[gridMET provenance](../../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json).

Pre-agent data gate je prošao za prošireni okvir, a inputi su postavljeni: LANDFIRE
fuel/terrain i početne FEDS maske postoje za 99/99 TRAIN slučajeva. Zatim je kohortni
TRAIN-only no-op screen završen za osam WAF kandidata; **nijedan nije prošao** unaprijed
zadan uslov prema persistence/elipsi i rubu mape. Mjere, reference i run receipt hashovi
su u [screen reportu](../../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json)
i [ADR-022](../specs/DECISION_RECORDS.md).

Sljedeći research korak je dijagnosticirati po-požar neslaganje i provjeriti gridMET
forcing, vjetar/vlagu, rasterizaciju i SimFire prostorni odgovor. Zatim dokumentovati
mali zajednički kandidat skup i ponoviti isti TRAIN-only gate. Ne mijenjati baseline,
score rule ili postavke po požaru radi prolaza. Validation rasteri se mogu koristiti
tek nakon TRAIN gate prolaza i zamrzavanja postavki; 2024 TEST ostaje zatvoren.

Crosswalk/environment izvještaji potvrđuju data/runtime pokrivenost, ne fizičku
validaciju ili RL rezultat. Tehnički PPO smoke je dostupan, ali benchmark/policy-benefit
trening ostaje blokiran do gate prolaza. FEDS je satelitska procjena, gridMET proxy, a
aktivni `lf_fireline` sloj nije izgrađena suppression linija.
