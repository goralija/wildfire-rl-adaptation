---
type: Environment Record
title: SimFire/FEDS runner environment and data cache
status: current
sources:
  - resource: /requirements/simfire-macos-arm64-py39.freeze.txt
  - resource: /scripts/fetch_feds_archive.py
  - resource: /scripts/build_feds_simfire_inputs.py
  - resource: /scripts/sample_gridmet_episode_weather.py
  - resource: https://github.com/mitrefireline/simfire
  - resource: https://zenodo.org/records/22921773
  - resource: https://www.climatologylab.org/gridmet.html
  - resource: https://landfire.gov/data
---
# SimFire/FEDS runner environment

## Provjereni runtime

Projektni CLI koristi Python 3.11 ili noviji. Pinovani upstream SimFire 2.0.1 traži
Python 3.9, pa se izvršava u odvojenom izolovanom venv-u. U ovom worktreeu je
postavljen Python 3.9.25 u `.local/simfire-venv`; `uv pip check` je provjerio svih 85
paketa bez konflikta. Verzije uključuju NumPy 1.26.4, Rasterio 1.4.3, Fiona 1.10.1,
GeoPandas 0.14.4, Shapely 2.0.7, Gymnasium 1.1.1, Stable-Baselines3 2.7.1,
PyTorch 2.3.1 i netCDF4 1.7.2. SimFire je pinovan na commit
`04905b19fe8c10dc08d64faddd00303e0561bb66`.

Tačan macOS ARM64 freeze je u
[`requirements/simfire-macos-arm64-py39.freeze.txt`](../../requirements/simfire-macos-arm64-py39.freeze.txt).
Venv, uv cache, FEDS/NetCDF arhive, LANDFIRE rasteri, case maske i no-op izlazi ostaju
u ignorisanom `.local/` i ne idu u Git.

Na ovoj mašini je originalni Python interpreter u `.local/uv-python` ostao neupotrebljiv
i njegovi raniji procesi su zaglavljeni u macOS I/O stanju. Da se sačuvaju instalirani
paketi, `.local/simfire-venv/bin/python` sada poziva provjereni Python 3.9 interpreter iz
susjednog `cfsds-train-qc` worktreea, dok `sys.prefix` i 85 paketnih instalacija ostaju
u ovom worktreeu. `uv pip check` nad ovim venv-om prolazi. Originalna Python veza je
sačuvana kao `.local/simfire-venv/bin/python.stalled-target-runtime`. Ovo je lokalna
veza na zajednički osnovni interpreter; pri premještanju/uklanjanju susjednog worktreea
treba je zamijeniti nezavisnim Python runtimeom.

Ponovno postavljanje u čistom klonu:

```sh
UV_CACHE_DIR=.local/uv-cache UV_PYTHON_INSTALL_DIR=.local/uv-python uv python install 3.9.25
UV_CACHE_DIR=.local/uv-cache UV_PYTHON_INSTALL_DIR=.local/uv-python uv venv --python 3.9.25 .local/simfire-venv
UV_CACHE_DIR=.local/uv-cache uv pip install --python .local/simfire-venv/bin/python -r requirements/simfire-macos-arm64-py39.freeze.txt
UV_CACHE_DIR=.local/uv-cache uv pip check --python .local/simfire-venv/bin/python
```

Headless komande postavljaju `MPLCONFIGDIR`, `XDG_CACHE_HOME` i
`SDL_VIDEODRIVER=dummy` unutar worktreea. SimFireova konfiguracija je verzionisana u
[`configs/simfire_feds_base.yml`](../../configs/simfire_feds_base.yml). Python 3.9 je
posebno potreban zbog upstream paketa; moderni projektni runtime ostaje odvojen.

## FEDS crosswalk, front i prostorna mreža

FEDS-CONUS v1 su poludnevne 375 m satelitske procjene. `lf_perimeter` je opaženi
požarom zahvaćeni prostor, a `lf_fireline` je FEDS procjena aktivnog dijela fronta;
to nije ručno izgrađena USFS suppression linija. Za train/validation godine su preuzeti
oba sloja 2018, 2019. i 2023. MD5 svakog fajla odgovara Zenodo zapisu; sirove arhive su
u `.local/feds-conus/`.

Tačan početni `fireID + t` front postoji za **119/119** epizoda (99 train, 20
validation). Svaki front dodiruje odgovarajući vremenski obod, a cijela FEDS linija je
unutar jedne 375 m izvorne ćelije od oboda; direktno preklapanje s geometrijskom
granicom je varijabilno i zato se ne traži. Rezultat je geometrijska pokrivenost, ne
provjera spread modela. Pogledaj [active-front audit](../../reports/real-fire-data/feds-active-front-coverage-v1.json).

Simulator koristi dogovorenu mrežu **256×256 ćelija po 180 m** (46.08 km po stranici),
centariranu na centroidu početnog FEDS oboda u lokalnom UTM CRS-u. `--preflight` je
provjerio da cijeli početni obod i front stanu u mapu za svih 119 slučajeva: 99/99
train i 20/20 validation. Ništa se ne reže prešutno. Perimeter poligon postaje već
opožareni scar; vremenski usaglašena FEDS linija postaje više aktivnih ćelija. Maska
koristi `all_touched=true`; front ćelije imaju prednost ako se preklope sa scarom.
Izvorna 375 m rezolucija FEDS nije predstavljena kao 180 m opažanje.

Provjerljivi artefakti su
[mrežni preflight](../../reports/real-fire-data/feds-simfire-grid-preflight-v1.json),
[mask/grid helper](../../src/wildfire_rl/feds_simfire_inputs.py),
[case builder](../../scripts/build_feds_simfire_inputs.py) i
[multi-cell state tests](../../tests/test_feds_simfire_inputs.py).

## LANDFIRE inputi

Case builder povlači male prostorno usaglašene ImageServer izvatke:

- LF2016 FBFM13 za 2018/2019, `RSP_Majority` jer su fuel kodovi kategorije.
- LF2022 FBFM13 za 2023, istim većinskim resamplingom.
- LF2020 Elevation, `RSP_BilinearInterpolation` za kontinuiranu visinu.

Sada svih **99/99 train** epizoda ima preuzete i validirane LANDFIRE fuel/elevation
GeoTIFF-ove i početne FEDS maske na dogovorenoj mreži. Svaki od 198 rastera je iste
256×256 dimenzije, CRS-a i granica te prolazi NoData i kategorijski fuel-code provjere.
Kompletna receipt lista i SHA-256 su u
[train input coverage reportu](../../reports/real-fire-data/feds-simfire-input-train-coverage-v1.json);
sirovi fajlovi ostaju u `.local/`. Validation rasteri još nisu preuzeti: parametri se
prvo biraju na TRAIN. Izabrani LANDFIRE proizvodi su pre-event kandidat podaci, ne
terenski izmjerena vegetacija na dan požara. Jedan-case receipt i demonstracijski smoke
ostaju [ovdje](../../reports/real-fire-data/feds-simfire-input-smoke-v1.json).

Za jedan-case preflight/fetch ponovi:

```sh
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/build_feds_simfire_inputs.py --preflight
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/build_feds_simfire_inputs.py --fetch-split train
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/build_feds_simfire_inputs.py --scenario-id fpa-fod-400300427-plateau
```

## gridMET i granica informacije

Službene godišnje NetCDF arhive za `th`, `vs` i `fm100` preuzete su samo za dozvoljene
2018, 2019. i 2023. godine. Svih devet arhiva imaju SHA-256 u
[weather coverage reportu](../../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json).
Skripta ih je validirala kroz dnevnu dimenziju, gridMET oznaku varijable, zadnji vremenski
uzorak, jedinice i checksum.

Za svih 119 epizoda uzimaju se sirovi gridMET uzorci u najbližoj 4 km ćeliji centroidu
početnog FEDS poligona, za sredinu svakog od četiri 12h segmenta. Pošto FEDS polje
`t` nema vremensku zonu, skripta bilježi pretpostavku da je UTC; gridMET datumi se
mapiraju preko fiksne MST granice iz metadata. Rezultat ima 396 train i 80 validation
segmenta. Svi izabrani zapisi imaju vrijednosti; uzorci se kreću od 1.1 do 11.6 m/s za
`vs`, od 21° do 347° za `th` i od 3.5% do 15.2% za `fm100`.

Kompletni case-level uzorci ostaju ignorisani u
`.local/gridmet/feds-episode-weather-v1.json`; ponavljanje:

```sh
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/fetch_gridmet_archives.py --year 2018 2019 2023 --variable th vs fm100
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/sample_gridmet_episode_weather.py
```

`th` je u NetCDF-u označen kao `wind_from_direction`; SimFire koristi smjer vjetra
prema kojem vatra gura. Helper zato ima eksplicitnu 180° rotaciju, `vs` m/s pretvara u
ft/min uz zajednički wind-adjustment faktor, a `fm100` procenat pretvara u razlomak.
Međutim, **wind-adjustment faktor još nije izabran**; raw vrijednosti se za sada ne
predstavljaju kao validirani SimFire weather. Buduće vremenske vrijednosti ostaju
skriveni istorijski forcing u simulatoru, ne agentovo znanje ili prognoza.

gridMET je dnevni proizvod približno 4 km; `fm100` je NFDRS 100-hour fuel moisture,
ne direktno SimFireova ili FBFM13 fina gorivna vlaga. Zato je to kandidat proxy. Izbor
faktora i drugi zajednički parametri moraju se kalibrisati samo na trainu i zaključati
prije validation provjere. 2024 test ni njegovi zapisi nisu učitani.

## Šta smoke dokazuje i ne dokazuje

`scripts/run_feds_simfire_smoke.py` je pokrenuo one-hour no-op na Plateau koristeći
stvarne FEDS scar/front i LANDFIRE fuel/terrain, ali demonstracijski vjetar 7 mph,
90° i vlagu 3%. Uz 90 update-a trajanja aktivne ćelije smoke je imao 27 kumulativnih
ćelija (87.48 ha), fire i dalje aktivan nakon jednog sata. Vrijednost 90 je 15-minutni
SimFire demo default skaliran šest puta za šest puta širu ćeliju 180m/30m; nije
odabrana prema završnom obodu požara. Bez skaliranja, 15 update-a nije dalo novi spread
u ovom grubom demo slučaju.

Ovaj smoke potvrđuje samo da SimFire v2 prihvata multi-cell stanje, izvatke i projektne
metapodatke. Ne potvrđuje da je rast blizak opaženom požaru.

Dodani su [historijski no-op runner](../../scripts/run_feds_noop_episode.py),
[metric helpers](../../src/wildfire_rl/feds_spread_metrics.py) i
[timebase tests](../../tests/test_simfire_timebase.py). Runner koristi četiri 12h
gridMET segmenata; svaku buduću FEDS granicu učitava nakon simulacije samo za mjerenje.
Jedan Plateau TRAIN pilot pokazuje veliku osjetljivost na wind-adjustment faktor:
0.20–0.60 završi na 61.56 ha (samo 3 nova rastera, IoU 0.64 prema 71.28 ha opaženih),
dok 0.65 daje 1,244 ha, a 0.75 daje 2,262 ha u 12h; visoki faktori kasnije dodiruju
rub mape. Svi su to nesabrani kalibracijski pokušaji jednog događaja; nijedan WAF nije
izabran ili zaključan. Detalji i hashes su u
[no-op pilot izvještaju](../../reports/real-fire-data/feds-simfire-noop-pilot-v1.json).

Testni 5-min unutrašnji korak čuva 90-min nominalni aktivni vijek ćelije kao 18 update-a;
WAF-1.0 pilot na tom koraku trajao je oko 40 s za 48h. Ovo je kandidat numeričke
postavke, nije konačna kalibracija. Agentove odluke ostaju na 12h. Train/validation
no-op gate sa persistence i unaprijed definisanom elipsom nije prošao niti je završen.

## TRAIN-only PPO putanja

Na korisnikov zahtjev sada postoji tehnička MaskablePPO putanja nad FEDS/LANDFIRE
epizodama, bez čekanja na naučni no-op gate. [`FedsSimFireEnv`](../../src/wildfire_rl/feds_simfire_env.py)
dozvoljava samo manifest TRAIN slučajeve (99), drži isti 48h horizont i četiri 12h
odluke, a budžet se nasumično uzorkuje iz CLI skupa. Akcije su uvijek legalni no-op ili
jedan od osam smjerova koji polaže najviše sedam `FIRELINE` ćelija ispred trenutnog
centroida fronta i troši jednu budžetsku jedinicu. Ovo je diskretni prototip politike,
ne provjeren model operativne gradnje linije.

Observation sadrži samo sažeto trenutno stanje (16×16 agregati burn/front/linija/gorivo),
budžet, vrijeme epizode i **trenutni** weather segment. Budući gridMET segmenti ostaju
skriveni policy-ju. Reward je negativan broj dodatnih kumulativno opožarenih ćelija
skaliran sa 100; FEDS budući obodi se ne koriste ni u observation ni u reward. Kumulativni
scar ostaje zabilježen i kad SimFire na ćeliju postavi liniju. Pražnjenje budžeta ili
gašenje vatre ne prekida epizodu: sva četiri 12h koraka se završe, uz no-op kada nema
akcije. PPO je from-scratch; prethodni Firehose checkpointi se ne učitavaju.

Kratki CPU smoke (64 odluke, približno 16 epizoda) može se pokrenuti ovako; odaberi
novi izlazni direktorij pod `.local/`:

```sh
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache SDL_VIDEODRIVER=dummy \
  .local/simfire-venv/bin/python scripts/train_feds_simfire.py \
  --steps 64 --out .local/feds-ppo-experiments/NEW-ID \
  --wind-adjustment-factor 0.605 --budgets 0,2,4 --seed 7
```

WAF 0.605 u komandi je samo eksplicitan **provisional** kandidat radi reproducibilnog
smokea, nije izabran parametar. Veći `--steps` produžava trening; smoke težine i manifest
ostaju u ignorisanom `.local/`. Svaki receipt izričito označava da nije fizička validacija,
benchmark ni dokaz RL prednosti. Poslije dodavanja trenažnog adaptera, Plateau no-op
recheck sa WAF .605 ponovio je 19 kumulativnih ćelija/61.56 ha, 4/4 poređenja bez rubnog
udara; to i dalje nije cohort-level kalibracija.

Odvojeni Plateau TRAIN action smoke s budžetom 1 potrošio je tačno jednu jedinicu na
legalnu fireline akciju, a zatim završio preostala tri 12h koraka. To potvrđuje samo
API/budget plumbing; ne potvrđuje učinkovitost ili realističnost linije.

## Sljedeće provjere

1. TRAIN fuel/terrain je pribavljen za 99/99 slučajeva. Kalibrisati mali zajednički
   parametarski skup preko TRAIN uz istu grid i vrijeme; bez podešavanja po požaru.
2. Dodati persistence i unaprijed definisanu zajedničku elipsnu referencu, zatim izmjeriti
   48h no-op na TRAIN i VALIDATION: površinu, IoU/area error i map-edge dodire svakih 12h.
   Validation mape preuzeti tek kad su TRAIN postavke zaključane.
3. Tehničko PPO treniranje je dostupno, ali benchmark ili policy-benefit poređenje
   ostaje blokirano dok no-op ne bude upoređen sa referencama na TRAIN kohorti i dok se
   zajednički WAF/timebase ne zaključa. Trenutna sektor-akcija je samo prototype.
4. Za naučno poređenje unaprijed definisati operativnu gradnju linije i zatim dati svim
   politikama iste epizode, budžete, horizonte, observacije i seedove.

## Primarni izvori (provjereni 2026-11-03)

- FEDS-CONUS v1, objava/licenca/checksumi: [Zenodo](https://zenodo.org/records/22921773),
  objavljeno 2026-10-02; opis toka [Wildfire Tracking Lab](https://www.ess.uci.edu/~uci-nasa-firetracking/).
- SimFire kod i pin: [MITRE SimFire GitHub](https://github.com/mitrefireline/simfire),
  commit `04905b19fe8c10dc08d64faddd00303e0561bb66`.
- gridMET varijable i rezolucija: [Climatology Lab gridMET](https://www.climatologylab.org/gridmet.html)
  i [PyGridMET dokumentacija/tabela jedinica](https://github.com/hyriver/pygridmet).
- LANDFIRE podaci i ImageServer proizvodi: [LANDFIRE data](https://landfire.gov/data)
  i [Esri ImageServer exportImage opcije](https://developers.arcgis.com/rest/services-reference/enterprise/export-image/).
- FPA-FOD izvor i licenca: [USFS RDS-2013-0009.7](https://doi.org/10.2737/RDS-2013-0009.7).
