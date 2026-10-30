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
| S-006 | [MITRE SimFire](https://github.com/mitrefireline/simfire), [docs](https://mitrefireline.github.io/simfire/) | alternativni Python backend; ovdje nije instaliran ni benchmarkovan |
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
- S-017: [MITRE BurnMD](https://github.com/mitrefireline/burnmd/tree/a9e423f15906bc9860be6d80b56e71e4a6ee307c),
  samo LFS metapodaci, mogući SimFire fallback; sadržaj arhive nije pregledan.
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
  ecological inputs, and NFDB/NBAC use. It does not give a per-pixel acquisition date or
  a clear cutoff for burn records, so its version label alone cannot prove as-of-event
  safety for every 2014–2018 target. No license statement was identified in the
  reviewed archive listing or metadata; confirm reuse/redistribution terms with NRCan.
- S-032: [CWFIS development directory for Canadian Forest FBP Fuel Types](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/)
  and [v20191114 metadata](https://cwfis.cfs.nrcan.gc.ca/downloads/fuels/development/Canadian_Forest_FBP_Fuel_Types/Canadian_Forest_FBP_Fuel_Types_Metadata_v20191114.pdf),
  reviewed 2026-10-31. The 250 m archive is listed at about 2 GB in a development
  directory; metadata lists kNN Forest Inventory (2017) and NBAC. The raw raster was not
  downloaded or selected as the 2014–2018 event baseline. No license statement was
  identified in the reviewed listing/metadata; confirm terms with NRCan before use.
- S-033: [Open Government Portal, CFFDRS FBP Fuel Types 2024, 30 m](https://open.canada.ca/data/dataset/4e66dd2f-5cd0-42fd-b82c-a430044b31de),
  reviewed 2026-10-31. Official metadata gives 2020-08-01 to 2024-04-01 coverage and lists
  SCANFI, ecozones, and NBAC inputs. This postdates the current train targets. The
  portal lists the Open Government Licence - Canada.
- S-034: [NRCan National Elevation Data Strategy](https://natural-resources.canada.ca/maps-tools-publications/satellite-elevation-air-photos/national-elevation-data-strategy),
  [MRDEM Open Government record](https://open.canada.ca/data/en/dataset/18752265-bda3-498c-a4ba-9dfe68cb98da),
  and [NRCan MRDEM overview](https://natural-resources.canada.ca/science-data/science-research/geomatics/ending-canadian-digital-elevation-model-era-new-medium-resolution-digital-elevation-model).
  Reviewed 2026-10-31. MRDEM provides 30 m terrain products; the overview says lidar
  sources incorporated into DTM were collected between 2006 and 2023. The portal lists
  the Open Government Licence - Canada; product metadata also carries Copernicus-source
  attribution/limitations. The source cell and acquisition date for the three saved
  pilot grids are not recorded.
- S-035: [Copernicus ERA5 hourly single-level dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview),
  [ERA5-Land dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=download),
  [Open-Meteo Historical Weather API documentation](https://open-meteo.com/en/docs/historical-weather-api),
  [Open-Meteo terms](https://open-meteo.com/en/terms), and
  [service pricing/limits](https://open-meteo.com/en/pricing),
  reviewed 2026-10-31. ERA5 is hourly on a 0.25 degree grid; ERA5-Land is hourly at
  approximately 0.1 degree. Open-Meteo says ERA5-Seamless combines temperature/humidity
  from ERA5-Land with wind/solar from ERA5. Open-Meteo states API data are CC BY 4.0
  with attribution, while free API service terms are separate. The exact variable
  lineage for each column in our saved API responses, especially precipitation, still
  needs recording.
- S-036: [CWFIS CNFDB documentation](https://cwfis.cfs.nrcan.gc.ca/downloads/nfdb/fire_poly/current_version/NFDB_documentation_EN.pdf)
  and [CWFIS FAQ](https://cwfis.cfs.nrcan.gc.ca/en/faq?wbdisable=true), reviewed 2026-10-31.
  CNFDB contains agency-provided fire locations/perimeters; documentation says the data
  are incomplete and quality varies and that access requires an End-User Agreement.
  No agreement was accepted and no event-level action/resource timeline was joined.
- S-037: [Bennett et al., 2026, W.I.S.E. assessment using CFSDS 1.1](https://doi.org/10.1071/WF26072),
  *International Journal of Wildland Fire* 35(8), WF26072, reviewed 2026-10-31.
  Methods report filtering fires with suppression from CNFDB and making annual fuel maps
  by masking previous perimeters and applying the v20191114 burn-scar succession rules.
  This is a published method reference, not a reproduction or result from this project;
  the exact event-action linkage and transfer to our simulator remain unverified.

[REAL_FIRE_DATASETS](REAL_FIRE_DATASETS.md) čuva preporuku, obim uzorka i nedostatke;
reports/real-fire-data/ čuva download SHA256 i provjere stvarno preuzetih fajlova.

## Format baze znanja
S-018: [Open Knowledge Format v0.2, kanonski pin](https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/ad30107c31c06aec8a7d5636e0d1058118604e6f/SPEC.md).
Koristimo strukturu/semantiku za repo bundle; [projektni profil i granice checkera](../../knowledge/okf-format.md).
