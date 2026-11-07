# Promjene baze znanja

## 2026-11-05: sintetički CA trening i jednokratni test (ADR-028)

- Novi CA simulator, okruženje s fizički ograničenim jedinicama i kontrafaktualna nagrada.
- PPO od nule nije prošao; imitacija + PPO je dala policy-v1, izjednačenu s heuristikom
  i jasno bolju od no-op. Na 119 stvarnih startova čuva 12% više od no-op (simulirani
  ishod). Jaz kalibracije: medijan IoU 0.27–0.30 na 48h.
- [STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md),
  [spec](docs/research/SYNTHETIC_CA_ENV.md), [izvještaji](reports/synthetic/index.md).

## 2026-11-04: koraci 5–8 (noćni samostalni rad)

- Ulazi ponovo izgrađeni i reproducirani (isti hashovi, isti WAF .01 IoU). Dijagnoza
  pada gatea i preregistrovana 3×3 mreža (ADR-023): bez prolaza; gate zamrznut kao
  `FAIL_exploratory` (ADR-024).
- Validation skoriran jednom po zapisu; free-burn stress zapis deklarisan za korake 7–8.
- ADR-025: jedinica budžeta = smjena ekipe od 20 ljudi = linija od 7 ćelija; heuristike i
  upareni benchmark. ADR-026/027: 5 seedova, 20 modela, 1,920 VALIDATION epizoda; osnovni
  PPO pobjeđuje no-op, fine-tuning po budžetu nema mjerljive koristi.
- [STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md),
  [benchmark](reports/real-fire-data/feds-simfire-policy-benchmark-v1.json),
  [odluke](docs/specs/DECISION_RECORDS.md).

## 2026-11-03: Handoff i agent upute usklađeni s ADR-022

- Ažurirani su AGENTS, Claude/Gemini/Copilot ulazi, project context, HANDOFF, README,
  backlog, code map i data/research ulazi da razlikuju data-coverage PASS od TRAIN
  no-op FAIL.
- Ispravljena je zastarjela uputa da je TASK-012/CFSDS još aktivan i da no-op kohortni
  gate tek slijedi. Stariji eksperimenti i odluke ostaju u historiji.
- Sljedeći korak je dijagnostika i ponovljeni zajednički TRAIN gate; validation rasteri
  i TEST 2024 ostaju zatvoreni do prolaza/odgovarajuće faze.

## 2026-11-03: TRAIN-only SimFire no-op screen — gate FAIL

- Osam WAF kandidata je poređeno na istih 99 TRAIN slučajeva i 396 vremenskih tačaka po kandidatu, uz no-op, persistence i fiksnu 2:1 elipsu.
- WAF .01 sa 1-min internim korakom dao je IoU .4771 (naspram .4769 na 5 min), bez rubnog kontakta; zaključak se nije promijenio.
- Nijedan kandidat nije prošao; persistence IoU=.5343, elipsa=.5308, najbolji SimFire=.4769. WAF .605 ima rubne kontakte u 61/99 slučajeva.
- Nije izabran WAF/timebase. Validation rasteri i 2024 TEST ostaju zatvoreni; benchmark PPO čeka dijagnostiku i prolaz novog TRAIN gatea.
- [Izvještaj](reports/real-fire-data/feds-simfire-train-noop-screen-v1.json), [status](docs/STATUS.md), [ADR-022](docs/specs/DECISION_RECORDS.md), [environment record](docs/research/SIMFIRE_ENVIRONMENT.md).

## 2026-11-03: TRAIN-only FEDS/SimFire PPO putanja

- Na korisnikov direktni zahtjev dodan je Gymnasium env i MaskablePPO CLI za 99 TRAIN
  slučajeva. Epizoda ima 48h/četiri 12h koraka; budžet ne prekida epizodu, no-op je uvijek
  legalan, a kumulativno opožarene ćelije ostaju šteta i kad ih SimFire prepiše linijom.
- Agent ne prima buduće FEDS obode; reward koristi samo dodatni simulator burn. Akcijski
  prostor (no-op + 8 kratkih sektorskih fireline poteza) je prototip, ne operativno
  validiran model gašenja.
- Python 3.9.25 venv package check je vraćen na PASS. Pošto je ciljni UV interpreter
  zaglavljen, `bin/python` poziva isti provjereni 3.9 runtime iz sačuvanog susjednog
  worktreea; lokalne biblioteke ostaju u aktivnom venv-u.
- Završio je 64-step CPU PPO smoke, checkpoint save/reload i završni TRAIN rollout.
  Izlaz ostaje ignorisan pod `.local/feds-ppo-smoke-waf-0.605-64steps`. WAF .605 je samo
  provisionalni smoke ulaz; nije kalibrisan. TRAIN cohort gate je naknadno dovršen i
  pao; vidi novi screening izvještaj. Validation mape i test 2024 nisu otvoreni.
- [ADR-021](docs/specs/DECISION_RECORDS.md), [environment/runbook](docs/research/SIMFIRE_ENVIRONMENT.md),
  [TRAIN env](src/wildfire_rl/feds_simfire_env.py), [CLI](scripts/train_feds_simfire.py)
  i [regresijski testovi](tests/test_feds_simfire_env.py).

## 2026-11-03: lokalni FEDS audit, širi candidate frame i SimFire runtime lock

- Checksum-verifikovane su train/validation FEDS perimetar arhive 2018/2019/2023; 2024
  test nije preuzet. Originalna kohorta lokalno daje 19/40 train i 7/20 validation, i
  dalje ispod 20/8. Širi, unaprijed spremljeni FPA screen frame daje 99/208 i 20/56 te
  119 punih FEDS 48h epizoda. Ova eksplicitna izmjena je u [ADR-018](docs/specs/DECISION_RECORDS.md).
- Dodani su local MD5 audit, checksum-aware, year-limited FEDS downloader i episode
  manifest builder. Crosswalk provjerava kompletan event time series nakon ranog
  3km matcha; 14 ciljanih testova prolazi.
- SimFire 2.0.1 pinovan je na upstream commit; Python 3.9 ARM64 freeze/setup je odvojen
  od projekta Python ≥3.11. [Environment record](docs/research/SIMFIRE_ENVIRONMENT.md).
- Active-front, 180m grid i inputi prolaze za 119 train/validation startova, a svih 99
  train slučajeva imaju checksum-verifikovane LANDFIRE rastere. Jedan 48h historijski
  Plateau no-op pilot otkriva strm WAF prag; parametar nije izabran i no-op gate ostaje
  otvoren. Sljedeće: cohort train kalibracija i persistence/elipsa prije validation.
  To nije fizička validacija; nema PPO treninga ni test pristupa.

## 2026-11-03: SimFire/FEDS podaci i pre-agent gate

- Po korisničkoj odluci novi aktivni pravac je SimFire + FPA-FOD/FEDS-CONUS, uz
  ograničeni FLE/ICS-209 post-hoc kontekst. Stari CFSDS/Cell2Fire izbor ostaje historijski.
- Napravljen je test-excluded manifest od 40 train i 20 validation požara; FEDS tražen
  prostornim HTTP Range upitima, bez preuzimanja 1.2 GB godišnjih fajlova.
- Strogi datum/tačka/3 km crosswalk traži obod u prvih 24h od `t_st`; nalazi 13/40
  train i 7/20 validation sa ≥2 uzastopna 12h FEDS stanja. Prag 20/8 pada u oba splita.
  Eksplorativnih 17/12 slučajeva koristilo je preširok vremenski kriterij i supersedovano je.
- FLE grupisani incidentni sažetak: 0/40 train, 13/20 validation. Test nije učitan.
  SimFire nije portovan, no-op replay/PPO nisu pokrenuti. Validation je deterministički
  postfiltriran iz sačuvanih kandidata; nova Zenodo provjera nije uspjela zbog DNS-a.
- [Detaljna metoda i ograničenja](docs/research/FPA_FEDS_CROSSWALK.md),
  [kombinovani JSON](reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json),
  [ADR-017](docs/specs/DECISION_RECORDS.md), [radni dnevnik](docs/WORK_LOG.md).

## 2026-10-30: CFSDS putanja izabrana i prvi stvarni C++ replay

- Po korisnikovoj uputi odabrana je Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire, jer je to najbolji fit postojećem simulatoru. Stvarni historijski rast ostaje zaseban reality-check; RL iskustvo generiše simulator.
- Preuzeto je 2002–2024 CFSDS u Git-ignorisan raw storage; source size/SHA-256 manifest je u `reports/real-fire-data/cfsds-download-manifest.json`. Geometrijski screen za 2014–2024 zadržava do pet kandidata godišnje, 44 ukupno (20 train, 9 validation, 15 test) po požar-godini. To nije iscrpan niti finalan benchmark.
- TASK-017 `InitialState.csv` adapter importuje ranije izgorjeli scar i više aktivnih ćelija. Fixture i stvarni C++ import prošli su.
- Case builder `scripts/build_cfsds_case.py` pretvara `2018_747` u 20×20/100m Firehose ulaze: FBP 2014b gorivo, MRDEM 30m, satni ERA5-Seamless weather i historical start state. Naredni dan ostaje odvojen u `truth/`, ne u agent inputu.
- Novi real-case Docker image je ponovo prošao 12/12 postojećih Sub20 smoke/inference slučajeva; svi C++ kodovi su 0, a PPO težine nepromijenjene. Receipt: `reports/firehose-verification/real-case-image-regression.json`.
- Šest no-action C++ seedova (123–128, bez treninga/intervencija) dalo je identičnu završnu mapu od 66 ha prema CFSDS cilju 15.39 ha; area-weighted IoU 0.2187; svih 6 predikcija je dodirnulo 19 rubnih ćelija modelskog prozora, dok se trajanje simulacije razlikovalo. [Seed-sweep izvještaj](reports/real-fire-data/2018_747-seed-sweep.json). Suppression status je nepoznat. Ovo je mismatch dijagnostika, ne fizikalna validacija ni dokaz politike.
- Case manifest, replay JSON, mapa i update odluka/statusa/backloga su u reports/data/docs. Dodatno pokrenuto pet seed ponavljanja; ukupno šest runova imaju isti input/final mask, dok je trajanje 206–363 simulator minute. Nema treniranja, remote objave, commit-a ili merge-a u ovom koraku.

## 2026-10-30: još dva CFSDS train replaya i fuel QC nalaz

- Pretvoreni su i pokrenuti `2018_241` i `2018_1770` s istim 20×20/100m setupom, satnim ERA5-Seamless vremenom, MRDEM 30m i `steps-before=0`. Bez akcija simulator daje 237 ha / 12.153 opaženih (IoU .0376; 400/400 ćelija zahvaćeno) i 73 ha / 12.151 ha (IoU .1361). Oba imaju po jedan seed.
- `2018_241` je ponovljen sa 20 minuta početnog simulator zagrijavanja: završni grid i mjere ostali su isti. `2018_747` seed 123 takođe je ponovljen bez zagrijavanja, uz iste 66 ha/.2187 mjere.
- Geometrijski kandidat `2014_538` nije prošao converter: bar jedna historijska scar/front/target ćelija postaje water/nonfuel pod Canadian FBP 2014b; nije pokrenut u C++.
- Ažuriran je plotting CLI da datume i event ID čita iz case manifesta. Sačuvani su novi FireCase manifesti, replay JSON-ovi, warmup poređenje, tri karte i fuel-rejection receipt. Nalaz je da se screening po geometriji mora dopuniti fuel QC, a simulator treba kalibraciju/ulaznu dijagnostiku prije RL treniranja.


## 2026-10-30: lokalni BiH FireSpread_MedEU pregled

- Skinut je FireSpread_MedEU v2 ZIP od 2.75 MB u Git-ignorisan `data/raw/` samo za prostorni screening. Presjek sa Natural Earth državnom granicom otkrio je 7 BiH kandidata: EFFIS IDs 12321, 13228, 22108, 25244, 25274, 43482, 205938. Hashovi, datumi, kvalitet i granice metode su u [spatial-screen izvještaju](reports/real-fire-data/medeu-spatial-screen.json); raw nije u Git-u.
- `205938` ima 4 dnevna koraka vrlo visoke kvalitete, ali extenta 4.14×4.18 km; `43482` je 216.87 ha, ali extent 2.56×1.71 km. Oboje prevazilazi postojeći 2×2 km agentov prozor.
- Skinuta je i EFFIS European Fuel Map 2017 (18.2 MB; 250 m; NFFL/Anderson). Overlap daje kodove 4/5/9 za `205938` i 3/5 za `43482`; ovaj format goriva nije kompatibilan direktno s trenutnim Canadian FBP buildom. Rastera, hashova, licencnih napomena i model ograničenja ima u istom [spatial-screen izvještaju](reports/real-fire-data/medeu-spatial-screen.json).
- Preporuka je uslovna: CFSDS ako zadržimo Canadian FBP/Cell2Fire; MedEU ako želimo BiH historijske slučajeve, uz izbor regionalnog fuel modela, license provjeru, potvrdu event lokacija i grid odluku.
- Ažurirani su [X/Y pipeline](docs/research/REAL_CASE_PIPELINE.md), [dataset pregled](docs/research/REAL_FIRE_DATASETS.md), `DATASET`, HANDOFF, STATUS, backlog, manifests, izvori i environment receipt. Nema simulator conversion/replay, treninga ili potvrđene fizike.

## 2026-10-30: dataset prijedlog i ponovljen environment setup

- Početni cross-dataset pregled i environment setup su zabilježeni; noviji rezultat je BiH prostorni screen opisan iznad. Aktuelna preporuka zavisi od toga da li ostajemo na Canadian FBP ili prelazimo na BiH/regionalni model.
- Dodane su odluke koje ostaju otvorene, CFSDS v1.1 istraživanje, model/scenario split ugovor i TASK-014/015/004c redoslijed.
- [Environment receipt](reports/environment-setup/README.md): Python 3.12.4 moderni venv, 26+15 testova, smokeovi i Linux ARM64 legacy image/inference; bez treninga Firehosea.
- Ponovljeni pinovani Sub20 inventar odgovara hash-manifestu; ignition 381/372 su dvije različite gorive ćelije, a Data.csv ima jedan krnji red. Nema konačnog dataset izbora ili fizikalne validacije.

## 2026-10-28: Workspace raspored

- [Runbook](knowledge/workspace-layout.md) definiše mpvi glavni klon, .worktrees i ignorisani .local prostor, uz očuvanje PR-a i dataset prioriteta.
- [Dokaz preseljenja](reports/workspace-relocation.json) čuva hash/package/test provjere i ponovljeni setup iz novog klona.

## 2026-10-28: OKF 0.2 bundle u repozitoriju

- Dodani typed koncepti, lowercase indeksi, [kontekst](knowledge/project-context.md), [mapa koda](knowledge/code-map.md) i [održavanje](knowledge/maintenance.md).
- Root [index](index.md) i [AGENTS](AGENTS.md) vode do izvora i dokaza bez vanjske baze/chat historije; mali agent ulazi dijele ista pravila.
- [OKF profil](knowledge/okf-format.md) pinova specifikaciju; zaseban checker/CI provjerava strukturu i projektne linkove, bez tvrdnje o naučnoj verifikaciji.
- [Završni receipt](reports/knowledge-validation.json) čuva 63-file provjeru, 15 knowledge testova, clean-clone rezultate i hashove; pregled i regresijske ispravke su u [REVIEW](docs/REVIEW.md).

## 2026-10-28: Dataset refinement ostaje otvoren

- Korisnik je ispravio redoslijed: [TASK-012](docs/BACKLOG.md) je prvi projektni korak, izbor i obim još nisu usaglašeni; ADR-009.
- Handoff i PR usklađeni; postojeći runtime nalazi ostaju važeći.

## 2026-10-28: Bootstrap, runtime i pregled izvora

- Sačuvani [pilot](reports/pilot/README.md), [Firehose dokazi](reports/firehose-verification/README.md) i [Dogrib/CFSDS profili](reports/real-fire-data/README.md).
- Detaljan redoslijed, komande, rulings i pregledi su u [WORK_LOG](docs/WORK_LOG.md) i [REVIEW](docs/REVIEW.md).
