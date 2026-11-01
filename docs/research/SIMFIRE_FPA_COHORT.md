---
type: Dataset Record
title: Stvarna USFS FPA-FOD kohorta za SimFire
status: current
sources:
  - resource: /data/manifests/simfire-fpa-fod-cohort-v2.json
  - resource: /reports/real-fire-data/simfire-cohort-v2-input-acquisition.json
  - resource: /reports/real-fire-data/simfire-cohort-v2-seed-selection.json
---
# Stvarna kohorta požara za SimFire

## Šta ovaj skup podataka jeste

To je skup **80 stvarnih historijskih požara** iz službene baze US Forest Servicea. Svaki
požar nam daje prijavljeni datum i približnu lokaciju. Oko te lokacije smo pripremili
stvarnu kartu goriva i stvarnu visinsku kartu terena. Te karte ulaze u SimFire.

Važna razlika: FPA-FOD **ne sadrži ispravne vatrogasne poteze** za učenje, niti nam govori
šta bi agent trebao uraditi. Agentova iskustva nastaju kada igra u SimFire-u: vidi mapu,
odluči gdje staviti vatrogasnu liniju ili uraditi no-op, a zatim dobije nagradu prema
simuliranom širenju požara. Konačna historijska površina i MTBS perimetri nisu ulaz ni
nagrada.

## Izbor i podjela požara

Koristimo trenutni FPA-FOD sedmo izdanje, šesti update, koji obuhvata zabilježene događaje
1992–2024. Iz baze smo birali slučajeve iz 10 zapadnih saveznih država: CA, OR, WA, ID, NV,
AZ, UT, CO, NM i MT. Slučaj mora imati prijavljenu površinu od barem 5.000 acres, datum,
lokaciju i MTBS identifikator za kasniju, samo vizualnu referencu. Hash rangiranje daje
ponovljiv izbor i prvo nastoji uzeti požar iz različite države.

| Godine | Namjena | Izabrano | Broj kandidata koji je prošao filter |
| --- | --- | ---: | ---: |
| 2018–2019 | Trening | 40 | 208 |
| 2023 | Provjera postavki | 20 | 56 |
| 2024 | Završni test | 20 | 109 |
| **Ukupno** |  | **80** | **373** |

Cijeli incident pripada samo jednom skupu: požar iz 2024. ne može slučajno završiti i u
treningu. Validation i test su vremenski kasniji događaji. Godine 2020–2022 su izostavljene
jer pre-event FBFM13 verzija za taj period nije bila dostupna na provjerenom javnom
ImageServeru; nećemo tiho koristiti kartu koja uključuje kasnije promjene nakon požara.

Jedan test incident, Larch Creek (`fpa-fod-401411292-larch-creek`), već je korišten za
adapter smoke i podešavanje tehničkog ponašanja simulatora. Ne koristiti ga za završni agent
benchmark. Ostaviti ga izvan eval ID liste, a preostalih 19 test događaja sačuvati za
završni poređeni rezultat.

## Koje stvarne podatke smo zaista preuzeli

- Za 2018–2019: LANDFIRE LF2016 FBFM13, prije datuma požara.
- Za 2023–2024: LANDFIRE LF2022 FBFM13, prije datuma požara.
- Za svih 80: LANDFIRE LF2020 elevation za oblik terena.
- Svaka mapa je 128×128 ćelija po 30 m, u odgovarajućoj lokalnoj UTM projekciji.
- Svih 80 gorivnih i visinskih rastera su preuzeti, poravnati i prošli provjeru oblika,
  koordinatnog sistema, granica i kodova. Hashovi su u scenario karticama i receiptu.
- Za 71 požar je prijavljena tačka pala u gorivu ćeliju. Za 9 požara je uzeta najbliža
  goriva ćelija; ona je bila najviše oko 62 m od prijavljene tačke. Pravilo koristi samo
  pre-event kartu goriva, ne perimetar ili konačnu površinu.
- Za svih 80 požara preuzeli smo dnevni weather kontekst iz gridMET-a: osam stvarnih
  meteoroloških i fire-danger vrijednosti za prijavljenu tačku i datum, uz koordinate
  uzorkovane grid ćelije, jedinice, URL i SHA-256. Mali JSON fajl po događaju nalazi se u
  `data/processed/simfire-cohort-v2-gridmet-weather/`; završni broj preuzetih/grešaka je u
  [weather receiptu](../../reports/real-fire-data/simfire-cohort-v2-gridmet-weather.json).
- Ovo su stvarni dnevni regionalni podaci, ne mjerenje svake minute baš na mjestu paljenja.
  Grid ćelija je približno 4 km; dnevni period je ponoć–ponoć po MST (UTC−7), a FPA-FOD
  discovery vrijeme nema potvrđenu vremensku zonu.
- Napravljen je zaseban, verzionisan **dnevni weather proxy** u
  `data/processed/simfire-cohort-v2-gridmet-mappings/`, po jedan za svaki slučaj. Nominalna
  verzija tretira gridMET 10 m brzinu kao približnu 20 ft referentnu brzinu, množi je sa
  NWCG faktorom zaklona 0.3, pretvara meteorološki smjer vjetra iz “odakle” u SimFire “prema
  kojem”, i računa Simard ravnotežnu vlagu iz dnevne maksimalne temperature/minimalne RH.
  Jedan dnevni uslov ostaje isti tokom najviše 12 sati simulacije. Originalni gridMET podaci
  ostaju sačuvani odvojeno, a mapiranje čuva formule, vrijednosti, hash i ograničenja.
- **To je praktičan model ulaza, ne dokaz istorijskog vremena na mjestu paljenja.** RH je
  zračna vlažnost; 100-satna model-G vlaga je ostavljena kao kontekst, ne predstavljena kao
  sitno gorivo. Dnevni maksimum temperature i minimum RH možda se nisu javili istovremeno.
  Canopy/visinski profil i prethodno vlaženje goriva nisu poznati. WAF 0.1/0.3/0.5 tehnički
  su smoke-testirani, ali nisu određeni lokalnim mjerenjima.

## Početna postavka simulacije

SimFire grid je usklađen sa 30 m raster ćelijom, odnosno približno 98.43 ft. Adapter
koristi 15 jednominutnih update-a kao maksimalno trajanje jednog zapaljenog piksela. Stock
SimFire primjer koristi 4 update-a; na 30 m mreži se u no-op probi to pokazalo prekratkim
za neke sporije ćelije. Vrijednost 15 je engineering konfiguracija i još nije fizički
kalibrisana. No-op probe služe da potvrde da slučajevi simuliraju različita trajanja i da
se horizont pravilno prekida, ne da potvrde historijsku veličinu požara.

Sirovi GeoTIFF fajlovi ostaju u ignorisanom `.local/simfire-cohort-v2/`. Git sadrži male
scenario kartice, originalne izvorne redove, screening snapshotove, hashove i zbirni
receipt, tako da kolege mogu vidjeti porijeklo bez preuzimanja velikih karata u repo.

## Ograničenja koja treba imati na umu

- To nisu svi požari SAD-a. To je namjerno izdvojena kohorta velikih požara iz deset
  zapadnih država.
- FPA-FOD lokacija nije nužno tačna GPS tačka gdje je vatra počela. Izvor navodi da tačnost
  može biti samo granica PLSS sekcije, približno jedna kvadratna milja.
- Stvarna goriva i teren daju stvarnu geografsku podlogu, ali SimFire nije time fizički
  validiran za svaki od ovih požara.
- Historijski finalni obod govori gdje je vatra na kraju završila nakon stvarnih uslova i
  reakcije vatrogasaca; ne govori šta bi se desilo bez ljudi ili šta bi naš agent uradio.
- Skup je spreman za ponovljivo učitavanje stvarnog goriva/terena i jednog eksplicitnog
  dnevnog weather proxyja. Tačan satni historijski replay nije dostupan (0/80), a proxy nije
  fizički validiran; RL politika nije trenirana.

## Ponovno pravljenje

```sh
.local/simfire-venv/bin/python scripts/build_simfire_fpa_cohort.py --offline
.local/simfire-venv/bin/python scripts/fetch_simfire_cohort_inputs.py --workers 3 --skip-weather
.local/simfire-venv/bin/python scripts/resolve_simfire_seed_cells.py
.local/simfire-venv/bin/python scripts/fetch_gridmet_cohort_weather.py --workers 4
.local/simfire-venv/bin/python scripts/summarize_gridmet_cohort.py
python3 scripts/map_gridmet_weather_to_simfire.py --wind-adjustment-factor 0.3
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy
```

Prva komanda za vremenske podatke bilježi gridMET dnevne vrijednosti za 80 historijskih
incidenata. Ako servis privremeno vrati grešku, ponoviti preuzimanje i sačuvati receipt.
Mapiranje je namjerno zaseban korak: prvo provjeriti izvorne podatke, pa eksplicitno
generisati proxy. Receipti i formule su u [mapiranju](../../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json)
i [adapteru](SIMFIRE_RL_ADAPTER.md).

**Izvori:** [USFS FPA-FOD servis i verzija](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer),
[LANDFIRE LF2022 FBFM13](https://landfire.gov/data/lf2022),
[gridMET opis](https://www.climatologylab.org/gridmet.html), [GDEX dataset](https://gdex.ucar.edu/datasets/d761426/),
[SimFire wind konfiguracija](https://mitrefireline.github.io/simfire/config.html),
[NWCG midflame wind](https://www.nwcg.gov/course/ffm/fire-behavior/firefighter-math-82-midflame-windspeed)
i [NWCG fuel moisture](https://www.nwcg.gov/publications/pms425-1/11-weather-and-fuel-moisture).
Datum pregleda: 2026-11-01. Detaljni source ID-jevi su u
[`SOURCES.md`](SOURCES.md#fpa-fod--simfire-kohorta-i-rl-okruženje).
