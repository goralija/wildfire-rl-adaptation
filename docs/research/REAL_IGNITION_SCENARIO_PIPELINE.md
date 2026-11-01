---
type: Data Pipeline Design
title: Real fire records into SimFire scenarios
status: current-provisional
sources:
  - resource: /data/manifests/simfire-scenario.schema.json
  - resource: /data/manifests/simfire-fpa-fod-cohort-v2.json
  - resource: /docs/research/SOURCES.md
  - resource: /docs/specs/DECISION_RECORDS.md
---
# Od stvarnog zapisa požara do SimFire scenarija

## Jednostavno objašnjenje

Historijska baza nam kaže **gdje i kada je požar prijavljen**. Za taj približni položaj
uzeli smo stvarnu kartu goriva i visine tla iz LANDFIRE-a. Te slojeve pretvaramo u isti
kvadratni raster koji SimFire može učitati. Simulator zatim pravi nove pokušaje širenja i
agentove poteze.

Historijski zapis ne kaže šta bi se desilo da je agent drugačije djelovao. Zbog toga
koristimo historijske uslove kao početnu podlogu, a ne završnu površinu požara kao nagradu.
Završni obod može kasnije biti nacrtan odvojeno radi poređenja.

## Šta izvorni podaci daju, a šta simulator treba

| Historijski zapis (Y) | Ulaz koji treba SimFire (X) | Trenutni status |
| --- | --- | --- |
| ID, datum i približno mjesto incidenta | scenario JSON, početni red/kolona i izvorna nesigurnost | 80 slučajeva snimljeno; 71 prijavljena ćelija je goriva, za 9 je proxy ćelija do oko 62 m |
| LANDFIRE FBFM13 karta | poravnata matrica kodova goriva, koju SimFire zna pretvoriti | preuzeto i provjereno za 80/80 |
| LANDFIRE elevation | visinska matrica na istom projektovanom gridu | preuzeto i provjereno za 80/80 |
| gridMET dnevne vremenske procjene | originalni dnevni kontekst + zaseban SimFire proxy po slučaju | izvorni podaci i proxy checksum-QC 80/80; satni replay 0/80 |
| Konačna površina/MTBS obod, ako postoji | odvojen vizualni sloj | referenca samo; ne koristi se kao nagrada ili agentov ulaz |

Zajednički mali JSON format je [`simfire-scenario.schema.json`](../../data/manifests/simfire-scenario.schema.json).
JSON čuva porijeklo i putanje; GeoTIFF rasteri ostaju odvojeni jer u njima žive hiljade
prostorskih vrijednosti po slučaju. Sirovi rasteri su u Git-ignorisanom `.local/`, a
manifeste, hashove i male receipte može pregledati cijeli tim.

## Kohorta koja se sada koristi

Izabrano je 80 stvarnih incidenata iz US Forest Service FPA-FOD-a. Filter traži barem
5.000 acres, prijavljeni datum/lokaciju, MTBS ID za kasniji vizualni kontekst i jednu od
deset zapadnih država. Izabran je ponovljiv uzorak od 20 slučajeva po godini:

| Godina | Uloga | Požari |
| --- | --- | ---: |
| 2018–2019 | train | 40 |
| 2023 | validation | 20 |
| 2024 | test | 20 |

Požar kao cjelina postoji samo u jednom splitu. Zato susjedni dani ili kvadrati istog
požara ne mogu procuriti iz treninga u test. Godine 2020–2022 su preskočene jer nismo
potvrdili odgovarajuću prije-požarnu FBFM13 verziju na javnom LANDFIRE ImageServeru.
Filter je našao 373 kandidata ukupno, ali 80 je izabrano za prvi upravljiv i vremenski
odvojen skup. Potpuna selekcija je u
[`simfire-fpa-fod-cohort-v2.json`](../../data/manifests/simfire-fpa-fod-cohort-v2.json).

## Kako su sirovi podaci pretvoreni

1. **Zamrznuti izvorni slučaj.** Za svaki izabrani `FOD_ID` sačuvan je mali izvorni zapis,
   URL, verzija izvora i SHA-256. Tačka je označena kao incidentna referenca; ne tvrdi se
   da je to tačan GPS položaj paljenja.
2. **Napraviti isti oblik mape.** Oko prijavljene tačke izrezan je prozor od 128×128 ćelija,
   tačno 30 m po ćeliji, u lokalnoj UTM projekciji. Kvadrat ne zavisi od kasnijeg perimetra.
3. **Dodati gorivo i teren.** Za požare 2018–2019 koristi se pre-event LF2016 FBFM13; za
   2023–2024 pre-event LF2022 FBFM13. Svima je dodan LF2020 elevation. Gorivo je izabrano
   prije datuma događaja, ali nije terenski inventar tačno na dan događaja.
4. **Odrediti simulator start.** Ako je prijavljena ćelija goriva, koristi se ona. Ako nije,
   bira se najbliža goriva ćelija u radijusu do polovine PLSS sekcije (804.672 m). U našem
   skupu svih devet zamjena su bile unutar oko 62 m. To je reproducibilna aproksimacija,
   ne dokaz tačnog mjesta paljenja. Pravilo ne gleda obod požara.
5. **Provjeriti svaki raster.** Skripta provjerava CRS, 30 m bounds, 128×128 oblik, no-data,
   prepoznate kodove goriva i SHA-256. U svim 80 slučajevima gorivo i teren su prošli.
6. **Dodati dnevni weather i jasno ga prevesti u simulator.** gridMET dnevni kontekst je
   preuzet i provjeren za 80/80 slučajeva. Zasebna mapping skripta pravi ponovljiv proxy:
   vjetar 10 m→približan 20 ft referentni vjetar→WAF 0.3; `wind_from`→SimFire smjer prema;
   dnevni max T/min RH→Simard EMC procjena→SimFire moisture fraction. Pretpostavke i
   alternativni WAF 0.1/0.5 se bilježe. Ovo nije satni replay ni fizički izmjerena vlaga;
   vidjeti [mapping receipt](../../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json).
7. **Pokrenuti uporedive politike.** Nakon što se X kompletira, base PPO, fine-tuned
   kopija, no-op i jednostavna heuristika dobijaju iste mape, vremenske uslove, trajanje,
   seedove i budžet. Fine-tuning koristi samo TRAIN požare; validation podešava; test se
   čuva za završnu provjeru. Jedan test incident, Larch Creek, već je otvoren za tehnički
   smoke i treba ga isključiti; sačuvati preostalih 19 za završni benchmark.

## Koliko je trenutno spremno

Za svih 80 incidenata postoje stvarni fuel/terrain rasteri, dnevni gridMET context i
zaseban po-slučaju SimFire weather proxy. Mapping JSON-i su povezani sa manifestima
checksumovima. Proxy-mode adapter se tehnički pokrenuo kroz jedan TRAIN, jedan validation
i jedan test slučaj pri WAF 0.1, 0.3 i 0.5; učitavanjem svakog split-a provjereni su svi
njegovi mapping hashovi. `learn()` nije pozvan.

Ovo je **izvršivo simulacijsko okruženje sa stvarnim geografskim podacima i označenim
pretpostavkama**, a ne historijski fire replay ili fizički potvrđen model. gridMET je dnevni
oko 4 km; ne znamo tačan sat paljenja/time zone, canopy profil ni stvarnu vlagu sitnog goriva.
No-op i test protokol još treba zamrznuti prije rezultatskog poređenja.

SimFire stock trajanje jedne zapaljene ćelije bilo je 4 update-a. U 30 m mreži adapter sada
koristi 15 jednominutnih update-a, jer se na Owyhee primjeru stock podešavanje gasilo prije
sporijeg susjednog širenja. To je tehnički izbor, ne kalibracija požarne fizike. No-op
receipti i reprodukcijska komanda su u [environment kartici](SIMFIRE_ENVIRONMENT.md).

## Šta rezultat može tvrditi

Možemo reći: “Na ovim SimFire scenarijima, sastavljenim od historijskih lokacija i
provjerenih mapa goriva/terena, politika A je imala manje simuliranih izgorjelih ćelija od
politike B, pod istim uslovima i budžetom.”

Ne možemo reći: “Agent bi spasio određeni broj hektara u tom stvarnom požaru.” Historijski
obod uključuje stvarno vrijeme, gašenje, izvještavanje i neizvjesnosti koje SimFire ne
reprodukuje.

## Reprodukcija

```sh
.local/simfire-venv/bin/python scripts/build_simfire_fpa_cohort.py --offline
.local/simfire-venv/bin/python scripts/fetch_simfire_cohort_inputs.py --workers 3 --skip-weather
.local/simfire-venv/bin/python scripts/resolve_simfire_seed_cells.py
.local/simfire-venv/bin/python scripts/fetch_gridmet_cohort_weather.py --workers 4
.local/simfire-venv/bin/python scripts/summarize_gridmet_cohort.py
python3 scripts/map_gridmet_weather_to_simfire.py --wind-adjustment-factor 0.3
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy
```

`--skip-weather` služi da se odvojeno pribave gorivo i teren; gridMET se dohvaća zasebnom
skriptom radi per-case receipta i nastavka nakon privremenog neuspjeha. Mapping je dodatni
izričit korak; proxy smoke traži `--weather-mode gridmet_daily_proxy`.

**Dokazi:** [kohorta](SIMFIRE_FPA_COHORT.md), [adapter](SIMFIRE_RL_ADAPTER.md),
[input receipt](../../reports/real-fire-data/simfire-cohort-v2-input-acquisition.json),
[ADR-044 i ADR-045](../specs/DECISION_RECORDS.md), [EXP-034 i EXP-035](EXPERIMENT_LOG.md).
