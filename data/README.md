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

## Dataset opaženih požara
Za zasebnu historijsku provjeru preuzeti su mali Dogrib i CFSDS uzorci, ukupno
3,683,869 bajtova u ignorisanom data/raw/. [Preporuka i ograničenja](../docs/research/REAL_FIRE_DATASETS.md)
razlikuju opaženi ishod od simulator inputa. Kandidati su u
manifests/real-fire-candidates.json, hashovi/profili u reports/real-fire-data/.
Nije još izvršen replay/kalibracija na tim događajima. Raw podaci nisu dodani u Git.
