---
type: Reference
title: Izvori i literatura
---
# Izvori i literatura

Primarni izvori; datumi pregleda su navedeni uz stavke. Postojeći rad nije naš rezultat.

| ID | Izvor | Uloga / ograničenje |
| --- | --- | --- |
| S-001 | [Firehose projekat, Shen & Curtis, 2022](https://williamshen-nz.github.io/firehose/) | polazni rad, baseline i već postojeće priority zone |
| S-002 | [Firehose rad](https://williamshen-nz.github.io/firehose/firehose-paper.pdf) | definicija idealizirane intervencije i eksperimenti; studentski projektni izvještaj |
| S-003 | [Firehose izvor](https://github.com/aidan-curtis/firehose/tree/e49a52a9a987a1585d25ddca2f711222ca500ffb) | pregledani kod i modeli, pin u manifestu |
| S-004 | [Pais et al., Cell2Fire, 2021](https://doi.org/10.3389/ffgc.2021.692706) | naučna osnova simulatora; nije validacija našeg adaptera |
| S-005 | [Originalni Cell2Fire](https://github.com/cell2fire/Cell2Fire) | build dokumentacija i upućivanje na drugi fork |
| S-006 | [MITRE SimFire](https://github.com/mitrefireline/simfire), [docs](https://mitrefireline.github.io/simfire/) | sadašnji standalone simulator; samo funkcionalni 30-min smoke je izvršen, još bez historical BurnMD replaya ili RL benchmarka |
| S-007 | [MITRE SimHarness](https://github.com/mitrefireline/simharness) | alternativni RL harness; nema dokaza prenosa Firehose težina |
| S-008 | [Fire2A C2F-W](https://github.com/fire2a/C2F-W) | drugi model goriva/razvoj; nije drop-in Firehose backend |
| S-009 | [Schulman et al., PPO, 2017](https://arxiv.org/abs/1707.06347) | razlog izbora PPO porodice, ne obećanje učinka |
| S-010 | [Huang & Ontañón, 2020](https://arxiv.org/abs/2006.14171) | teorija i empirija invalid action masking |
| S-011 | [Agarwal et al., 2021](https://arxiv.org/abs/2108.13264) | motivacija za intervale i više treninga |
| S-012 | [Gymnasium custom env](https://gymnasium.farama.org/introduction/create_custom_env/) | trenutni reset/step kontrakt, provjeren kroz Context7 |
| S-013 | [MaskablePPO dokumentacija](https://sb3-contrib.readthedocs.io/en/master/modules/ppo_mask.html) | maske pri učenju i predict/evaluation |

Činjenice iz korisničke prepiske i slike imaju lokalnu provenance evidenciju, ne javni URL.

## Razlika prema polaznom radu

Firehose već obuhvata CNN politike, maskiranje, više ignition postavki i prioritetne
nagrade. Naš predloženi doprinos je kontrolisano ispitivanje adaptacije preko budžeta,
uz jasne troškove, kumulativnu štetu, uparene scenarije i analizu ukupne/prioritetne
štete. Originalnost tog uskog doprinosa još zahtijeva širi pregled literature prije
konačne tvrdnje; nije provedena sistematska literature review.

## Runtime continuation sources
- [Autorski SB3 contrib fork](https://github.com/williamshen-nz/stable-baselines3-contrib/tree/43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3): stvarno korišten, verzija 1.5.0.
- [PyTorch 1.13.1 release files](https://pypi.org/project/torch/1.13.1/): potvrđen ARM64 Linux wheel za legacy runtime.
- Checkpoint `system_info.txt`, lokalni C++/Python kod, dataset fajlovi i izvršeni
  stdout/JSON su primarni dokazi nastavka; receipti i hashovi su u reports/firehose-verification/.

## Historijski požari: izvori pregledani 2026-10-28 i dopunjeni 2026-10-30

- S-014: [Kim, Pais & Gonzalez, 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12254405/),
  DOI 10.1038/s41598-025-05706-6; Dogrib kao Cell2Fire validacijski slučaj.
  [Podaci i kod](https://github.com/humnetlab/Cell2Fire/tree/84e3c817ad866358d8db28e87c9445b42aaf7908),
  pin 84e3c817…; zasebno pregledan originalni Dogrib_v624 README (Alberta, 2019-02-03).
- S-015: [Barber et al., 2024, CFSDS](https://pmc.ncbi.nlm.nih.gov/articles/PMC11239873/),
  DOI 10.1038/s41597-024-03436-4; [OSF podaci](https://osf.io/f48ry/),
  DOI 10.17605/OSF.IO/F48RY. Rad opisuje v1; [version record](https://osf.io/download/8fe4u/)
  dokumentuje v1_1 od 2025-06-12. Provjeren javni OSF API: projekt, fajlovi i
  [deklarisana CC-BY 4.0 licenca](https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e96a/).
- S-016: [Gerard, Zhao & Sullivan, WildfireSpreadTS](https://zenodo.org/records/8006177),
  DOI 10.5281/zenodo.8006177; [autorski code/loader](https://github.com/SebastianGer/WildfireSpreadTS).
  Pregledani javni metapodaci; arhiva nije preuzeta niti očišćena u ovom projektu.
- S-017: [MITRE BurnMD](https://github.com/mitrefireline/burnmd), pregledan ponovo 2026-11-01.
  GitHub repozitorij sadrži `BurnMD.zip` kroz Git LFS. Ovo je izvor arhive, ne dokaz da
  licenca koda pokriva podatke; vidi S-054.
- S-019: [Bennett, Jain, Moore & Boisvert, 2026, W.I.S.E. assessment using CFSDS 1.1](https://doi.org/10.1071/WF26072),
  *International Journal of Wildland Fire* 35(8), WF26072. Novija peer-reviewed
  procjena dokumentuje v1.1 obim, dnevne FBP/terrain/weather potrebe, filtere i
  razliku između osnovnog i ciljano podešenog modelskog poređenja.
- S-020: [Canadian Wildland Fire Information System — FBP fuel maps](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/current/),
  pregledano 2026-10-30. Dinamički katalog; uključuje 2026 rastere do 30 m i oko 3 GB.
  To nije pinovana ulazna mapa projekta i nije preuzeta.
- S-021: [Alberta wildfire maps and data](https://www.alberta.ca/wildfire-maps-and-data),
  pregledano 2026-10-30. Historijski zapisi/perimetri dostupni u više vremenskih opsega;
  geospatial portal traži verificiran Alberta.ca nalog. Finalni perimetri sami ne daju
  dnevni redoslijed širenja.
- S-022: Müller et al. (2026), [FireSpread_MedEU v2 dataset](https://zenodo.org/records/18200075),
  DOI 10.5281/zenodo.18200075; [peer-reviewed Data Descriptor](https://doi.org/10.1038/s41597-026-06965-2).
  Pregledano 2026-10-30: 103 evropsko/mediteranska požara, 320 ~3 m progression koraka,
  dnevno kad satelitske slike dozvoljavaju. Zenodo v2 data-license metadata nije prikazan;
  članak je CC-BY-4.0, što nije dokaz licence zasebnog dataset zipa. Ne koristi se kao
  Canadian FBP input bez opravdanog gorivnog modela.
- S-023: [JRC/GWIS GlobFire v2 DailyPerimeters](https://developers.google.com/earth-engine/datasets/catalog/JRC_GWIS_GlobFire_v2_DailyPerimeters),
  MODIS MCD64A1-derived global fire event progression, 2001–2021, 500 m nominal daily,
  CC-BY-4.0 per Earth Engine catalog metadata; [GWIS technical note](https://gwis.jrc.ec.europa.eu/about-gwis/technical-background/statistics)
  describes several-day timing uncertainty. Coarse global fallback, not Cell2Fire-ready.
- S-024: [FireSpread_MedEU v2 Zenodo record](https://zenodo.org/records/18200075),
  [peer-reviewed Data Descriptor](https://doi.org/10.1038/s41597-026-06965-2), and our
  [local spatial screen](../../reports/real-fire-data/medeu-spatial-screen.json).
  On 2026-10-30 a 2,751,019-byte archive was inspected locally; seven EFFIS IDs were
  first-pass overlaps with a coarse Bosnia and Herzegovina country boundary. Do not
  assume the empty Zenodo license field is covered by the article's CC-BY license.
- S-025: [EFFIS data and services](https://forest-fire.emergency.copernicus.eu/applications/data-and-services),
  including current burned-area downloads and request form for historical extracts/raw
  perimeters that are not available through web services. [2022 country report](https://data.effis.emergency.copernicus.eu/effis/reports-and-publications/annual-fire-reports/Annual_Report_2022_final_240126_print.pdf)
  confirms substantial mapped fire activity in Bosnia and Herzegovina, but country totals
  are not daily perimeters or simulator inputs.
- S-026: [Federal Hydrometeorological Institute of Bosnia and Herzegovina fire-danger page](https://fhmzbih.gov.ba/latinica/AGRO/pozar.php).
  It describes local fire-danger reporting using the Canadian Fire Weather Index and
  local weather/forecast inputs; it is not a downloadable historical hourly station feed
  and does not validate Canadian FBP fuel equations for BiH vegetation.
- S-027: [Natural Earth Admin 0 country boundaries](https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/),
  used only for first-pass geographic candidate discovery. The 1:110m boundary is too
  coarse to serve as final event-location validation.
- S-028: [EFFIS European Fuel Map technical description](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/fuels),
  [download page](https://forest-fire.emergency.copernicus.eu/applications/data-and-services)
  and [data license](https://forest-fire.emergency.copernicus.eu/about-effis/data-license).
  The 2017 layer is 250 m and uses NFFL/Anderson fuel categories. Downloaded locally and
  sampled against MedEU event polygons; EFFIS website content defaults to CC BY 4.0 unless
  a particular item says otherwise. This does not make the layer compatible with the
  current Canadian FBP Firehose build.
- S-029: [Kutchartt et al., Pan-European Fuel Map Server (2024)](https://doi.org/10.1016/j.geomat.2024.100036),
  [public map app](https://www.cirgeo.unipd.it/fire-res/app/) and
  [FirEUrisk product catalogue](https://fireurisk.eu/products/). The paper describes
  co-registered ~100 m fuel/terrain/canopy layers, including Scott–Burgan fuel classes;
  the current catalogue also lists a 1 km European fuel product and 100 m pilot products.
  Coverage of Bosnia and Herzegovina, exact exportable layers, vintage and reuse terms
  were not verified, so this remains a candidate rather than a selected input.
- S-030: [Cell2Fire-W documentation](https://fire2a.github.io/C2F-W/index.html), reviewed
  2026-10-30. Documents Canadian FBP, Scott–Burgan and KITRAL model modes in a separate
  Cell2Fire fork. It may offer an integration starting point for European fuels, but its
  RL wrapper, exact fuel crosswalk and transfer of this project's Firehose weights have
  not been tested.
- S-031: [CWFIS archived National FBP Fuel Types v2014b](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/archive/)
  and [official metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/archive/nat_fbpfuels_2014b_metadata.pdf),
  reviewed 2026-10-31. The archive is 250 m; metadata lists 2011 land cover, CanFI2000,
  ecological inputs, and NFDB/NBAC use to identify burn scars. It does not give a
  per-pixel acquisition date or a clear cutoff for burn records, so its version label
  alone cannot prove as-of-event safety for every 2014–2018 target. Its references also
  cite the 2016 NFDB Agency FireData publication. That citation does not prove that
  records through 2016 were incorporated, but it does rule out assuming that “2014b” by
  itself dates the burn-scar inputs before the TRAIN events. The general CWFIS
  download licence says Open Government Licence - Canada and specifies attribution
  [S-039]; no product-specific exception was found in the reviewed listing/metadata.
  The complete 13-member v2014b ZIP was inventoried from the local ignored raw copy
  (SHA-256 `8675bbd92d99366e46b6537d5b512017d0982e3a34f97e4bc81fb60b93c29a2b`). It
  contains the raster, metadata, legend and GIS sidecars but no separate burn-scar rule
  file. This archive inventory does not add a missing NFDB/NBAC cutoff.
- S-032: [CWFIS development directory for Canadian Forest FBP Fuel Types](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/)
  and [v20191114 metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/Canadian_Forest_FBP_Fuel_Types_Metadata_v20191114.pdf),
  reviewed 2026-10-31. The 250 m v20191114 archive is 2,680,409,561 bytes; metadata lists
  kNN Forest Inventory (2017) and NBAC. The raster itself was not downloaded or selected
  as the 2014–2018 event baseline. A 13,417-byte ZIP central-directory range enumerated
  all 170 members and exposed `docs/Burn Scar Rules.txt`, a 1,737-byte text file. That
  internal note says its burn-scar rules used an NFDB update dated 2018-07-26 for fires
  over 50 ha, gives broad 1–2 / 3–5 / 6–21? / >21-year classes and O-1/Water/Non-Fuel
  special handling, and warns that the 6–21-year M-2 interval may vary by region. The
  archive member inventory and extracted-member SHA-256 are in
  [`canfg-fuel-archive-member-review.json`](../../reports/real-fire-data/canfg-fuel-archive-member-review.json).
  This later release note does not establish the older v2014b NFDB/NBAC cutoff. The
  general CWFIS download licence says Open Government Licence - Canada and specifies
  attribution [S-039]; no product-specific exception was found in the reviewed
  listing/metadata.
- S-033: [Open Government Portal, CFFDRS FBP Fuel Types 2024, 30 m](https://open.canada.ca/data/dataset/4e66dd2f-5cd0-42fd-b82c-a430044b31de),
  reviewed 2026-10-31. Official metadata gives 2020-08-01 to 2024-04-01 coverage and lists
  SCANFI, ecozones, and NBAC inputs. This postdates the current train targets. The
  portal lists the Open Government Licence - Canada.
- S-034: [NRCan National Elevation Data Strategy](https://natural-resources.canada.ca/maps-tools-publications/satellite-elevation-air-photos/national-elevation-data-strategy),
  [MRDEM Open Government record](https://open.canada.ca/data/en/dataset/18752265-bda3-498c-a4ba-9dfe68cb98da),
  and [NRCan MRDEM overview](https://natural-resources.canada.ca/science-data/science-research/geomatics/ending-canadian-digital-elevation-model-era-new-medium-resolution-digital-elevation-model).
  Reviewed 2026-10-31. MRDEM provides 30 m terrain products; the overview says lidar
  sources incorporated into DTM were collected between 2006 and 2023. The three saved
  pilot manifests identify the MRDEM-30 DTM VRT and bilinear 30 m to 100 m conversion,
  and generated-grid hashes are recorded. Exact upstream tile/source-cell IDs, source
  raster checksum, and per-cell acquisition dates are absent. The portal lists the Open
  Government Licence - Canada; product metadata also carries Copernicus-source
  attribution/limitations. The published collection dates are not per-cell dates for
  our three pilot grids.
- S-035: [Copernicus ERA5 hourly single-level dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview),
  [ERA5-Land dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=download),
  [Open-Meteo Historical Weather API documentation](https://open-meteo.com/en/docs/historical-weather-api),
  [Open-Meteo terms](https://open-meteo.com/en/terms), and
  [service pricing/limits](https://open-meteo.com/en/pricing),
  reviewed 2026-10-31. ERA5 is hourly on a 0.25 degree grid; ERA5-Land is hourly at
  approximately 0.1 degree. Open-Meteo says ERA5-Seamless combines temperature/humidity
  from ERA5-Land with wind/solar from ERA5; its model table lists precipitation for
  ERA5 only. The three saved raw responses preserve resolved grid point, timezone/offset,
  variables/units and response hash, but not the original query coordinates/URL or exact
  model revision. The manifest's request_location is the resolved response point, not
  the original query point, so target-blind selection of these historical requests is
  unproven. Open-Meteo states API data are CC BY 4.0 with attribution, while free API
  service terms are separate.
- S-036: [CWFIS CNFDB documentation](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_documentation_EN.pdf)
  and [CWFIS FAQ](https://cwfis.cfs.nrcan.gc.ca/en/faq?wbdisable=true), reviewed 2026-10-31.
  CNFDB contains agency-provided fire locations/perimeters; documentation says the data
  are incomplete and quality varies and that access requires an End-User Agreement.
  No agreement was accepted and no event-level action/resource timeline was joined.
- S-037: [Bennett et al., 2026, W.I.S.E. assessment using CFSDS 1.1](https://doi.org/10.1071/WF26072),
  *International Journal of Wildland Fire* 35(8), WF26072, reviewed 2026-10-31.
  Methods describe building yearly fuel maps from the 2014/2019/2024 releases with the
  v20191114 burn-scar succession rules, then reclassifying same-fire pixels burned before
  day n as non-fuel for each daily simulation. Figure 2 publicly depicts the succession
  tree; this project transcribed it in `CFSDS_FUEL_VINTAGE_REVIEW.md`. The exact age
  counting convention and NRCan release artifact have not been independently checked.
  The paper's initial boundary selects day n-1 pixels adjacent to target day n and
  explicitly acknowledges future-perimeter information; do not copy that input rule into
  an unbiased agent benchmark. Methods also state that fires before 2014 were removed
  because the national fuel map was unavailable, and fires with any recorded suppression
  were removed using CNFDB because W.I.S.E. cannot model intervention. Our three saved BC
  matches do not have complete event-keyed action logs and cannot be called “no
  suppression”; two have partial public reports of activity at the candidate incident or
  complex level. The small embedded v20191114 `Burn Scar Rules.txt` was inspected
  separately [EXP-023]; the full fuel raster was not downloaded and the rules have not
  been independently executed. Exact age arithmetic and regional threshold remain
  unverified. Study data are available from the corresponding author upon reasonable
  request; there is no public code/data archive.
- S-038: [CWFIS CanFG fuel-layer-with-burn-scars legend](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/FBP_FuelLayer_wBurnScars.pdf),
  and [official v20191114 metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/Canadian_Forest_FBP_Fuel_Types_Metadata_v20191114.pdf),
  reviewed 2026-10-31. The one-page PDF lists fuel classes (including non-fuel, water,
  and urban) but does not expose the burn-scar succession decision tree. The metadata
  confirms NBAC was used to reassign fuel types in burned areas and lists supporting
  fuel-layer decision documentation; it does not give per-pixel temporal cutoffs.
- S-039: [CWFIS download-site licence](https://cwfis.cfs.nrcan.gc.ca/downloads/licence.txt),
  reviewed 2026-10-31. The site-wide notice states the Open Government Licence - Canada
  applies to downloaded data and gives the required Canadian Forest Service/CWFIS
  attribution. This resolves the prior finding that no licence statement was visible in
  individual v2014b/v20191114 files; it does not replace checking for product-specific
  exceptions or licences on separately sourced input layers.
- S-040: [Canadian National FBP Fuel Type Layer - Current Year, Open Government Portal](https://open.canada.ca/data/en/dataset/851e6a27-a250-41e6-9cd0-d7ff96455dd6),
  reviewed 2026-10-31. The official 2026 product description says national fuel maps are
  updated before fire season with burned-area and other data from the previous year and
  are scheduled for publication by 30 April. This is evidence for the current product's
  update convention, not proof of the historical v2014b map's exact cutoff.
- S-041: [FBP Fuel Layer Decision Rules](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/FBP_Fuel_Layer_Decision_Rules.pdf)
  and [FBP Fuel Layer Base Layers](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/FBP_Fuel_Layer_Base_Layers.pdf),
  reviewed 2026-10-31. These official 2018 documents describe deriving base FBP classes
  from inventory, species, land-cover and ecological layers. They are not the post-fire
  burn-scar succession crosswalk cited as a separate figure in S-037. The base-layer
  document notes that kNN NFI v1 layers are available on request and some Agriculture
  Canada land-cover inputs were under a data-sharing agreement.

- S-042: [CWFIS Satellite/NDVI data for CWFIS/fire danger rating in Canada](https://cwfis.cfs.nrcan.gc.ca/downloads/greenup/Satellite_NDVI_data_for_CWFIS_fire_danger_rating_in_Canada.pdf),
  reviewed 2026-10-31. The official note says the operational 2015 CWFIS fuel grid used
  2012 MODIS land cover and CanFI, and annual updates mapped areas burned in the last year
  as non-fuel and areas burned in the previous two years as grass. It describes a simpler
  2015 operational grid; it is not proof of the versioned v2014b burn-record cutoff and
  is not the v20191114 Figure 2 succession tree.
- S-043: [Government of Alberta Historical wildfire data: 2006–2025 catalogue](https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e),
  [official CSV](https://open.alberta.ca/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e/resource/80480824-0c50-456c-9723-f9d4fc136141/download/fp-historical-wildfire-data-2006-2025.csv),
  [official data dictionary](https://open.alberta.ca/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e/resource/1b635b8b-a937-4be4-857e-8aeef77365d2/download/fp-historical-wildfire-data-dictionary-2006-2025.pdf),
  and [Alberta wildfire maps/data landing page](https://www.alberta.ca/wildfire-maps-and-data),
  reviewed 2026-10-31. Official metadata says the fire-level dataset includes location,
  time/duration, weather, staffing and physical resources used to suppress each fire, and
  area burned; the catalogue lists Open Government Licence - Alberta. Search-indexed
  official dictionary text identifies `initial_action_by`, `ia_arrival_at_fire_date`,
  `fire_fighting_start_date` and `fire_fighting_start_size`; those fields may support a
  target-day physical-action check if a CFSDS-to-Alberta incident join is established.
  The CSV and dictionary could not be downloaded or locally inspected: the direct request
  returned HTTP 403 / a Cloudflare verification page. No Alberta events have been joined.
  An empty action field must remain unknown. Fire number, event date and perimeter/location
  must be matched before updating suppression status.
- S-044: [BC Wildfire Fire Perimeters - Historical, official ArcGIS layer](https://delivery.maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_land_and_natural_resource/MapServer/6)
  and [Open Government catalogue entry](https://open.canada.ca/data/en/dataset/22c7cb44-1463-48f7-8e47-88857f207702),
  reviewed 2026-10-31. The BC Wildfire Service layer exposes fire number/year, cause,
  reported perimeter size, fire date, GPS track date and source; the catalogue lists the
  Open Government Licence - British Columbia. A TRAIN-only point-in-polygon query matched
  each of the three saved 2018 CFSDS target centroids to exactly one 2018 BC perimeter:
  N12395, C11937 and N12413. These are strong candidate incident crosswalks, not shared
  identifiers proven against a CFSDS event key. The layer has no crew/resource/daily
  action fields, so these matches do not change suppression status from `unknown`. Query
  inputs, case/response hashes and result attributes are in
  [`cfsds-train-bc-perimeter-crosswalk.json`](../../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json).
- S-045: [BC Wildfire Service 2018 Wildfire Season Summary](https://www2.gov.bc.ca/gov/content/safety/wildfire-status/about-bcws/wildfire-history/wildfire-season-summary), reviewed 2026-10-31. The official retrospective identifies North Baezaeko (C11937) as discovered August 1, lightning-caused, and 13,433.2 ha at season end. It supports incident context and name/date cross-checking, not a daily response timeline.
- S-046: [Emergency Management BC, PECC Situation Reports #10–#11, August 16–17, 2018](https://docs.openinfo.gov.bc.ca/Response_Package_PSS-2018-86747.pdf), in the official open-information response package, reviewed 2026-10-31. Report #10's August 16 15:00 snapshot lists North Baezaeko (C11937) at 2,500 ha/0% contained and Lost Dog Complex (N12413) at 452.5 ha/out of control. Report #11, sent August 17, prints the same August 16 15:00 snapshot time but lists 4,000 ha/10% for C11937 and 706 ha/out of control for N12413. Preserve these as different report-version estimates, not a clean perimeter time series. The package contains incident status, not these fires' crew assignments, tactics, or daily action schedules; status is not proof of no suppression.
- S-047: Contemporaneous [East Kootenay wildfire updates (August 12)](https://www.e-know.ca/regions/east-kootenay/east-kootenay-wildfire-update/), [nine fires update (August 14)](https://www.e-know.ca/regions/east-kootenay/nine-wildfires-of-note-burning-in-region/), [Kimberley public update (August 16)](https://www.e-know.ca/regions/kimberley/grateful-for-information-meeting-on-fires/), and [regional update (August 18)](https://www.e-know.ca/regions/east-kootenay/meachen-creek-fire-remains-in-drainage/), reviewed 2026-10-31. These local public reports relay BC Wildfire Service updates and a City of Kimberley mayor's recap. They report target-day containment-line work at Coal Creek (candidate N12395) and complex-level Lost Dog ignition/resources on August 15 (candidate N12413), adjacent to the saved target dates. Treat them as dated public reporting, not structured dispatch records: exact per-fire allocation, hours, cell-level locations and complete daily actions are unavailable. The train-only extraction, date offsets and limits are in [`cfsds-train-bc-operational-evidence.json`](../../reports/real-fire-data/cfsds-train-bc-operational-evidence.json).
- S-048: Official [CanFG v20191114 directory listing](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/), [FBP Fuel Layer Decision Rules PDF](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/FBP_Fuel_Layer_Decision_Rules.pdf), and [FBP Fuel Layer with Burn Scars legend](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/FBP_FuelLayer_wBurnScars.pdf), reviewed 2026-10-31. The official 2.68 GB ZIP central directory has now been read without downloading the raster. It contains `docs/Burn Scar Rules.txt`, which specifies broad fire-age classes, a 2018-07-26 NFDB input date for fires over 50 ha, O-1/Water/Non-Fuel special handling, and a region-dependent M-2 threshold. The archive's `FBP_Fuel_Layer_Decision_Rules.pdf` and included R classifier concern baseline FBP assignment, not the age-succession process; the burn-scar PDF is a legend. The age note corroborates W.I.S.E. Figure 2 [S-037], but does not define exact date arithmetic or the regional boundary and does not prove the v2014b cutoff. Full member names, byte ranges and hashes are in the [archive review receipt](../../reports/real-fire-data/canfg-fuel-archive-member-review.json).
- S-049: NRCan [CanElevation–MRDEM Product Specifications, edition 1.2](https://download-telecharger.services.geo.ca/pub/elevation/dem_mne/MRDEM_MNEMR/CanElevation-MRDEM-Product-Specifications.pdf), the public [MRDEM-30 source-class COG](https://canelevation-dem.s3.ca-central-1.amazonaws.com/mrdem-30/mrdem-30-source.tif), NRCan [National Elevation Data Strategy](https://natural-resources.canada.ca/maps-tools-publications/satellite-elevation-air-photos/national-elevation-data-strategy), and Open-Meteo [Historical Weather API documentation](https://open-meteo.com/en/docs/historical-weather-api), reviewed 2026-10-31. MRDEM source codes identify adjusted Copernicus GLO-30 (1), blended area (5), or HRDEM Mosaic (10). Bounded 30 m source-class reads over each of the three saved 2018 TRAIN grids returned 4,489/4,489 pixels as code 1. NRCan documents the GLO-30 source collection as 2011–2015, but the current source-class asset is not the saved DTM source bytes and does not expose an exact acquisition date per pixel. Fresh Open-Meteo ERA5-Seamless queries at reconstructed target-blind pre-target-front centroids resolve to the same coarse grid points as legacy manifests, but temperature changes in all 24 target-day hours and humidity in 1–6 hours; wind and precipitation match. The cause of those weather changes is unknown. Exact query URLs and small response snapshots are pinned in [`cfsds-train-terrain-weather-provenance.json`](../../reports/real-fire-data/cfsds-train-terrain-weather-provenance.json) and `reports/real-fire-data/weather-snapshots/`. The legacy original query coordinates remain unknown; the old FireCases are not updated or reclassified as target-blind.
- S-050: Official [CWFIS FAQ](https://cwfis.cfs.nrcan.gc.ca/en/faq?wbdisable=true), [NBAC 1972–2024 metadata v20250506](https://cwfis.cfs.nrcan.gc.ca/downloads/nbac/NBAC_1972to2024_20250506_shp_metadata.pdf), and [CWFIS NFDB polygon download directory](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/), reviewed 2026-10-31. NRCan describes NBAC as an annually compiled burned-area composite from agency and satellite sources, with `YEAR`, agency start/end dates, source/acquisition metadata, and retrospective edits across prior years; v20250506 added/updated fires including 1972–1985 and removed duplicate polygons from consecutive years. This makes NBAC a useful candidate for reconstructing prior-fire geography, but a current retrospective release is not a frozen as-of-target snapshot. The current NFDB polygon ZIP is hundreds of MB and requires an End-User Agreement; it was not downloaded. Neither product contains the complete daily suppression action history required to label a case as untreated.
- S-051: [Benoit et al. 2026, ERA5-FWI-SN methods and validation](https://doi.org/10.5194/essd-18-5995-2026), [Borealis ERA5-FWI-SN dataset, DOI 10.5683/SP3/4B18XZ](https://doi.org/10.5683/SP3/4B18XZ), and the [Cell2Fire repository/documentation](https://github.com/cell2fire/Cell2Fire), reviewed 2026-10-31. ERA5-FWI-SN v2 provides the six Canadian FWI components as daily values on a 0.25-degree grid calculated with local solar-noon ERA5 meteorology; the paper reports median correlation 0.81 against CWFIS station values for 2015–2024 and notes smoothed extremes. Borealis lists CC BY 4.0. The study inspected and checksum-verified only the six 2018 NetCDF files. Cell2Fire's weather input is hourly; the tested mapping repeats each dated daily FWI value over that day's 24 hourly rows while retaining hourly temperature, humidity, wind and precipitation separately. Three paired TRAIN-only replays changed only the six FWI columns: two final predicted masks did not change and one had three fewer new 100 m cells; all three still touched the 20×20 crop edge. This closes a reproducible daily-FWI source path for the diagnostic copies, not hourly FWI observation, weather calibration, physical validation, fuel vintage, or suppression gates. See [audit values](../../reports/real-fire-data/era5-fwi-sn-2018-pilot-comparison.json), [paired replay receipt](../../reports/real-fire-data/era5-fwi-sn-2018-weather-replay-comparison.json), and [EXP-025](EXPERIMENT_LOG.md#exp-025--era5-fwi-sn-weather-source-paired-train-replays-2026-10-31).
- S-052: Official [Alberta Historical Wildfires Data Service](https://geospatial.alberta.ca/mimas/rest/services/wildfire/historical_wildfires_data/FeatureServer) and its [8-years-prior point layer schema](https://geospatial.alberta.ca/mimas/rest/services/wildfire/historical_wildfires_data/FeatureServer/8), reviewed 2026-10-31. The provincial REST service describes historical fire-location and perimeter layers for roughly the preceding ten years. The inspected point-layer schema exposes incident number/year, status and status date, area estimate, cause and responsible area; it does not expose the Alberta fire-level dataset's initial-action arrival, physical-firefighting start time, or resource fields. This spatial service can help identify incidents or show reported status but cannot establish that a target day had no suppression. No feature records were downloaded or joined to CFSDS. The service page identifies Government of Alberta copyright; no product-specific reuse terms were verified for this read-only schema inspection.
- S-053: Dotter, [BurnMD: A Fire Projection and Mitigation Modeling Dataset](https://www.climatechange.ai/papers/iclr2023/19), ICLR 2023 Climate Change AI workshop, [paper PDF](https://s3.us-east-1.amazonaws.com/climate-change-ai/papers/iclr2023/19/paper.pdf), reviewed 2026-11-01. The paper describes 308 western-US medium fires from 2018–2021 with perimeter and mitigation-line data. It describes estimated per-coordinate line times derived from a final time anchor, assumed hand/dozer production rates, and fuel/topography; it assumes a 20-person hand crew and D6C dozer. It also discusses missing/incorrect perimeter times, validation with MODIS/VIIRS, absent crew/equipment counts, and weather as a planned future field. The paper's method is a starting point, not proof that every distributed event file contains usable timestamp values.
- S-054: [MITRE BurnMD public repository and archive](https://github.com/mitrefireline/burnmd), inspected 2026-11-01. The Git LFS object is 362,131,110 bytes; its SHA-256 was verified locally. The repo includes an Apache-2.0 `LICENSE`, but no separate data license or data-specific reuse statement was found in the repo README (two-line hosting description), archive members, or inspected paper page. Treat the archive's data reuse/redistribution license as unresolved; do not commit or redistribute raw or geometry-derived data until checked. MITRE site `https://fireline.mitre.org/burnmd` returned 502 in the web review; the GitHub LFS asset is an accessible official-hosted alternative.
- S-055: MITRE [SimFire source](https://github.com/mitrefireline/simfire), [official docs](https://mitrefireline.github.io/simfire/), and package metadata, reviewed 2026-11-01. Source identifies version 2.0.1, Apache-2.0 software license, and Python `~3.9`; it supports Rothermel-based spread, LANDFIRE operational fuel/topography, mitigation maps, rendering, GIF and spread-graph output. Its software license is separate from data licences. The 2023 paper reports a LANDFIRE 2019 landscape near Mineral Fire; the current official product-version table marks LF 2019 Limited as archived and available through the help desk. This example does not itself establish historical-fire predictive validity.
- S-056: MITRE [SimHarness repository](https://github.com/mitrefireline/simharness), its [2023 SimFire/SimHarness paper](https://arxiv.org/abs/2311.15925) and [workshop PDF](https://ccai-papers.s3.us-east-1.amazonaws.com/neurips2023/31/paper.pdf), reviewed 2026-11-01. SimHarness trains RLlib policies against SimFire and supports movement plus interaction actions such as fireline, wetline, and scratchline. Its README states it was tested on Ubuntu 18.04/Python 3.9.18. The paper's Mineral-area demonstration uses a 128×128 grid, 30 m pixels, LANDFIRE 2019 data and random ignition scenarios; it says further detailed simulator verification/validation remained future work. The code/action model is a promising match, not an already verified project environment.
- S-057: [MITRE BurnMD Git LFS object](https://media.githubusercontent.com/media/mitrefireline/burnmd/main/BurnMD.zip) and [repository pointer](https://github.com/mitrefireline/burnmd/blob/main/BurnMD.zip), inspected 2026-11-01. The downloaded 362,131,110-byte archive SHA-256 exactly matches the official pointer. A ZIP inventory and Mineral-only case audit are recorded in project reports; the archive itself and derived geometry stay out of Git. The ZIP contains no member named as a license, notice, README or citation, so data reuse terms remain unresolved.
- S-058: [MITRE SimFire pinned source commit](https://github.com/mitrefireline/simfire/tree/04905b19fe8c10dc08d64faddd00303e0561bb66), run 2026-11-01. This is package version 2.0.1 and the exact source in the local ignored checkout. The isolated macOS ARM64/Python 3.9.25 environment completed a 30-minute functional-config smoke and emitted a GIF, final-state PNG and receipt. It is not a BurnMD event, RL policy, training run or physical validation; SimHarness/RLlib was not installed.
- S-059: The [BurnMD paper's line timestamp method](https://s3.us-east-1.amazonaws.com/climate-change-ai/papers/iclr2023/19/paper.pdf), reviewed against the local Mineral archive 2026-11-01. The paper estimates timestamps for points along a completed mitigation line from a final line-time anchor, assumed hand/dozer production rates, and LANDFIRE fuel/topography. It describes assumptions of a 20-person hand crew and D6C dozer. In the distributed Mineral line layer, `LineDateTi` is null for all 249 records and the `Mitigation` per-vertex list is empty for all 249. `CreateDate` is present but denotes source-feature creation, not a verified construction time. See [case audit](../../reports/real-fire-data/mineral-case-audit.json) and [EXP-029](EXPERIMENT_LOG.md#exp-029--burnmd-mineral-case-and-landfire-api-compatibility-audit-2026-11-01).
- S-060: Official [LANDFIRE Product Service User Guide](https://lfps.usgs.gov/LFProductsServiceUserGuide.pdf), [LFPS API schema](https://lfps.usgs.gov/docs/api), [current API product catalog](https://lfps.usgs.gov/api/products), and [product version comparison](https://landfire.gov/data/comparison-table), reviewed 2026-11-01. The guide documents the 2025 service change to `/api/job/submit`, required requester email, job status and output URL. The live `/api/healthCheck` returned success. The current product catalog lists `LF2016_FBFM13` and `LF2020_Elev` but not LF2019 FBFM13; the official comparison table marks LF 2019 Limited archived and says archived versions are available through the help desk. The new project-owned adapter's dry run uses the current service schema; no real raster job was submitted because no user email was provided.
- S-061: [SimFire source](https://github.com/mitrefireline/simfire/tree/04905b19fe8c10dc08d64faddd00303e0561bb66), [landfire 0.5.0 on PyPI](https://pypi.org/project/landfire/0.5.0/), and official [LANDFIRE API schema](https://lfps.usgs.gov/docs/api), reviewed 2026-11-01. SimFire's isolated environment includes `landfire==0.5.0` (published in 2023) and calls the pre-migration `/arcgis/rest/.../submitJob` endpoint. A live request to that operation returned HTML instead of JSON and caused the old client to fail parsing the response. This is an integration-version break, not a failure of the current public LANDFIRE health endpoint. The earlier `scripts/prepare_mineral_landfire.py` path through the newer job API was not used for this smoke. A separate public ImageServer/exportImage path fetched and validated small real rasters, then the project bridge loaded them into SimFire; S-065/EXP-033 document that working path. SimFire's own legacy LANDFIRE downloader and Mineral historical load remain unverified.
- S-062: USDA Forest Service official [FPA-FOD current occurrence service](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0), [current layer metadata](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0/metadata?format=html), and versioned [Research Data Archive record DOI 10.2737/RDS-2013-0009.7](https://doi.org/10.2737/RDS-2013-0009.7), reviewed 2026-11-01. Current service describes the seventh edition (sixth update) covering 1992–2024 with about 2.66 million point incidents and fields for discovery date/time, final area, coordinates, cause and record identifiers. Metadata says source locations are at least as precise as a PLSS section (one square mile), not necessarily exact ignition GPS. It includes IDs that can link to large-fire perimeters and incident reporting products. Use the versioned archive for a frozen cohort; current service may update. The current edition's reuse statement was checked separately in S-064.
- S-064: USFS Research Data Archive's versioned [FPA-FOD 7th Edition record](https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.7) and the [current occurrence-service layer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0), checked 2026-11-01. The archive page identifies release `FPA_FOD_20260615`, says the data may be used without additional permissions or fees, and requests citation to Short (2026), DOI 10.2737/RDS-2013-0009.7. A one-record service query retrieved the 2021 Dixie Fire (`FOD_ID=401019270`, `FPA_ID=INF-2021-CABTU-009205`, `MTBS_ID=CA3987612137920210714`): reported discovery date 2021-07-13, HHMM `1615` with timezone not assigned here, reported size 963,309 acres, and a point returned in EPSG:4326. The event-specific location accuracy is not supplied, so the publication's PLSS-section precision caveat remains. The small source snapshot and candidate scenario are in [`fpa-fod-dixie-2021-source.geojson`](../../reports/real-fire-data/fpa-fod-dixie-2021-source.geojson) and [`simfire-fpa-fod-401019270-dixie-candidate.json`](../../data/manifests/simfire-fpa-fod-401019270-dixie-candidate.json). This is an adapter fixture only; the locally cached fuel/terrain/weather data remain uncommitted and do not make it a training case.
- S-065: Official LANDFIRE [LF2016 FBFM13 CONUS ImageServer](https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2016/LF2016_FBFM13_CONUS/ImageServer), [LF2020 Elevation CONUS ImageServer](https://lfps.usgs.gov/arcgis/rest/services/Landfire_Topo/LF2020_Elev_CONUS/ImageServer), and Esri [exportImage REST documentation](https://developers.arcgis.com/rest/services-reference/enterprise/export-image/), checked and queried 2026-11-01. Both service metadata records use one signed-16-bit band in EPSG:5070; `scripts/fetch_simfire_real_inputs.py` requests nearest-neighbor 128×128 windows in the event UTM CRS (EPSG:32610), 30 m cells. The downloaded files pass shape, CRS, bounds, no-NoData and value checks. LF2016 fuel is pre-event for Dixie but five years old; it is a candidate landscape, not a 2021 field inventory. The input hashes and exact projected bounds are in the [Dixie real-input receipt](../../reports/real-fire-data/simfire-dixie-real-input-smoke/receipt.json); raster files remain local in ignored `.local/`.
- S-066: Open-Meteo [Historical Weather API documentation](https://open-meteo.com/en/docs/historical-weather-api) and the [archive API](https://archive-api.open-meteo.com/v1/archive), checked and queried 2026-11-01. The Dixie date query requests 24 hourly ERA5 values for temperature, relative humidity, 10 m wind speed/direction and precipitation at the FPA-FOD coordinate, stored in UTC. The documentation lists ERA5 at 0.25° (~25 km) hourly resolution and notes that reanalysis values are model estimates informed by observations. The fetched JSON SHA-256 is recorded in the scenario card and local input receipt. The series is context only: HHMM timezone is unresolved, 10 m wind is not SimFire's midflame wind, and relative humidity is not dead-fuel moisture.
- S-063: Gerard, Zhao & Sullivan, [WildfireSpreadTS NeurIPS 2023 Datasets and Benchmarks paper](https://papers.nips.cc/paper_files/paper/2023/file/ebd545176bdaa9cd5d45954947bd74b7-Paper-Datasets_and_Benchmarks.pdf), [Zenodo v1.0 record](https://zenodo.org/records/8006177), and [author loader repository](https://github.com/SebastianGer/WildfireSpreadTS), reviewed 2026-11-01. The paper states the full dataset is CC BY 4.0 and consists of 607 US fires / 13,607 multi-modal daily images across 2018–2021. The complete GeoTIFF ZIP is 48,359,369,821 bytes (48.4 GB), so it is not suitable for the current nearly-full local disk or as the fastest SimFire input path. It is a strong alternative for a separate historical-spread prediction track; it does not provide firefighting line actions and is not a drop-in SimFire raster/weather case.
- S-067: USDA Forest Service [FPA-FOD current occurrence service](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceCurrentEdition_01/MapServer/0), versioned [FPA-FOD archive record](https://www.fs.usda.gov/rds/archive/catalog/RDS-2013-0009.7), and the saved cohort query snapshots in [`fpa-fod-simfire-cohort-v2`](../../reports/real-fire-data/fpa-fod-simfire-cohort-v2/), queried 2026-11-01. The first cohort selected 20 cases in each of 2018, 2019, 2023 and 2024 from annual eligible pools of 146, 62, 56 and 109. Selection was stable SHA-256 rank with preference for distinct states; require >=5,000 reported acres, date, coordinates and MTBS ID for optional display. Result is 40/20/20 whole-incident, year-separated train/validation/test. The selection is a screened western-US large-fire cohort, not a random national sample. Each source point is an incident reference with unknown case-specific GPS precision; the point-to-burnable-cell rule is recorded separately. FPA-FOD final size/perimeter is not used as a training target.
- S-068: Official LANDFIRE [LF2022 product page](https://landfire.gov/data/lf2022), [LF2016 FBFM13 ImageServer](https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2016/LF2016_FBFM13_CONUS/ImageServer), [LF2022 FBFM13 ImageServer](https://lfps.usgs.gov/arcgis/rest/services/Landfire_LF2022/LF2022_FBFM13_CONUS/ImageServer), and [LF2020 elevation ImageServer](https://lfps.usgs.gov/arcgis/rest/services/Landfire_Topo/LF2020_Elev_CONUS/ImageServer), queried 2026-11-01. The project fetched LF2016 FBFM13 for 2018–2019 cases, LF2022 FBFM13 for 2023–2024 cases, and LF2020 elevation for all 80. Each 128×128 30 m GeoTIFF was checked for CRS, bounds, dimensions, NoData, supported fuel classes and SHA-256. These releases predate the selected events but are not per-event field surveys; LF2022 includes disturbance information through its product vintage and should not be described as event-day vegetation truth. Raw raster files remain ignored under `.local/simfire-cohort-v2/`; provenance and receipts are committed.
- S-069: Open-Meteo [Historical Weather API documentation](https://open-meteo.com/en/docs/historical-weather-api) and [archive endpoint](https://archive-api.open-meteo.com/v1/archive), checked 2026-11-01. The prior development-only Dixie case has one 24-hour ERA5 response. An exact 2018-07-21 cohort query failed from the local runtime with DNS error `Could not resolve host: archive-api.open-meteo.com`; the web access tool also could not open the endpoint. This records a retrieval limitation for that route, not a data-provider outage; the project subsequently acquired daily gridMET context for all cohort cases (S-071). ERA5 10 m wind must not be renamed midflame wind, air relative humidity must not be renamed fuel moisture, and FPA-FOD discovery time zone remains unresolved.
- S-070: Official [Stable-Baselines3 2.7.1 changelog](https://stable-baselines3.readthedocs.io/en/v2.7.1/misc/changelog.html), [Gymnasium 1.1.1 package metadata](https://pypi.org/project/gymnasium/1.1.1/), and installed package freeze [`simfire-rl-macos-arm64-py39.freeze.txt`](../../requirements/simfire-rl-macos-arm64-py39.freeze.txt), checked 2026-11-01. The local Python 3.9.25 environment pins PyTorch 2.3.1, Gymnasium 1.1.1, Stable-Baselines3 2.7.1 and sb3-contrib 2.7.1. The registered environment's smoke initializes MaskablePPO and predicts a legal action; no learning call was made and no policy checkpoint is produced. This exact freeze is a macOS ARM64 environment, not a portable cross-platform lock.
- S-071: Climatology Lab [gridMET description and limitations](https://www.climatologylab.org/gridmet.html), NSF NCAR GDEX [dataset d761426](https://gdex.ucar.edu/datasets/d761426/), and its [THREDDS NetCDF Subset Service](https://tds.gdex.ucar.edu/thredds/ncss/grid/files/d761426/), reviewed 2026-11-01. gridMET supplies daily CONUS surface-weather grids at about 4 km. Its documented variables include temperature, precipitation, relative humidity, wind and NFDRS model-G fire-danger/fuel indicators. It is spatially interpolated and will miss sub-grid microclimates; its wind source fields are inherited from coarser NARR/NLDAS-2 data; the nominal day is midnight-to-midnight Mountain Standard Time (UTC-7). GDEX lists DOI 10.5065/FDBC-FV90, CC BY 4.0, and a temporal range through 2025-12-31. The project queries a nearest grid-cell/day value at each FPA-FOD reported point and saves the exact provider variable, unit, sample-cell coordinates and URL. These are daily environmental context, not hourly ignition-time observations.
- S-072: Official NWCG [midflame-wind guidance](https://www.nwcg.gov/course/ffm/fire-behavior/firefighter-math-82-midflame-windspeed), [surface-to-midflame wind estimation](https://www.nwcg.gov/publications/pms437/weather/estimating-winds-for-fire-behavior), and [dead-fuel moisture overview](https://www.nwcg.gov/publications/pms425-1/11-weather-and-fuel-moisture), plus the pinned [SimFire configuration documentation](https://mitrefireline.github.io/simfire/config.html) and source at commit `04905b19fe8c10dc08d64faddd00303e0561bb66`, reviewed 2026-11-01. SimFire expects wind at midflame height and fuel moisture; its user-facing simple-wind config accepts mph and degrees clockwise from north. NWCG treats conversion from reference surface wind to midflame wind as dependent on sheltering/fuel-bed conditions; dead-fuel moisture depends on fuel size/time lag and weather history, so relative humidity or 100-hour moisture is not automatically equivalent to SimFire's single moisture input. This supports keeping weather in an explicit candidate/context layer until a project mapping is chosen and sensitivity recorded.
- S-073: MITRE [SimFire configuration documentation](https://mitrefireline.github.io/simfire/config.html) and [fire-manager API documentation](https://mitrefireline.github.io/simfire/autoapi/simfire/game/managers/fire/index.html), reviewed 2026-11-01 against pinned source commit `04905b19fe8c10dc08d64faddd00303e0561bb66`. SimFire defines `max_fire_duration` as the maximum number of update frames a single pixel remains on fire; `update_rate` defines minutes per frame. The project uses a one-minute update and sets a 15-frame duration for 30 m cells after the stock four-frame value ended a sample episode before slow cell-to-cell spread completed. The 15-frame setting is an explicit project engineering choice and has not been physically calibrated.
- S-074: Magstadt et al., [daily NIROPS fire-perimeter progression dataset, v2](https://data.mendeley.com/datasets/95rj5d379g/2), [USDA Forest Service record](https://research.fs.usda.gov/treesearch/81275), reviewed 2026-11-02. The v2 record describes 12,705 infrared perimeter observations across 737 fires in USFS Regions 1–6 from June 2020–November 2024, with UTC timestamps, EPSG:4326 geometry and at least three survey days per included fire; the record lists CC BY 4.0. It says missing/inconsistent acquisition times may be estimated from filenames, metadata and supplementary maps. The v2 outer archive size was verified by HTTP byte-range metadata as 1,735,431,121 bytes; its raw `NIROPS_2020_2024_R1_R6.zip` geometry member is listed as 1.29 GB. Only the 78,086,022-byte `Area_Progression_TimeSeries.zip` (709 PNG area-over-time charts) and 19.1 KB author-code member were downloaded locally; no raw perimeter geometry archive was downloaded. An exact incident-code/state/name screen found 8 matches among the frozen 20-case 2023 VALIDATION cohort; three extra name/state matches were rejected because the official incident codes differ. One Hayden chart was visually reviewed and appears consistent with FPA-FOD's reported area, but is not a spatial validation. The article's old NIFC `/public/incident_specific_data` root returned 404 when opened on 2026-11-02; the current path/authentication change is documented separately in S-077. NIROPS is selectively tasked, flights can be irregular or partial, and the dataset does not supply an untreated counterfactual or complete response history. It remains a promising comparison source, not physical validation evidence. See [crosswalk receipt](../../reports/real-fire-data/nirops-validation-id-crosswalk-20261102.json) and [physical validation gate](SIMFIRE_PHYSICAL_VALIDATION_GATE.md); all 2024 TEST geometries remain closed.
- S-075: MITRE [SimFire repository](https://github.com/mitrefireline/simfire), [SimFire configuration documentation](https://mitrefireline.github.io/simfire/config.html), and [SimFire/SimHarness paper](https://arxiv.org/abs/2311.15925), reviewed 2026-11-02. The paper's demonstration used SimHarness with DQN and included an unmitigated final fire map in the agent observation; it reports detailed SimFire/Rothermel validation against other models as future work. The current project does not copy the future-map observation and uses MaskablePPO in its different one-cell-action adapter. The paper supports SimFire as a configurable research environment but is not a validation certificate or a direct training recipe for this project.
- S-076: USDA Forest Service [2023 Fire Perimeter layer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/30), [Hayden feature 8040665](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/30/8040665), reviewed 2026-11-02. The layer describes daily and final mapped fire perimeters associated with Forest Service fire records/lands. An exact Hayden query returned one `Final Wildfire Perimeter` record (`2023-IDSCF-023084`) with 24,706 total acres and 24,730.34 GIS acres. Its numeric `perimeterdatetime` is 2023-08-30 22:52 UTC if interpreted as UTC, while its comment says a 22:52 MDT flight (2023-08-31 04:52 UTC); resolve field timezone before replay. The validation geometry page was inspected but the shape was not saved locally, aligned or used for physical validation. It is a public final-perimeter route, not a daily progression series for this fire. See [screen receipt](../../reports/real-fire-data/usfs-hayden-final-perimeter-screen-20261102.json).
- S-077: NIFC [File Share access information](https://ftp.wildfire.gov/), reviewed 2026-11-02. The official landing page says that as of 2026-05-04, `/public/incident_specific_data` moved to `/protected/incident_specific_data`, with protected folders requiring FAMAuth and folder-level authorization. It separately says the public Incident Specific Maps area does not require authentication; this does not establish that historical machine-readable NIROPS perimeter archives are available there. This explains why the old raw-data root URL now returns 404 without proving the data were deleted.
- S-078: NIFC [historical maps/open-data page](https://www.nifc.gov/fire-information/maps), [WFIGS public perimeter item](https://www.arcgis.com/home/item.html?id=2140078c59714858b67feb33df4bc69e), and its [authoritative NIFC FeatureServer](https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters/FeatureServer/0), reviewed and queried 2026-11-02. The service is an ongoing, incomplete public set of approved/visible interagency fire perimeters. A names-plus-2023-date attribute query was limited to the eight exact NIROPS/VALIDATION crosswalk cases and requested no geometry. Seven had exact incident identifiers; six had a final-perimeter row, but two of those have large area mismatches (Prior: 0.1 GIS acres vs 12,833 incident acres; Gray: 200 vs 10,064). Rabbit's matching daily row has no GIS area or polygon time. Four NIFC final-area values (Hayden, Sourdough, River Road East, Pass) are close to FPA-FOD; USFS adds a matching final-area candidate for Prior and a single size-matching daily record for Bedrock. The service did not provide a multi-day geometry series for any of these cases. The attribute-only query details and per-case output are in [usfs-nifc-validation-perimeter-screen-20261102.json](../../reports/real-fire-data/usfs-nifc-validation-perimeter-screen-20261102.json).
- S-079: Esri [Feature Service Query date-time documentation](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service/), reviewed 2026-11-02, alongside the [USFS 2023 perimeter layer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/30). Esri states that a null dateFieldsTimeReference means date fields are assumed to be UTC; the USFS layer returns null and datesInUnknownTimezone=false. For Hayden and Pass, the returned numeric values decode to the same clock times printed in local MDT flight comments, which would be six hours later in UTC. The schema rule does not reveal whether the publisher entered local wall-clock values into a UTC field, so both event times remain unresolved pending source-owner clarification.
- S-080: Esri [Feature Service/Layer Query REST documentation](https://developers.arcgis.com/rest/services-reference/enterprise/query-feature-service-layer/), reviewed 2026-11-02. `returnExtentOnly=true` returns the query result's extent rather than feature geometry (and can also return the count). Used for the eight 2023 VALIDATION perimeter candidates to request only server-side bounding rectangles projected to each existing raster CRS; no perimeter vertices were returned or saved. The resulting rectangle intersections are explicitly not polygon overlap or a physical-validation metric; see [extent-only receipt](../../reports/real-fire-data/simfire-validation-perimeter-extent-screen-20261102.json).
- S-081: Official [USDA Forest Service 2023 Fire Perimeter layer](https://apps.fs.usda.gov/arcx/rest/services/EDW/EDW_FireOccurrenceAndPerimeter_01/MapServer/30) and [NIFC WFIGS Interagency Perimeters feature layer](https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters/FeatureServer/0), queried 2026-11-02 by exact feature ID for only the eight code-matched 2023 VALIDATION incidents and four alternate-service duplicates. Returned polygon coordinates were projected to each existing raster CRS, checked for ring topology, and used in memory to calculate projected area, actual polygon/map intersection, and rectangular grid footprint. Raw coordinate arrays were not saved. All eight primary shapes are valid and their planar projected areas are within 0.58% of FPA-FOD incident size; the 128×128 maps contain 4.8–26.1% of each shape. NIFC area fields for Prior and Gray conflict with polygon-derived areas. Matching USFS/NIFC shapes are publication-consistent to under 0.24 mm for four incidents, not necessarily independent measurements. No progression sequence was found in the examined public services. Repeat with `.local/simfire-venv/bin/python scripts/qc_simfire_validation_perimeters.py --overwrite`; methods and per-case values are in [polygon QA receipt](../../reports/real-fire-data/usfs-nifc-validation-perimeter-polygon-qc-20261102.json) and [figure](../../reports/real-fire-data/validation-perimeter-map-footprints-20261102.png).

[REAL_FIRE_DATASETS](REAL_FIRE_DATASETS.md) čuva preporuku, obim uzorka i nedostatke;
reports/real-fire-data/ čuva download SHA256 i provjere stvarno preuzetih fajlova.

## Format baze znanja
S-018: [Open Knowledge Format v0.2, kanonski pin](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md).
Koristimo strukturu/semantiku za repo bundle; [projektni profil i granice checkera](../../knowledge/okf-format.md).
