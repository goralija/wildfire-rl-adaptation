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
početnu lokaciju. Budući perimetar/linija ostaju van agentovog opažanja i nagrade. Detalji: [pipeline](research/REAL_IGNITION_SCENARIO_PIPELINE.md)
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
  scenario-karticu na mreži 128×128 nominalnih 30 m ćelija; sačuvala je izvorni zapis od
  455 B, SHA-256, izvorni ID, MTBS vezu, ulogu incident-referentne tačke i napomenu o
  njenoj neizvjesnosti. To je razvojni primjer, još nije
  slučaj za trening niti simulaciju. [Kartica](../data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json),
  [izvorni zapis](../reports/real-fire-data/fpa-fod-dixie-2021-source.geojson).
- **Prvi pravi-data most je provjeren u dry-run modu.** `scripts/prepare_mineral_landfire.py`
  sada može čitati scenario-karticu ili default Mineral slučaj. Računa fiksnu mapu oko
  prijavljene lokacije, tako da veličina ne zavisi od kasnijeg perimetra ili linije. Dry-run za Mineral
  i Dixie prolazi; operativni SimFire runner može čitati istu karticu.
- **CFSDS/Firehose faza je sačuvana**, ali više nije aktivni dizajn. Njeni prethodni
  izvještaji i metrički brojevi ostaju u arhivi, ne brišu se ni ne prepravljaju.

## Šta još nije urađeno

1. Nema rastera LANDFIRE u SimFire cache-u; pravi request još nije poslan jer `LANDFIRE_EMAIL`
   nije postavljen. Trenutno ima 3.0 GiB slobodno (provjera 2026-11-01), pa je stari navod
   o 29 MiB zastario.
2. Nema odabranog/historijski provjerenog weather niza za Dixie scenario.
3. FPA-FOD pravila korištenja su provjerena, ali imamo samo jedan development kandidat;
   nije izabrana kohorta niti zamrznut event-level split.
4. SimHarness/RLlib nije instaliran ni pokrenut u ovom environmentu.
5. Nema real-input SimFire smokea, treninga, finetunea, heldout evaluacije ni naučnog
   poređenja.
6. BurnMD data reuse licenca i razlika između 243 arhivskih foldera i 308 paper požara
   ostaju otvorena pitanja. BurnMD linijski replay je opcioni track.

## Ograničenja računara

Na provjeri 2026-11-01 `LANDFIRE_EMAIL` nije bio postavljen, a `df -h .` je pokazao 3.0 GiB
slobodno. To je dovoljno za mali podatkovni primjer, ali još ne potvrđuje da na ovom Macu
stane/podržan je SimHarness/RLlib stack. Ne brisati venv, sirove podatke ni korisničke
rezultate da bi se forsirala instalacija.

## Sljedeći taskovi

Aktivni redoslijed je u [backlogu](BACKLOG.md): pribaviti fuel/terrain za već pripremljeni
Dixie scenario; mapirati istorijski weather; provjeriti raster i napraviti prvu real-input
kartu/animaciju; zatim sastaviti veći FPA-FOD uzorak i event-level split; postaviti RL
runtime; tek onda trenirati i porediti politike.

## Kuda dalje

- [HANDOFF](../HANDOFF.md) — kratki nastavak za kolege.
- [NEXT_SESSION](NEXT_SESSION.md) — konkretne komande i zavisnosti.
- [DESIGN](DESIGN.md) — šta se mjeri i zašto.
- [Experiment log](research/EXPERIMENT_LOG.md) — provjere i zaključci.
- [Izvori](research/SOURCES.md) — primarni izvori i datumi pregleda.
- [Arhivirani CFSDS status](STATUS_CFSDS_ARCHIVE.md) — prethodna putanja.
