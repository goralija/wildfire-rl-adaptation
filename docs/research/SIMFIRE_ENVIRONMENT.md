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
  - resource: https://github.com/Earth-Information-System/fireatlas/tree/1.4.1
  - resource: https://github.com/Earth-Information-System/fireatlas/issues/230
  - resource: https://doi.org/10.1038/s41597-022-01343-0
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

Za svih 118 epizoda (nakon uklanjanja duplikata, ADR-030 §6) uzimaju se sirovi gridMET
uzorci u najbližoj 4 km ćeliji centroidu početnog FEDS poligona, za sredinu svakog od četiri
12h segmenta, plus `pre_start` dan za observation. FEDS `t` je oznaka VIIRS prolaza u
lokalnom sunčevom vremenu, ne UTC (TASK-027, odjeljak ispod): segmenti počinju u 01:30 (AM)
ili 13:30 (PM) lokalnog sunčevog vremena u tački uzorka, preračunato u UTC preko
dužina/15, a gridMET datumi se mapiraju preko fiksne MST granice iz metadata. Rezultat ima
392 train i 80 validation segmenta. Svi izabrani zapisi imaju vrijednosti; uzorci (sa
`pre_start`) se kreću od 1.1 do 12.1 m/s za `vs`, od 5° do 359° za `th` i od 3.1% do 17.5%
za `fm100`. Svaki slučaj ima svoju ćeliju (118 različitih, najviše 2.80 km); hash fajla,
hash manifesta i poređenje sa starim, neispravnim fajlom su u
[coverage reportu](../../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json).

Kompletni case-level uzorci ostaju ignorisani u
`.local/gridmet/feds-episode-weather-v1.json`; ponavljanje:

```sh
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/fetch_gridmet_archives.py --year 2018 2019 2023 --variable th vs fm100
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache .local/simfire-venv/bin/python scripts/sample_gridmet_episode_weather.py [--previous-weather <stari fajl>]
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

## FEDS `t` nije UTC trenutak (TASK-027, provjereno 2026-11-09)

**Činjenice iz izvora.**
- Zenodo FEDS-CONUS zapis ([22921773](https://zenodo.org/records/22921773)) navodi da je
  arhiva napravljena s FEDS/fireatlas v1.4.1 iz SNPP VIIRS detekcija, u 12-satnim koracima;
  polje `t` ni vremensku zonu ne definiše.
- U fireatlas v1.4.1 detekcija dobija AM ili PM po **lokalnom sunčevom satu** izračunatom iz
  geografske dužine (UTC vrijeme akvizicije + `Lon/15` h; PM ako je sat između 7 i 17,
  inače AM): [`FireIO.AFP_setampm`](https://github.com/Earth-Information-System/fireatlas/blob/1.4.1/fireatlas/FireIO.py#L541-L562).
  Datum je datum akvizicije u UTC ([`preprocess.py`](https://github.com/Earth-Information-System/fireatlas/blob/1.4.1/fireatlas/preprocess.py#L251-L280)).
- Oznaka `(godina, mjesec, dan, 'AM'|'PM')` pretvara se u sat 0 ili 12
  ([`FireTime.t2dt`](https://github.com/Earth-Information-System/fireatlas/blob/1.4.1/fireatlas/FireTime.py#L123-L140)),
  a u slojeve se upisuje kao string bez zone
  ([`postprocess.py` L186](https://github.com/Earth-Information-System/fireatlas/blob/1.4.1/fireatlas/postprocess.py#L186)).
- Autor koda u [issue #230](https://github.com/Earth-Information-System/fireatlas/issues/230)
  piše da `t` bilježi "UTC date and Local time (converted to 0:00 and 12:00)".
- [Chen i sar. 2022, Scientific Data 9:249](https://doi.org/10.1038/s41597-022-01343-0)
  opisuju poludnevne korake vezane za VIIRS prolaze oko 01:30 i 13:30 lokalnog vremena.
- Lokalne arhive: svih 171 485 zapisa `t` u `feds_{2018,2019,2023}_lf_perimeter.fgb` imaju
  sat 00:00 ili 12:00 (otprilike pola-pola). Fireline sloj nema vremena piksela, pa se iz
  samih podataka UTC i AM/PM ne mogu razlikovati.

**Zaključak.** `t` je oznaka poludnevnog prolaza (00:00 = AM, oko 01:30 lokalnog sunčevog
vremena; 12:00 = PM, oko 13:30), a ne UTC trenutak. Za kohortu (dužine −124° do −102°) stvarni
prolaz je oko 8–10 h kasnije u UTC nego što ga je čitao raniji kod. Nesigurno: da je ulazno
`HHMM` u UTC slijedi iz logike koda, ne iz dokumentacije proizvoda; to ne mijenja zaključak,
jer 00:00 i 12:00 ni u jednom čitanju nisu trenuci akvizicije.

**Posljedice UTC čitanja (izmjereno na manifestu sa 118 slučajeva, prije izmjene).**
- gridMET: tumačenje kao prolaz (01:30/13:30 lokalnog sunčevog minus `Lon/15`), kao lokalno
  sunčevo 00:00/12:00 i kao fiksni MST daju iste dnevne oznake za 118/118 slučajeva; sredine
  segmenata su najmanje 3.2 h od MST ponoći (najmanje 3.235 h, kod najzapadnijeg slučaja). U odnosu na UTC čitanje mijenja se 236/472
  segmenta (svaki slučaj, jedan dan, naizmjenično) i `pre_start` za 66 slučajeva s AM startom.
- Sintetički CA na stvarnim startovima (`synthetic_real_cases.py`) iz `initial_state_time`
  računa lokalni sat za dnevni ciklus; pod UTC čitanjem AM start na −120° dobija oko 16 h
  umjesto oko 01:30.
- Crosswalk i FEDS referentna stanja koriste datume i relativne 12h razmake, pa ih tumačenje
  ne mijenja.

**Odluka (korisnik, 2026-11-09, opcija 2).** `t` se čita kao prolaz u 01:30/13:30 lokalnog
sunčevog vremena u tački gridMET uzorka, preračunat u UTC preko dužina/15
(`feds_overpass_utc` u `src/wildfire_rl/gridmet_weather.py`); segmenti i `pre_start` se grade
iz tog trenutka u jednoj funkciji. Fajl s vremenom mora navesti
`feds_time_reference = feds_t_viirs_overpass_local_solar/v1`, inače ga okruženje odbija.
CA epizode na stvarnim startovima počinju u UTC početku segmenta 0. Zapis odluke:
[ADR-030 dopuna](../specs/DECISION_RECORDS.md).

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
postavke, nije konačna kalibracija. Agentove odluke ostaju na 12h.

## TRAIN-only no-op screen — završen, nije prošao

Osam WAF kandidata (`0, 0.0025, 0.01, 0.025, 0.05, 0.10, 0.20, 0.605`) pokrenuto je
na svih 99 TRAIN slučajeva, uz seed 0, 5-min SimFire korak i isti 48h horizont. Svaki
case je ocijenjen na +12/+24/+36/+48h, ukupno 396 case-timepointa po kandidatu. Svi
runovi su završili 99/99, bez grešaka. SimFire rezultat nije prešao rub na WAF ≤0.05;
WAF 0.10 imao je jedan case sa rubnim kontaktom, 0.20 22 vremenska kontakta, a 0.605
157 kontakata u 61 slučaju.

| Referenca/kandidat | Mean IoU | Mean apsolutna area error (ha) | Rubni kontakti |
|---|---:|---:|---:|
| Persistence | 0.5343 | 2,351.7 | 0 |
| Elipsa | 0.5308 | 2,346.6 | 0 |
| Najbolji kandidat po IoU: WAF 0.0025 | 0.4769 | 2,265.0 | 0 |
| Najbolji kandidat po površinskoj grešci: WAF 0.01 | 0.4769 | 2,262.1 | 0 |

Strogi uslov je bio: 99/99 slučajeva, nula SimFire edge kontakata, veći mean IoU i
manja mean absolute area error od persistence i elipse istovremeno. **0/8 kandidata je
prošlo.** Nije izabran WAF; 5-min korak takođe ostaje provisionalni numerički kandidat.
Detalji i SHA-256 lokalnih run receiptova su u
[TRAIN no-op screen reportu](../../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json);
raw per-case izlazi ostaju ignorisani pod `.local/`.

Osjetljivost za WAF .01 na 1-min koraku dala je IoU .4771, area error 2,265.8ha i nula
edge kontakata, praktično isto kao 5-min korak (.4769 / 2,262.1ha / nula rubova).
Zato nisu pokretani dodatni 3/10/15-min runovi. Ovaj ograničeni nalaz ne zaključava
timebase; interni korak ostaje neizabran.

Ovo je train-only screening, ne fizička validacija: FEDS su satelitske procjene, gridMET
je dnevni 4km proxy, a elipsa jednostavna unaprijed definisana geometrijska referenca.
Validation rasteri nisu preuzeti; 2024 TEST nije otvoren. Benchmark PPO trening i
policy-benefit poređenje ostaju blokirani dok se uzroci prostornog nesklada ne istraže,
postavke zajednički ne kalibrišu i gate ne prođe.

## Dijagnoza i ponovljeni gate — 2026-11-04 (ADR-023/024)

Na drugom računaru su ulazi ponovo izgrađeni iz javnih izvora: svih 99 TRAIN LANDFIRE
fuel/elevation rastera i FEDS početnih maski ima isti SHA-256 kao
[committed coverage report](../../reports/real-fire-data/feds-simfire-input-train-coverage-v1.json),
a svih devet gridMET arhiva isti SHA-256 kao weather report. Python 3.9.25 venv je
samostalan (`uv python install` u `.local/uv-python`); nema više veze na susjedni worktree.
WAF .01 cohort run reproducira ADR-022 do zadnje decimale (IoU .476852, 2,262.1 ha) za
~42 s uz 7 procesa.

[Dijagnoza](../../reports/real-fire-data/feds-simfire-train-noop-diagnosis-v1.json):
cijeli IoU deficit je u trećini timepointa gdje FEDS gotovo ne raste; tamo SimFire dodaje
~262 ćelije uz 2.9% preciznosti. Na brzo rastućim požarima SimFire već pobjeđuje
persistence. Problem je razlikovanje koji požar raste (vjerovatno zbog stvarnog gašenja ili
zaustavljanja), ne smjer vjetra.

Zajednički modul [`feds_simfire_setup.py`](../../src/wildfire_rl/feds_simfire_setup.py)
sada gradi simulaciju za runner, env i benchmark, uz `SimFireParams` (WAF, interni
korak, životni vijek aktivne ćelije, `ros_multiplier`). `ros_multiplier` skalira SimFire
prag paljenja susjedne ćelije, što je ekvivalentno skaliranju Rothermel brzine širenja.
VALIDATION se učitava samo eksplicitno uz commitan TRAIN freeze zapis; TEST se odbija.

Preregistrovana 3×3 mreža (ROS 0.35/0.5/0.7 × WAF 0.05/0.2/0.4) nije dala prolaz. Najbolji
kandidat bez rubnog kontakta, ROS 0.35 / WAF 0.05, ima IoU .5266 i 2,350.5 ha naspram
persistence .5343 / 2,351.7 ha. On je zamrznut kao `FAIL_exploratory`
([gate freeze](../../configs/frozen/feds-simfire-gate-freeze-v1.json)), ali gotovo ne širi
vatru (medijan 0 novih ćelija za 48h). Za korake 7–8 je zato zaseban, jasno označen
free-burn stress zapis WAF .01 / ROS 1.0
([stress record](../../configs/frozen/feds-simfire-stress-scenario-v1.json)).

[VALIDATION no-op](../../reports/real-fire-data/feds-simfire-validation-noop-v1.json),
jednom po zapisu: gate freeze IoU .5419 naspram persistence .5432 (FAIL); stress zapis
IoU .5452 i 1,275.3 ha naspram .5432/1,501.9 ha, bez ruba, pa prolazi strogo pravilo na
ovih 20 slučajeva. Zbog pada na TRAIN-u i malog uzorka to nije dokaz kalibracije.

Komande (sve iz worktree roota, uz `PYTHONPATH=src`, `SDL_VIDEODRIVER=dummy`,
`OMP_NUM_THREADS=1`):

```sh
.local/simfire-venv/bin/python scripts/evaluate_feds_train_noop.py --wind-adjustment-factor 0.05 \
  --ros-multiplier 0.35 --workers 7 --out .local/gate/NEW.json
.local/simfire-venv/bin/python scripts/diagnose_feds_noop_gate.py .local/gate/NEW.json
.local/simfire-venv/bin/python scripts/evaluate_feds_train_noop.py --split validation \
  --frozen-params configs/frozen/feds-simfire-stress-scenario-v1.json \
  --wind-adjustment-factor 0.01 --ros-multiplier 1.0 --workers 7 --out .local/gate/NEW-val.json
```

`build_feds_simfire_inputs.py --fetch-split` piše coverage report direktno u
`reports/real-fire-data/`; pri ponovnoj izgradnji uporedi ga s commitanom verzijom prije
commita.

## Intervencije i prilagodba budžetu — 2026-11-04 (ADR-025–027)

`FedsSimFireEnv` sada prima `sim_params`, `split` (TRAIN zadano, VALIDATION eksplicitno),
`line_placement` (`front_edge` za benchmark) i fiksnu skalu budžeta (`max_budget=4`), te
`reset(options={"scenario_id", "budget"})` za uparenu evaluaciju. Heuristike su u
[`feds_heuristics.py`](../../src/wildfire_rl/feds_heuristics.py). Trening
([`train_feds_budget_adaptation.py`](../../scripts/train_feds_budget_adaptation.py))
koristi 7 `SubprocVecEnv` procesa i ~8 odluka/s; osnovni model od 8,064 odluke traje
15–25 min, fine-tune od 3,024 oko 6 min. Upareni VALIDATION benchmark za 24 politike traje
~5 min na 7 procesa. Checkpointi i puni izvještaji ostaju u `.local/`; commitani su samo
[sažetak s hashovima](../../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json)
i [grafikon](../../reports/real-fire-data/feds-simfire-policy-benchmark-v1.png).

## TRAIN-only PPO putanja

Na korisnikov zahtjev sada postoji tehnička MaskablePPO putanja nad FEDS/LANDFIRE
epizodama, bez čekanja na naučni no-op gate. [`FedsSimFireEnv`](../../src/wildfire_rl/feds_simfire_env.py)
dozvoljava samo manifest TRAIN slučajeve (99), drži isti 48h horizont i četiri 12h
odluke, a budžet se nasumično uzorkuje iz CLI skupa. Akcije su uvijek legalni no-op ili
jedan od osam smjerova koji polaže najviše sedam `FIRELINE` ćelija ispred trenutnog
centroida fronta i troši jednu budžetsku jedinicu. Ovo je diskretni prototip politike,
ne provjeren model operativne gradnje linije.

Observation sadrži samo sažeto trenutno stanje (16×16 agregati burn/front/linija/gorivo),
budžet, vrijeme epizode i vrijeme **posljednjeg gridMET dana strogo prije** dana sljedećeg
12h segmenta; za prvu odluku to je dan prije početka (ADR-030 §1 i dopuna, TASK-023). Vrijeme
koje pokreće sljedeći segment agent nikad ne vidi, osim u označenoj ablaciji sa savršenom
prognozom. Reward je negativan broj dodatnih kumulativno opožarenih ćelija
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
  --wind-adjustment-factor 0.01 --budgets 0,2,4 --seed 7
```

WAF 0.01 u komandi je samo eksplicitan tehnički smoke ulaz; cohort screen je pokazao da
ne prolazi persistence/elipsa gate. WAF .605 iz ranijeg smokea dodiruje rub u 61/99
caseova i ne smije biti korišten kao benchmark parametar. Ne pokretati duži PPO benchmark
dok TRAIN gate ne prođe. Smoke težine i manifest ostaju u ignorisanom `.local/`; svaki
receipt izričito označava da nije fizička validacija, benchmark ni dokaz RL prednosti.

Odvojeni Plateau TRAIN action smoke s budžetom 1 potrošio je tačno jednu jedinicu na
legalnu fireline akciju, a zatim završio preostala tri 12h koraka. To potvrđuje samo
API/budget plumbing; ne potvrđuje učinkovitost ili realističnost linije.

## Sljedeće provjere

1. Dijagnosticirati zašto SimFire no-op mean IoU zaostaje za obije reference; provjeriti
   gridMET proxy, vjetar, fuel/moisture mapping, FEDS rasterizaciju i zajednički grid.
2. Formulisati mali unaprijed dokumentovan shared-parameter candidate set i ponoviti
   TRAIN screen. Bez fitovanja po požaru i bez mijenjanja baseline/metrike nakon ishoda.
3. Validation mape preuzeti tek nakon TRAIN gate prolaza i zaključavanja parametara.
   2024 TEST ostaje zatvoren do završnog obračuna.
4. PPO smoke je tehnički dostupan, ali duži benchmark/policy trening čeka gate. Prije
   agentnog poređenja precizirati operativnu gradnju linije i uskladiti scenarije,
   budžete, horizonte, informacije i seedove.

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
