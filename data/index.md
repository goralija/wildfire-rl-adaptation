# Podaci i provenance

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
