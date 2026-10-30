---
type: Experiment Report
title: 'Stvarni požari: pregled kandidata i mali uzorci'
---
# Stvarni požari: kandidati, CFSDS pilot i mali uzorci

Prikladnost izvora za naš projekat, ne rezultat fizičke validacije simulatora.
Primarni nalazi i preporuka: docs/research/REAL_FIRE_DATASETS.md.
Candidate manifest: data/manifests/real-fire-candidates.json.

## Odabrani CFSDS put i prvi replay

Glavni izvor je sada CFSDS v1.1 jer se uklapa u Canadian FBP/Cell2Fire. Preliminarni
screen iz 2014–2024 dao je 44 kandidata (do pet po godini; 20 train, 9 validation,
15 test po godini cijelog požara); kohorta nije iscrpna niti zaključana za benchmark.
Pogledaj [kohort manifest](../../data/manifests/cfsds-v1_1-pilot-cohort.json) i
[screen izvještaj](cfsds-cohort-screen.json).

Tri train slučaja imaju verzionisane ulaze, mjere i vizualizacije. `2018_747`
(15–16.08.2018) daje 66 ha novog gorenja prema 15.39 ha opaženih (IoU .2187); svih šest
seedova završava na istoj mapi, koja dotiče rub. `2018_241` (15.08.2018) daje 237 ha
prema 12.153 ha (IoU .0376) i zahvata svih 400 ćelija. `2018_1770` (12.08.2018) daje
73 ha prema 12.151 ha (IoU .1361). Slučajevi `2018_241` i `2018_1770` zasad imaju po
jedan seed bez intervencija; `2018_747` ima i šest ponavljanja. Prva dva su provjerena
bez početnog 20-minutnog zagrijavanja; za `2018_241` mjere se nisu promijenile kad se
zagrijavanje uključi. Ovo nije treniranje, fizička validacija ni rezultat politike;
historijsko gašenje nije poznato.

- [2018_747 manifest](2018_747-case.json), [mjere](2018_747-day228-replay.json), [seedovi](2018_747-seed-sweep.json), [karta](2018_747-day228.png)
- [2018_241 manifest](2018_241-case.json), [no-action mjere](2018_241-day227-replay.json), [20-min zagrijavanje](2018_241-day227-replay-warmup20.json), [karta](2018_241-day227.png)
- [2018_1770 manifest](2018_1770-case.json), [no-action mjere](2018_1770-day224-replay.json), [karta](2018_1770-day224.png)
- [Odbijeni fuel kandidat 2014_538](2014_538-fuel-rejection.json)

Case input je napravljen iz 90 m CFSDS, 250 m nacionalne FBP 2014b karte, 30 m MRDEM
terena i 24-satnog ERA5-Seamless vremena. Izvorne velike datoteke ostaju ignorisane u
Gitu; sažeci, checksum-i, konverter i karta su verzionisani.

FireSpread_MedEU v2: 2.8 MB ZIP preuzet samo za lokalni prostorni pregled. SHA256 i sedam
EFFIS kandidata koji dodiruju granicu BiH navedeni su u
[medeu-spatial-screen.json](medeu-spatial-screen.json). ZIP i Natural Earth granica su
u Git-ignorisanom `data/raw/`; nijedan nije commitan. Ovo nije konačna potvrda lokacije,
zamrznut skup događaja niti simulator replay.

EFFIS European Fuel Map (2017) takođe je preuzeta samo radi provjere dostupnosti
gorivnih klasa na tim lokacijama. ZIP je 18.2 MB; raster je NFFL/Anderson, 250 m i
EPSG:3035. Uzorkovani kodovi nad `205938` i `43482` su u istom screen izvještaju.
Ovaj sloj nije direktan input trenutnom Canadian FBP Firehose buildu. EFFIS-ova opća
reuse licenca je CC BY 4.0 osim specifičnih izuzetaka; provjeriti napomenu za sloj i
navesti citat/izmjene. Raw ZIP ostaje git-ignored.

Dogrib uzorak: 16 fajlova / 3,390,138 bajtova, lokalno u data/raw/dogrib-reference/.
CFSDS uzorak: dva ZIP-a za 2020 / 293,731 bajt, data/raw/cfsds-sample-2020/.
Raw podaci ostaju ignorisani. Ovdje su samo porijeklo/hashovi i mali profili.
Dogrib profile poredi stvarni mask, simulator reference i Firehose mapu; CFSDS
profile provjerava 38 rastera i 372 dnevna reda. Ovo nije provjera cijelog CFSDS-a.

sample-checks.txt je stvarni stdout offline ponavljanja: svih 18 preuzetih fajlova
ima zabilježenu veličinu/SHA256, Dogrib overlap i CFSDS ID/pixel-scale provjere prolaze.
Komanda iz repo roota: python3 scripts/profile_real_fire_samples.py.
Izvršeno Python 3.12.14 / NumPy 2.3.5 / Pillow 12.3.0 (postojeći bundled runtime).
Candidate manifest ne znači da je svaki kandidat preuzet: WildfireSpreadTS i BurnMD
su pregledani samo na nivou javnih metapodataka.
