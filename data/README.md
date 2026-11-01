---
type: Dataset Reference
title: Podaci, porijeklo i Git politika
---
# Podaci, porijeklo i Git politika

`manifests/upstream.json` pinova Firehose izvor i dostupne modele. `configs/pilot.json`
je cijeli mali sintetički landscape: 20×20 ćelija, ignition, negorive ćelije i prioriteti.
Pilot nema satelitskih snimaka, stvarnih kuća ili labelovanja ljudi. Maska prioriteta je naš
sintetički izbor, ne ground-truth procjena rizika. Jedna ćelija nema definisanu površinu
u hektarima; izvještavati ćelije i udjele, ne izmišljati prostornu rezoluciju.

U Git idu kod, male konfiguracije, manifesti, sažeci, mali provjereni CSV/SVG rezultati.
Izvan Gita ostaju `external/`, `data/raw/`, `artifacts/`, `runs/`, `.venv/` i `private/`.
Modeli/rasteri za kasnije: vanjsko spremište ili Git LFS nakon dogovora, uvijek URL,
commit/verzija, SHA256, licenca, preprocessing i scenario split. Ne preuzimati gigabajte.

Firehose i originalni Cell2Fire navode GPL-3.0 u repozitorijima. Kod trećih strana
nije kopiran u naš `src`. Licenca svakog dataset-a i težina može zahtijevati dodatnu
provjeru; ne pretpostavljati da javni GitHub znači slobodnu redistribuciju podataka.
Licenca za naš projekat je otvorena timska odluka prije javnog objavljivanja izdanja.

Data card prije glavnih eksperimenata: porijeklo, područje, rezolucija, gorivo,
weather, ignition, NODATA, priority definicija, prostorna usklađenost, licence,
hash sirovih i obrađenih fajlova, preprocessing komanda i split bez curenja.

## Početni simulator inputi
Sada je pregledan i izvršen Firehose Sub20x20 input. Detaljan [data card](../docs/research/DATASET.md)
navodi 400 ćelija, 4 rastera, Data.csv, lookup i 130 weather fajlova, uz provjere i
ograničenja. Hash svakog fajla je u reports/firehose-verification/dataset-inventory.json.
U Git idu ti mali manifesti, a sirovi dataset ostaje u external/firehose/data/Sub20x20/.

## Aktivni scenarij izveden iz FPA-FOD-a

Trenutni put je **USFS FPA-FOD → zajednički scenario JSON → LANDFIRE fuel/terrain +
ERA5 context → SimFire**. Prvi mali zapis je Dixie Fire 2021, `FOD_ID 401019270`. Službeni
archive navodi da se FPA-FOD može koristiti bez dodatne dozvole ili naknade uz citat Short
(2026); priključene mape imaju svoja pravila. Koordinata je incident-referentna lokacija,
ne potvrđen GPS položaj paljenja. Kartica je development primjer bez train/test pripadnosti.
Stvarni fuel i teren su pokrenuti u SimFire smokeu; ERA5 je pribavljen, ali još nije
mapiran u simulator.

- [Scenario manifest](manifests/simfire-fpa-fod-401019270-dixie-candidate.json)
- [Izvorni GeoJSON zapis, 455 B](../reports/real-fire-data/fpa-fod-dixie-2021-source.geojson)
- [Pretvarač jednog FPA-FOD zapisa](../scripts/build_fpa_fod_scenario.py)
- [LANDFIRE + ERA5 fetcher](../scripts/fetch_simfire_real_inputs.py)
- [SimFire real-layer runner](../scripts/run_simfire_real_input_smoke.py) i [sačuvane slike/receipt](../reports/real-fire-data/simfire-dixie-real-input-smoke/)
- [Zajednička šema i prazan template](manifests/simfire-scenario.schema.json), [template](manifests/simfire-scenario.template.json)

Raw TIFF/JSON su u Git-ignorisanom `.local/real-input-dixie/`; manifest i receipts sadrže
source, verziju, preprocessing i SHA-256. U Gitu su male slike i reproducibilan kod, ne raw
rasteri.

## Arhivirani dataset opaženih požara

Prethodna putanja je bila **CFSDS v1.1 + Canadian FBP/Cell2Fire**. 23 godišnja ZIP
para iz 2002–2024 (102,405,239 bajtova) i svi veći sirovi slojevi su lokalno u
Git-ignorisanom `data/raw/`. Candidate manifest je
[`cfsds-v1_1-pilot-cohort.json`](manifests/cfsds-v1_1-pilot-cohort.json); njegov trenutni
geometrijski screen zadržava do pet kandidata po godini, ukupno 20 train, 9 validation,
15 test. To nije iscrpan ni finalan benchmark.

Tri train slučaja (`2018_747`, `2018_241`, `2018_1770`) pretvorena su u simulator ulaze
i pokrenuta kao C++ no-action replayi bez treniranja. Prognoze su 66/237/73 ha prema
opaženih 15.39/12.15/12.15 ha; sve tri dotiču rub 2×2 km prozora. Kandidat `2014_538`
je odbijen na fuel kompatibilnosti jer dio historijskog scar/front/targeta mapira na
water/nonfuel. Suppression status nije poznat. Izvještaji, hashovi i vizualizacije su u
[`reports/real-fire-data/`](../reports/real-fire-data/README.md). [Pipeline objašnjava
razliku između simulator ulaza i historijskog cilja](../docs/research/REAL_CASE_PIPELINE.md).

Dogrib ostaje formatni primjer, ali dijeli gorivo/elevation s Firehose Sub20 i nije
nezavisan prostorni test. FireSpread_MedEU v2 je pregledan za moguću BiH studiju: ZIP
(2.75 MB) je u `data/raw/`, prvi grubi overlay našao je sedam EFFIS ID kandidata. EFFIS
European Fuel Map 2017 (250 m, NFFL/Anderson) je uzorkovana preko dva primjera, ali taj
fuel model ne odgovara trenutnom Canadian FBP buildu. MedEU licenca/lokacije, veći grid i
kompatibilan evropski model ostaju otvoreni ako kasnije izaberemo taj track. Hashovi,
izvori i ograničenja su u `reports/real-fire-data/medeu-spatial-screen.json`.

Veliki raw fajlovi, Docker image, virtualno okruženje i simulator runovi nisu dodani u
Git. Repo čuva URL, verziju, checksum, konverzijski kod, sažet case manifest i mali
vizualni rezultat. Pogledaj `reports/real-fire-data/cfsds-download-manifest.json` za
preuzimanje CFSDS arhive.
