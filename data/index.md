# Podaci i provenance

- [Aktivna FPA-FOD/SimFire kohorta — 80 požara](manifests/simfire-fpa-fod-cohort-v2.json) i [laiki data card](../docs/research/SIMFIRE_FPA_COHORT.md) - 40 train / 20 validation / 20 test, po incidentima.
- [Eval membership rezervacija](manifests/simfire-fpa-fod-evaluation-membership-v1.json) - 40 train / 20 validation / 19 budućih test incidenata; izuzeti Larch Creek smoke.
- [Provenance preuzimanja](../reports/real-fire-data/simfire-cohort-v2-input-acquisition.json) - LANDFIRE gorivo/teren za 80/80.
- [gridMET weather receipt](../reports/real-fire-data/simfire-cohort-v2-gridmet-weather.json), [QC summary](../reports/real-fire-data/simfire-cohort-v2-gridmet-summary.json) i [graf](../reports/real-fire-data/simfire-cohort-v2-gridmet-overview.png) - sirovi dnevni historijski kontekst za 80/80.
- [SimFire weather mapping receipt](../reports/real-fire-data/simfire-cohort-v2-gridmet-simfire-mapping.json) i [mapirani JSON-ovi](processed/simfire-cohort-v2-gridmet-mappings/) - transparentni proxy ulazi za 80/80; hourly replay 0/80.
- [No-op probe kod](../scripts/smoke_simfire_noop_horizon.py) i [rezultati/slike](../reports/real-fire-data/simfire-cohort-v2-gridmet-noop-horizon/) - ne koristi agenta ni intervenciju; Larch Creek iz test splita je tehnički otvoren i izostavlja se iz završne evaluacije.
- [WAF sensitivity smoke](../reports/real-fire-data/simfire-cohort-v2-gridmet-waf-sensitivity.json) - tehnički tok kroz WAF 0.1/0.3/0.5, bez učenja ili fizičke validacije.
- [Scenario kartice](manifests/simfire-cases-v2/) - izvorni ID, prijavljena lokacija, grid, seed cell, split, input pathovi i hashovi za svaki požar.
- [Seed izbor](../reports/real-fire-data/simfire-cohort-v2-seed-selection.json) - 71 prijavljena ćelija goriva, 9 najbližih zamjenskih ćelija po fuel-only pravilu.

- [SimFire scenario JSON schema](manifests/simfire-scenario.schema.json) i [template](manifests/simfire-scenario.template.json) - zajednički ugovor za događaj, grid, input fajlove/hashove i simulaciju; bez velikih rasterskih polja u JSON-u.

- [Dixie Fire probna kartica](manifests/simfire-fpa-fod-401019270-dixie-candidate.json) i [sačuvani izvorni zapis](../reports/real-fire-data/fpa-fod-dixie-2021-source.geojson) - jedan stvarni incident u zajedničkom formatu; stvarni fuel/terrain su pokrenuti u smokeu, ali scenario nije trening slučaj.
- [FPA-FOD → SimFire pretvarač](../scripts/build_fpa_fod_scenario.py) - lokalno pravi karticu iz jednog zapisa, čuva izvorni hash i ne izmišlja nedostajuće ulaze.
- [LANDFIRE/ERA5 preuzimanje](../scripts/fetch_simfire_real_inputs.py) i [stvarni ulazni SimFire smoke](../scripts/run_simfire_real_input_smoke.py) - reproducibilan 128×128 UTM izrez i slojevi koje stvarno čita SimFire; vremenski niz još nije ubačen.

- [CFSDS pilot cohort manifest](manifests/cfsds-v1_1-pilot-cohort.json) - Odabrana putanja, preliminarni event splitovi i prvi C++ replay.
- [TRAIN terrain/weather provenance](../reports/real-fire-data/cfsds-train-terrain-weather-provenance.json) - Source-class i weather snapshot porijeklo za tri stara TRAIN slučaja; nije benchmark ulaz.
- [ERA5-FWI-SN audit](../reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json) i [upareni replay](../reports/real-fire-data/era5-fwi-sn-2018-weather-replay-comparison.json) - provjereni dnevni FWI fajlovi i kontrolisana osjetljivost na tri kopije; sirovi fajlovi su ignorisani i nisu u Gitu.
- [Dogrib public-file manifest](../reports/real-fire-data/dogrib-download-manifest.json) - URL-ovi i SHA-256 za mali GIS/format fixture; raw datoteke ostaju ignorisane.
- [Dogrib alignment QC](../reports/real-fire-data/dogrib-reference-alignment.json) - koordinate paljenja, rasterska mreža, scar/gorivo i vremenski obuhvat.

## Dokumenti

- [Podaci, porijeklo i Git politika](README.md) - Dataset Reference
