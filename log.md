# Promjene baze znanja

## 2026-10-30: TASK-004c adapter završen lokalno

- C++ terminal receipt izvozi cumulative affected, active front, treated IDs i named reason; Python terminal counters se usklade s C++ stanjem, uz očuvan RGB 3×20×20 / Discrete(400) / no-op -1 ugovor.
- 1-scar/2-front fixture i 12/12 Sub20 inference rollouta prošli; matrix je našao i popravio slučaj gdje tretirana pogođena ćelija ostane u C++ damage skupu, ali je grid prikaže samo kao `-1`.
- Cumulative ID-jevi i hashovi su u [adapter receiptu](reports/firehose-verification/task004c-adapter-smoke.json); 38 aplikacijskih testova, strict OKF validator, synthetic CLI smoke i `git diff --check` prolaze.
- Bez treninga ili fizičke validacije. Svi matrix runovi završili su na `weather_horizon`, pa se druge C++ terminal grane nisu integracijski izvršile. CFSDS no-action gate ostaje FAIL.
- Sljedeće: preostali TASK-015 train-only fuel-vintage/terrain/weather/suppression QC, zatim unaprijed definisani no-action replay gate i heldout freeze prije benchmarka.

## 2026-10-30: TASK-018 no-action dijagnostika završena

- Analizirani su samo postojeći train replayi `2018_747`, `2018_241` i `2018_1770` na fiksnim 30–1.440 simuliranim minutama; nema novog C++ runa ni RL treninga.
- Sva tri predviđanja dotiču rub 20×20 mreže u 34–52 minute; jedan slučaj popuni svih 400 ćelija. Dnevni CFSDS cilj ne otkriva tačan minut izgaranja, a istorijsko gašenje nije poznato, zato uzrok nije izolovan i no-action gate ostaje FAIL.
- Ispravljen je samo probe metapodatak: horizon sada broji stvarne `Weather.csv` redove. Ranijih 480 minuta bila je pogrešna vrijednost izvještaja; sa 24 reda i 60 min/red stvarni gornji horizon je 1.440 min. Stari replayi se nisu mijenjali.
- Dijagnoza: [istraživački izvještaj](docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md), [mašinski timeline/hash receipt](reports/real-fire-data/cfsds-no-action-timeline.json), [EXP-007](docs/research/EXPERIMENT_LOG.md), [ADR-017](docs/specs/DECISION_RECORDS.md).
- Provjera: 34/34 aplikacijskih testova; strict OKF validator 69 Markdown fajlova; CLI smoke je uporedio spremljeni `2018_747` rezultat s reportom; `git diff --check` čist.
- Tada sljedeće: TASK-004c adapter; dovršen je u odjeljku iznad.

## 2026-10-30: train-only CFSDS fuel QC gate

- Nova grana `research/cfsds-train-qc` zasniva se na spojenom `main` (`ea5b8a7a`); rad je u izolovanom task worktreeu.
- `scripts/audit_cfsds_train_fuel.py` i tri GIS unit testa pregledaju 20 train day-pair kandidata na dvije skale: native CFSDS 90 m i stvarni Cell2Fire 20×20/100 m grid. Report uključuje source/code SHA-256, fuel class mape, mask/area statistiku i ograničenja.
- Rezultat: 10 `PASS_FUEL_ONLY`, 10 `FAIL_FUEL_OVERLAP`, 0 processing grešaka. Sva tri postojeća no-action replay događaja prolaze samo fuel gate; to ne potvrđuje weather/terrain/suppression ili potpunu podobnost.
- Train redovi u `data/manifests/cfsds-v1_1-pilot-cohort.json` nose odgovarajući fuel-only status i link na receipt; cijela kohorta i dalje nije finalni benchmark.
- Validation/test fuel i source rasteri nisu otvoreni. Zajednički cohort manifest i crop-screen JSON sa svim split metapodacima učitani su da se izdvoje train redovi; nijedan validation/test overlay nije izračunat. Dokumentacija to precizno navodi. Nije bilo replaya, RL treninga ni kalibracije.
- [Metoda i limiti](docs/research/CFSDS_TRAIN_QC.md), [mašinski report](reports/real-fire-data/cfsds-train-fuel-qc.json), [EXP-006](docs/research/EXPERIMENT_LOG.md), [ADR-016](docs/specs/DECISION_RECORDS.md).
- Tadašnji sljedeći zadatak bio je TASK-018, a zatim TASK-004c; oba su sada završena lokalno. Aktuelni korak je preostali train-only TASK-015 input/replay gate prije benchmarka ili fine-tuninga.
- U trenutku ovog ranijeg QC unosa fokusirani geo tests: 3/3 prolazili su; verifikacija TASK-018 je zapisana iznad.

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
