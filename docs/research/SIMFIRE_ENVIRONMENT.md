---
type: Environment Record
title: SimFire, real cohort and local RL setup — 2026-11-01
sources:
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/research/EXPERIMENT_LOG.md
  - resource: /docs/research/SOURCES.md
  - resource: /reports/real-fire-data/simfire-cohort-v2-input-acquisition.json
---
# SimFire, stvarni podaci i RL okruženje

## Verzije i lokacije

MITRE SimFire 2.0.1 je pinovan u `external/simfire` na commitu
`04905b19fe8c10dc08d64faddd00303e0561bb66`. Lokalni Python 3.9.25 environment je
`.local/simfire-venv/`; sistemski Python nije mijenjan. Osnovne verzije SimFire paketa su u
[`simfire-macos-arm64-py39.freeze.txt`](../../requirements/simfire-macos-arm64-py39.freeze.txt),
a dodatak za RL u
[`simfire-rl-macos-arm64-py39.freeze.txt`](../../requirements/simfire-rl-macos-arm64-py39.freeze.txt).
Instalirano je PyTorch 2.3.1, Gymnasium 1.1.1, Stable-Baselines3 2.7.1 i sb3-contrib 2.7.1.
To je lokalni macOS ARM64 setup, ne univerzalni recept za Linux/Windows.

Sirovi kod SimFirea, environment i veliki rasteri su Git-ignorirani. Kolega može iz
requirements fajlova ponoviti Python dio, ali LANDFIRE/SimFire inpute treba pribaviti po
sljedećim koracima iz [NEXT_SESSION](../NEXT_SESSION.md).

## Stvarna kohorta i karte

Aktivna kohorta `fpa-fod-western-us-2018-2024-v2` sadrži 80 stvarnih USFS FPA-FOD požara:
40 train, 20 validation i 20 test. Svaki slučaj ima FPA-FOD izvorni zapis, 128×128 grid,
pre-event FBFM13 gorivo i LF2020 terrain. Gorivo/terrain su preuzeti i raster provjere
prošle za 80/80. Izvorni podaci, pravila i ograničenja su u
[`SIMFIRE_FPA_COHORT.md`](SIMFIRE_FPA_COHORT.md).

Reprodukovati rastere ako lokalni `.local/` nedostaje, pa preuzeti originalni weather,
provjeriti ga i zasebno napraviti proxy:

```sh
.local/simfire-venv/bin/python scripts/build_simfire_fpa_cohort.py --offline
.local/simfire-venv/bin/python scripts/fetch_simfire_cohort_inputs.py --workers 3 --skip-weather
.local/simfire-venv/bin/python scripts/resolve_simfire_seed_cells.py
.local/simfire-venv/bin/python scripts/fetch_gridmet_cohort_weather.py --workers 4
.local/simfire-venv/bin/python scripts/summarize_gridmet_cohort.py
python3 scripts/map_gridmet_weather_to_simfire.py --wind-adjustment-factor 0.3
```

Dnevni kontekst i proxy postoje za 80/80. Tačan satni replay je 0/80. Proxy pretpostavlja
da je 10 m vjetar približan 20 ft vjetar, primjenjuje faktor zaklona 0.3, obrće smjer
vjetra i procjenjuje vlagu preko Simard EMC. Originalni podaci ostaju sačuvani zasebno.
Default smoke koristi demo atmosferu; proxy se aktivira samo sa
`--weather-mode gridmet_daily_proxy`.

Adapter takođe mijenja SimFire `max_fire_duration` sa stock 4 na **15 update koraka**.
SimFire definiše to kao broj frame-ova u kojima jedna ćelija može ostati zapaljena; naš
update je jedna minuta. Sa stock 4, Owyhee požar u no-op probi je prestao nakon 8 min i
dvije ćelije. Razlog je geometrijska skala: jedna ćelija predstavlja oko 98.43 ft (30 m),
a sporija susjedna ćelija nije skupila dovoljno simuliranog širenja u četiri koraka.
Petnaest koraka je inženjerska postavka da model ima vremena preći ćeliju pri sporijem ROS-u;
nije terenski izmjerena niti naučno kalibrisana vrijednost. [SimFire dokumentuje trajanje
kao broj frame-ova](https://mitrefireline.github.io/simfire/config.html).

## Adapter smoke

Osnovni demo smoke i historical-proxy smoke:

```sh
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy --wind-adjustment-factor 0.1 --out reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke-waf-01
.local/simfire-venv/bin/python scripts/smoke_simfire_gym_env.py --weather-mode gridmet_daily_proxy --wind-adjustment-factor 0.5 --out reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke-waf-05
```

Smoke pokreće po jedan slučaj iz svakog splita, postavi jednu linijsku tačku, provjeri
no-op nakon potrošenog budžeta i napravi MaskablePPO legalnu probnu akciju. Mapirani fajlovi
za cijeli izabrani split provjere se pri učitavanju environmenta. WAF 0.1, 0.3 i 0.5 smoke
prolaze tehnički; to ne dokazuje da je vjetar fizički dobro pretvoren. `learn()` nije pozvan,
nema treniranih težina.

Receipt demo-smoke je u
[`simfire-cohort-v2-gym-smoke`](../../reports/real-fire-data/simfire-cohort-v2-gym-smoke/);
receipt proxy-smoke je u
[`simfire-cohort-v2-gridmet-weather-smoke`](../../reports/real-fire-data/simfire-cohort-v2-gridmet-weather-smoke/).
Mala mapa svih 80 referentnih lokacija i raspodjele raw weather polja je u
[`gridMET overview`](../../reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png).
Za svaki slučaj, SimFire `pixel_scale` prati 30 m po ćeliji (98.43 ft).

No-op horizon probe koji **ne postavlja liniju i ne pokreće agenta** može se ponoviti ovako:

```sh
.local/simfire-venv/bin/python scripts/smoke_simfire_noop_horizon.py --splits train validation
.local/simfire-venv/bin/python scripts/smoke_simfire_noop_horizon.py --splits test --out reports/real-fire-data/simfire-cohort-v2-gridmet-noop-test-exposed
```

Pri WAF 0.3 i 15-minutnom trajanju ćelije, Owyhee no-op epizoda je trajala 675 min i
zahvatila 8.792 ćelije; Hayden je dosegao 720-minutni horizont i 1.059 ćelija; Larch Creek
je stao nakon 84 min i 24 ćelije. Različiti ishodi pokazuju da sada nema jednog kratkog
prekida za sva tri primjera; to i dalje nisu historijski predviđene površine. Sačuvani su
[receipti i mape](../../reports/real-fire-data/).

## Dodatni Dixie razvojni primjer

Raniji mali Dixie Fire primjer ostaje kao razvojna provjera lanfa i vizuala. Ima stvarni
LF2016 FBFM13 i LF2020 elevation raster, te jedan 24-satni ERA5 kontekstualni odgovor za
2021-07-13. Nije dio 80-člane kohorte i njegov weather ne popunjava kohortu. ERA5 je na
približno 25 km i po satu; SimFire traži vjetar uz plamen i vlagu goriva, dok dostupni
weather daje 10 m vjetar i vlažnost vazduha. Ta vrijednosti se još ne prevode u SimFire.

Reproducibilni Dixie smoke:

```sh
.local/simfire-venv/bin/python scripts/fetch_simfire_real_inputs.py
.local/simfire-venv/bin/python scripts/run_simfire_real_input_smoke.py --steps 30
```

Karte i receipt su u
[`simfire-dixie-real-input-smoke`](../../reports/real-fire-data/simfire-dixie-real-input-smoke/).

## Trenutna spremnost i granice

**Tehnički dokazano:** pinned SimFire radi na stvarnim fuel/terrain rasterima; Gymnasium
adapter podržava train/validation/test; svih 80 weather proxy fajlova provjerava se hashom;
MaskablePPO inference bira legalnu akciju; po jedan slučaj iz svakog splita prolazi duži
smoke; no-op epizode iz sva tri splita imaju sačuvane rezultate. Lokalni Python venv je
verzionisan i dokumentovan. Nije pozvan `learn()`.

**Nije dokazano:** da su proxy vjetar i vlaga jednaki stvarnim uslovima; da prijavljena tačka
jeste GPS mjesto paljenja; da SimFire fizički reprodukuje ove požare; da PPO pobjeđuje
kontrolne politike. Nema treniranja ili policy rezultata.

Za mjerodavno poređenje još treba zaključati no-op i heurističke kontrole, trening/eval
seedove, metrike, izbor checkpointa i zatvorene test ID-jeve. Zatim pripremiti reproducibilan
preflight i runner. Trening nije pokrenut u ovoj pripremnoj fazi i zahtijeva zasebnu naredbu.
Čak i kasniji dobar rezultat odnosit će se na SimFire simulacije sa označenim daily proxyjem,
ne na dokaz spašenih hektara u stvarnim požarima.

**Test skup:** incident `fpa-fod-401411292-larch-creek` (Larch Creek, 2024) je korišten u
smoke i no-op dijagnostici. Ne koristiti ga u završnom benchmarku. Preostalih 19 test
incidenta ostaju za kasniju završnu procjenu; ovaj izuzetak treba unijeti u benchmark
manifest prije bilo kakvog poređenja.
