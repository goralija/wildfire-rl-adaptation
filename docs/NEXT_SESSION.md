---
type: Handoff
title: Naredni korak — napraviti prvi stvarni SimFire scenario
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/BACKLOG.md
  - resource: /docs/research/REAL_IGNITION_SCENARIO_PIPELINE.md
---
# Sljedeći koraci koji otključavaju rad

## Novi praktični cilj

Prvo napraviti **jedan scenario** koji SimFire može pokrenuti na stvarnom gorivu i terenu,
sa prijavljenom lokacijom i datumom incidenta te historijskim vremenom. Tek poslije toga postavljati
RLlib i učiti agenta. Ne pokušavati ponovo zaključivati vrijeme izgrađenih linija za
Mineral; to ostaje zasebna opcija, ne blokada glavnog eksperimenta.

## Šta je već spremno

1. SimFire 2.0.1 radi u `.local/simfire-venv` (Python 3.9.25); funkcionalni demo i izlazi su
   u [simfire-functional-demo](../reports/environment-setup/simfire-functional-demo/).
2. BurnMD archive hash/schema i Mineral geometrije su pregledani. Tačni rezultati i
   vremenska ograničenja su u
   [Mineral audit dokumentu](research/MINERAL_CASE_AUDIT.md).
3. `data/manifests/simfire-scenario.schema.json` definiše format incidenta, grida, izvora
   raster/weather fajlova, simulacije i split-a.
4. Jedan pravi FPA-FOD zapis (Dixie Fire, 2021) je pretvoren u scenario manifest i source
   snapshot od 455 B. To je probni primjer formata, nije uzorak za treniranje.
5. `scripts/prepare_mineral_landfire.py --scenario-manifest ... --dry-run` računa Dixie
   fiksnu mrežu 128×128 nominalnih 30 m ćelija i priprema ispravan cache path za SimFire.
   Granice se ne biraju iz kasnijih linija/perimetara.

## Ograničenja ovog hosta koja su stvarno izmjerena

- `LANDFIRE_EMAIL` nije postavljen u ovom shellu. LFPS traži kontakt-email; ne izmišljati
  ga i ne koristiti privatni email iz Git konfiguracije.
- Zadnja disk-provjera je pokazala 3.0 GiB slobodno (2026-11-01); prethodni navod o 29 MiB
  je zastario. To još ne potvrđuje da SimHarness/RLlib stack stane ili radi na ovom hostu.
- `SimHarness/RLlib` i konverzija vremenskih uslova nisu još urađeni.

## Konkretan nastavak nakon što ima prostora

### 1) Završiti prvi real-input case

Početni candidate je Dixie Fire 2021: [scenario kartica](../data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json),
[mali source snapshot](../reports/real-fire-data/fpa-fod-dixie-2021-source.geojson). Dobiti
provjeren fuel/elevation i historijski weather za isti fiksni prozor. Konačna veličina ne
ulazi agentu kao input ili reward.

### 2) Dobiti i provjeriti raster

Nakon što je postavljen LANDFIRE kontakt-email i dovoljno slobodnog prostora:

```sh
SF_HOME="$PWD/.local/simfire-mineral-2020" \
  .local/simfire-venv/bin/python scripts/prepare_mineral_landfire.py \
  --scenario-manifest data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json --dry-run
LANDFIRE_EMAIL='tvoja adresa za LANDFIRE zahtjev' \
SF_HOME="$PWD/.local/simfire-mineral-2020" \
  .local/simfire-venv/bin/python scripts/prepare_mineral_landfire.py \
  --scenario-manifest data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json
```

Ovo pribavlja LF2016_FBFM13 + LF2020_Elev za 2021 Dixie development tile. Fuel je pet
godina stariji od događaja, pa je tehnički pre-event kandidat, ne automatski naučno
potvrđena mapa. Provjeriti receipt/hash, GeoTIFF bounds/CRS, band redoslijed, no-data/
kodove i da li prijavljena referentna lokacija padne u očekivanu ćeliju. Dixie tačka
   nije potvrđen GPS položaj paljenja.

### 3) Weather i prvi real-input smoke

Za isti događaj povući historijski weather iz dokumentovanog izvora i zapisati vremensku
zonu/jedinice. SimFire smoke config i dalje koristi demo wind/moisture; ne označiti ih kao
historijske dok se mapiranje ne implementira i provjeri. Popuniti scenario manifest nakon
što se inputi provjere, pa pokrenuti scenario-manifest runner i napraviti kartu/animaciju.

### 4) RL okruženje i benchmark

Nakon što je prostor dostupan, provjeriti podržan Python 3.9 RLlib/SimHarness stack u
izolovanom environmentu. Zabilježiti OS, paketne verzije i smoke. Ako zvanični stack ne
stane/ne radi na Macu, izabrati mali izolovani Linux runtime, ne instalirati stare pakete
globalno. Potom event-level split, budget check, base-vs-fine-tune i uparene heldout
trajektorije.

## Kanonski dokumenti

- [DESIGN](DESIGN.md)
- [scenario pipeline](research/REAL_IGNITION_SCENARIO_PIPELINE.md)
- [STATUS](STATUS.md), [BACKLOG](BACKLOG.md)
- [SimFire environment](research/SIMFIRE_ENVIRONMENT.md)
- [source list](research/SOURCES.md)
- [ADR-040](specs/DECISION_RECORDS.md#adr-040--train-on-real-ignition-conditions-with-simulated-actions-2026-11-01)
