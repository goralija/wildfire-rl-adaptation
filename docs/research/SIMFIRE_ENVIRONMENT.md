---
type: Environment Record
title: SimFire okruženje i prvi stvarni raster smoke — 2026-11-01
sources:
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /docs/research/EXPERIMENT_LOG.md
  - resource: /docs/research/SOURCES.md
---
# SimFire okruženje i probna pokretanja

## Okruženje

MITRE SimFire 2.0.1 je pinovan u `external/simfire` na commitu
`04905b19fe8c10dc08d64faddd00303e0561bb66`. Za njega postoji lokalni Python 3.9.25 venv
`.local/simfire-venv/`; globalni Python nije mijenjan. Snapshot je
[`simfire-macos-arm64-py39.freeze.txt`](../../requirements/simfire-macos-arm64-py39.freeze.txt).
`setuptools<81` ostaje zbog SimFireovog `pkg_resources` importa; rasterio 1.4.3 i affine
3.0.1 su dodani za provjeru GeoTIFF-a. Venv, SimFire klon i sirovi podaci su ignorisani u
Gitu. Ovo je macOS ARM64 lock, ne prenosivi Linux/Windows environment.

SimHarness/RLlib nije instaliran. Pokretanje standalone SimFire potvrđuje samo simulator,
ne RL algoritam ili agenta.

## Reproducibilni pokreti

### Funkcionalni demo na generisanoj mapi

```sh
.local/simfire-venv/bin/python scripts/run_simfire_demo.py \
  --steps 30 \
  --out runs/simfire-demo/first
```

Rezultat je [GIF, završna slika i receipt](../../reports/environment-setup/simfire-functional-demo/).
Ovaj primjer ne koristi historijske slojeve.

### Stvarni LANDFIRE slojevi za razvojni Dixie scenario

```sh
.local/simfire-venv/bin/python scripts/fetch_simfire_real_inputs.py
.local/simfire-venv/bin/python scripts/run_simfire_real_input_smoke.py --steps 30
```

`fetch_simfire_real_inputs.py` poziva javne LANDFIRE ImageServer servise, bez LANDFIRE
naloga/emaila, i Open-Meteo `/v1/archive`. Preuzima:

- LF2016 FBFM13 za gorivo. Tile sadrži kodove `1,2,4,5,6,7,8,9,10,91,98,99`; svi se
  prepoznaju u pinned SimFire mapiranju. Ovo je pet godina starije od Dixie požara iz 2021.
- LF2020 Elevation za teren. Sirove vrijednosti su 456–1385 m; SimFire adapter ih pretvara
  u feet pomoću upstream funkcije `meters_to_feet`.
- 24 ERA5 sata za datum 2021-07-13 uz koordinate FPA-FOD zapisa, tražena u UTC.

Dva rastera su jedan pojas, `128×128`, isti EPSG:32610, isti projected bounds
`[636690, 4413360, 640530, 4417200]` m i 30 m piksel. LANDFIRE služba uzorkuje na taj grid
nearest-neighbor. CRS, granice, oblik, no-data i kodove goriva skripta provjerava prije
SimFire pokretanja. Maknuli smo se od SimFireovog fiksnog stepen-po-ćeliji izreza: taj
proračun nije tačno 30 m na terenu. Scenario builder i zajednička kartica sada čuvaju
projekciju i metre.

Raw TIFF/ERA5 JSON ostaju u ignorisanom `.local/real-input-dixie/`. Skripta ispiše provenance
receipt; scenario kartica i receipt čuvaju hashove. To omogućava timu da ponovi preuzimanje
bez čuvanja velikih podataka u Gitu.

### Šta real-input smoke dokazuje

30-minutni SimFire run koristi stvarni LF2016 fuel raster i LF2020 elevation niz. Njegova
mala [ulazna mapa, završno stanje, GIF i receipt](../../reports/real-fire-data/simfire-dixie-real-input-smoke/)
potvrđuju da se mapirani slojevi učitavaju i simulator se pokreće na njima.

Ovaj smoke **nije** historijski fire replay, RL trening ni fizička validacija. Koristi demo
wind 7 mph/direction 90° i moisture 3%. ERA5 JSON postoji, ali nije ulaz simulacije:
meteorološki vjetar je na 10 m, SimFire traži midflame wind, a RH vazduha nije vlaga
mrtvog goriva. FPA-FOD `discovery_time=1615` ostaje bez potvrđene vremenske zone, zato
ERA5 sati nisu poravnati s tačnim discovery trenutkom.

FPA-FOD Dixie koordinate su incident-referentna tačka s nepoznatom događajnom preciznošću,
ne potvrđen GPS ignition. Grid od 30 m opisuje samo veličinu raster ćelije i ne pojačava
preciznost te koordinate. Završni fire size/perimeter nisu agentu dati niti su reward.

## Šta slijedi

Prije agent treninga riješiti tri otvorene stvari: bolji/vremenski odgovarajući fuel
vintage, izvorni timezone ili razumna date-only politika, i zasebno opravdan način tretmana
10 m vjetra i gorivne vlage. Zatim napraviti više događaja i split po cijelim incidentima.
Pogledati [scenario pipeline](REAL_IGNITION_SCENARIO_PIPELINE.md),
[status/backlog](../STATUS.md) i [EXP-033](EXPERIMENT_LOG.md#exp-033--real-layers-fetched-and-loaded-by-simfire-2026-11-01).
