---
type: Project Status
title: Stanje projekta — simulator i realni scenariji
sources:
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/research/EXPERIMENT_LOG.md
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
---
# Gdje smo sada

## Cilj, najjednostavnije

Poredimo osnovnog agenta i istog agenta nakon dodatnog učenja. Obojica dobiju identične
uslove i budžet da postave linije u **simulaciji**. Želimo da fine-tunirani agent sagori
manje simuliranog prostora u odabranim scenarijima. Ne obećavamo da bi požar u stvarnosti
bio manji za istu površinu.

Više ne tražimo da svaki historijski red vatrogasne linije ima tačno vrijeme gradnje prije
nego što počnemo. Mineral Fire audit je pokazao prazna polja vremena; korištenje obližnjeg
`CreateDate` bi značilo nagađanje. Umjesto toga, scenario počinje od prijavljene lokacije
i datuma otkrivanja incidenta, stvarnog goriva/terena i dokumentovanog vremena. FPA-FOD
tačka ne mora biti tačno mjesto paljenja, pa je za Dixie koristimo samo kao približnu
referencu scenarija. Budući perimetar/linija ostaju van agentovog opažanja i nagrade. Detalji: [pipeline](research/REAL_IGNITION_SCENARIO_PIPELINE.md)
i [ADR-040](specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01).

## Šta je stvarno urađeno

- **SimFire se pokrenuo.** MITRE SimFire 2.0.1 je instaliran lokalno u posebnom Python
  3.9.25 venvu. 30-min funkcionalni smoke je napravio GIF, mapu i receipt. To je bila
  funkcionalna demonstracija na generisanoj mapi, ne historijski požar, trening ni
  fizička validacija. [Slike i receipt](../reports/environment-setup/simfire-functional-demo/).
- **Pravi BurnMD fajl je pregledan.** Hash ZIP-a odgovara MITRE LFS pointeru. Mineral ima
  11 perimetara, 249 operativnih linija i 58 tačaka. Sve linije imaju prazne per-vertex
  timestamp liste, a `LineDateTi` je null za 249/249. Apache oznaka repo-a nije potvrđena
  licenca podataka. [Metadata audit](../reports/real-fire-data/mineral-case-audit.json),
  [detaljno objašnjenje](research/MINERAL_CASE_AUDIT.md).
- **Napravljen je zajednički scenario format.** JSON čuva mali opis događaja i putanje/hash
  velikih fuel/terrain/weather ulaza; ima [šemu](../data/manifests/simfire-scenario.schema.json)
  i [template](../data/manifests/simfire-scenario.template.json).
- **Uvezen je jedan stvarni slučaj kao probna kartica.** Iz službenog USFS FPA-FOD servisa
  preuzet je Dixie Fire 2021 (`FOD_ID 401019270`). Skripta ga je pretvorila u fiksnu
  128×128 mrežu u UTM-u sa stvarnih 30 m ćelija; sačuvala je izvorni zapis od
  455 B, SHA-256, izvorni ID, MTBS vezu, ulogu incident-referentne tačke i napomenu o
  njenoj neizvjesnosti. To je razvojni primjer, još nije
  slučaj za trening niti simulaciju. [Kartica](../data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json),
  [izvorni zapis](../reports/real-fire-data/fpa-fod-dixie-2021-source.geojson).
- **Preuzeti su i provjereni stvarni okolišni ulazi.** Javni LANDFIRE ImageServer dao je
  FBFM13 goriva za 2016. i visinu terena za 2020. ERA5 je dao 24 sata vremena na datum
  otkrivanja. Dva rastera su poravnata na isti EPSG:32610 grid od 128×128 ćelija po 30 m;
  u gorivu su provjereni kodovi i oba TIFF-a imaju odgovarajuće granice/CRS.
- **SimFire je pokrenut nad tim rasterima.** 30-minutni smoke je napravio kartu goriva i
  visine, završno stanje požara i GIF. Ovo dokazuje da stvarni rasteri ulaze u SimFire.
  Vjetar i vlaga su još demonstracijske vrijednosti; ERA5 nije potajno proglašen istim
  varijablama koje simulator traži. [Izlazi i receipt](../reports/real-fire-data/simfire-dixie-real-input-smoke/).
- **Podaci su u lokalnom ignorisanom folderu.** Ponovno preuzimanje radi
  `scripts/fetch_simfire_real_inputs.py`; sirovi GeoTIFF/JSON se ne commitaju, a njihove
  putanje i SHA-256 su u scenario kartici i receiptu.
- **CFSDS/Firehose faza je sačuvana**, ali više nije aktivni dizajn. Njeni prethodni
  izvještaji i metrički brojevi ostaju u arhivi, ne brišu se ni ne prepravljaju.

## Šta još nije urađeno

1. Fuel karta je LF2016, pet godina prije Dixie požara; to je pre-event kandidat, ne
   potvrđena 2021 karta vegetacije. DEM je iz 2020.
2. ERA5 niz je preuzet za 2021-07-13 u UTC, ali nije ubačen u simulaciju. Vrijeme FPA
   `1615` nema potvrđenu zonu u našem zapisu; ERA5 vjetar je na 10 m, a SimFire očekuje
   midflame wind; relativna vlažnost vazduha nije vlaga goriva.
3. FPA-FOD pravila korištenja su provjerena, ali imamo samo jedan development kandidat;
   nije izabrana kohorta niti zamrznut event-level split.
4. SimHarness/RLlib nije instaliran ni pokrenut u ovom environmentu.
5. Nema policy treninga, fine-tunea, heldout evaluacije ni naučnog poređenja. Real-input
   smoke nije fizička validacija i ne govori koliko bi površine izgorjelo u stvarnosti.
6. BurnMD data reuse licenca i razlika između 243 arhivskih foldera i 308 paper požara
   ostaju otvorena pitanja. BurnMD linijski replay je opcioni track.

## Ograničenja računara

Na provjeri 2026-11-01 `df -h .` je pokazao 3.0 GiB slobodno. To je bilo dovoljno za mali
LANDFIRE/ERA5 izrez i smoke; još ne potvrđuje da na ovom Macu stane ili radi SimHarness/RLlib
stack. Javni LANDFIRE ImageServer je omogućio preuzimanje bez LFPS kontaktnog emaila.
Ne brisati venv, sirove podatke ni korisničke rezultate da bi se forsirala instalacija.

## Sljedeći taskovi

Aktivni redoslijed je u [backlogu](BACKLOG.md): prvo opravdati/izabrati datum i fuel-moisture
ulaz, pa mapirati ERA5 10-m vjetar na smislen SimFire ulaz ili zadržati njegove vrijednosti
izvan modela; zatim proširiti događaje, zamrznuti event-level split, postaviti RL runtime,
pa trenirati i porediti politike.

## Kuda dalje

- [HANDOFF](../HANDOFF.md) — kratki nastavak za kolege.
- [NEXT_SESSION](NEXT_SESSION.md) — konkretne komande i zavisnosti.
- [DESIGN](DESIGN.md) — šta se mjeri i zašto.
- [Experiment log](research/EXPERIMENT_LOG.md) — provjere i zaključci.
- [Izvori](research/SOURCES.md) — primarni izvori i datumi pregleda.
- [Arhivirani CFSDS status](STATUS_CFSDS_ARCHIVE.md) — prethodna putanja.
