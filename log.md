# Promjene baze znanja

## 2026-10-31: TRAIN fuel source-gate inventory

- Zvanični v2014b metadata navodi NFDB/NBAC za burn scars, ali ne datum snapshot-a ni cutoff; ne možemo ga proglasiti leakage-safe za TRAIN događaje.
- Zvanični CanFG v20191114 direktorij navodi Decision Rules PDF za bazno mapiranje klasa. On ne sadrži godine-od-požara succession pragove iz W.I.S.E. Figure 2; ZIP od oko 2 GB nije pregledan.
- Figure 2 ostaje javno transkribovano pravilo, ali bez potvrđene age arithmetic, special-class semantike ili executable implementation. Godišnja mapa ostaje blokirana.
- Dodani su [source-gate receipt](reports/real-fire-data/cfsds-train-fuel-source-gate.json), [S-048](docs/research/SOURCES.md), [EXP-019](docs/research/EXPERIMENT_LOG.md#exp-019--train-fuel-vintage-artifact-inventory-2026-10-31) i [ADR-029](docs/specs/DECISION_RECORDS.md#adr-029). Nema download-a/generisanja rastera ni FireCase/replay/treninga; `research_ready=false`.

## 2026-10-31: TRAIN-only BC operational evidence follow-up

- Za kandidatski BC incident N12395, Coal Creek, pronađen je javni izvještaj koji za 12. august navodi rad na containment linijama, pet komada teške mehanizacije i helikopter; taj datum se poklapa sa target datumom CFSDS `2018_1770`.
- Za N12413 / Lost Dog Complex izvještaji opisuju planirano paljenje i resurse na kompleksu dan prije `2018_747` targeta, te još jedan resursni snapshot narednog dana. Ne raspoređujemo te zbirne resurse na pojedinačni incident ili ćelije.
- Za C11937 / North Baezaeko nađen je službeni 16. august status od 2.500 ha i 0% contained, ali ne i akcioni/crew log za 15. august. Sve tri spremljene case manifest oznake ostaju `unknown` dok se ne dobije event-keyed dnevni zapis.
- Dodani su [mašinski receipt](reports/real-fire-data/cfsds-train-bc-operational-evidence.json), [S-045–S-047](docs/research/SOURCES.md), [EXP-018](docs/research/EXPERIMENT_LOG.md#exp-018--train-only-bc-operational-record-search-2026-10-31) i [ADR-028](docs/specs/DECISION_RECORDS.md#adr-028). Nema novog FireCase/replaya/treninga/heldout pregleda; `research_ready=false`.

## 2026-10-31: TRAIN-only BC historical perimeter crosswalk

- Službeni BCWS poligoni vraćaju po jedan 2018 incident za svaki od tri sačuvana target centroids: N12395, C11937 i N12413. To su prostorno/godinski kandidati, ne shared-key join.
- Perimetri su finalni, nakon target dana; korišteni samo za identifikaciju incidenta. Sloj nema resurse/akcije gašenja, pa suppression ostaje unknown. JSON receipt čuva originalne odgovore i SHA-256.
- Bez novog FireCase/replaya/treninga. Vidi [ADR-027](docs/specs/DECISION_RECORDS.md#adr-027), [EXP-017](docs/research/EXPERIMENT_LOG.md#exp-017--train-only-bc-historical-perimeter-crosswalk-2026-10-31) i [receipt](reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json).

## 2026-10-31: TRAIN fuel-tree and input-lineage follow-up

- Ispravljen raniji nalaz: W.I.S.E. Figure 2 je javna i succession tree je transkribovano, ali datumsku semantiku i specijalne klase treba potvrditi; v2014b cutoff ostaje nepoznat.
- Pronađen je službeni Alberta 2006–2025 fire-level suppression dataset; direktni CSV download vraća HTTP 403, pa nema event join-a. Osvježeni su DEM/weather lineage nalazi: nedostaju izvorni tile/cell detalji i originalna vremenska query lokacija.
- Nema novog rasterskog ulaza, FireCase-a, replaya ni treninga. **research_ready=false**. Vidi [ADR-026](docs/specs/DECISION_RECORDS.md#adr-026), [EXP-016](docs/research/EXPERIMENT_LOG.md#exp-016--train-fuel-tree-correction-and-external-input-lineage-audit-2026-10-31) i [handoff](docs/NEXT_SESSION.md).

## 2026-10-31: TASK-015 explicit NF historical-scar importer contract

- C++ import sada podržava poseban `scar_nf` zapis samo uz eksplicitnu provenance tvrdnju i tačnu upstream `NF` klasu; scar ostaje u cumulative šteti, ali nikad nije aktivni front ili gorivo za širenje. Neispravni `burnt`/`burning`/mismatch slučajevi su odbijeni.
- Puni no-policy sintetički Sub20 rollout i tri negativna fixturea prošli su u offline, pinovanom ARM64 Docker runtimeu; vidi [receipt](reports/firehose-verification/nonfuel-initial-scar-contract.json), [ADR-025](docs/specs/DECISION_RECORDS.md#adr-025) i [EXP-015](docs/research/EXPERIMENT_LOG.md#exp-015--explicit-nonfuel-historical-scar-importer-contract-2026-10-31).
- CFSDS builder ostaje zatvoren za nonfuel scar dok annual fuel vintage i succession nisu dokazani. Nema CFSDS replaya, fizikalne validacije ili treniranja. Sljedeće: preostali fuel/source i DEM/weather/suppression provenance, zatim preregistrovani no-action gate.

## 2026-10-31: TRAIN-only FBP fuel-vintage source review

- Službeni v2014b metadata ne navodi cutoff za NFDB/NBAC burn scars; 2014b ostaje samo za reprodukciju već spremljenih slučajeva. v20191114/2024/2026 nisu odabrani kao TRAIN vintage.
- CWFIS download-site licenca je dokumentovana kao Open Government Licence - Canada uz CFS atribuciju. Službeni 2018 baseline FBP klasifikacioni PDF je razdvojen od post-fire succession stabla koje navodi W.I.S.E. rad.
- Nije preuzet niti napravljen novi raster. Dodani su [source review](docs/research/CFSDS_FUEL_VINTAGE_REVIEW.md), EXP-014 i ADR-024; ažurirani su input QC, status, backlog, handoff i navigacija.
- Tadašnji naredni korak bio je importer/cumulative-damage ugovor za historical scar na NF ćeliji; završen je u EXP-015/ADR-025. Mapiranje ostaje blokirano dok se ne pribave pouzdani cutoff i succession rules.

## 2026-10-31: Full TRAIN target-independent CFSDS day-pair screen

- Pregledano je svih 1.301 TRAIN fire arrival rastera pravilom koje ne koristi target-day uslove: najraniji dan sa najmanje tri validna 90 m piksela je input, sljedeći kalendarski dan target.
- Sačuvano je 1.010 parova s mapiranim target pikselima i 291 bez njih; sva članstva ostaju u screen-u. Uklanjanje target i kasnijih oznaka nije promijenilo izabrani input DOY.
- Na 20×20/100 m prozor je dostupan za 1.295 slučajeva; target ima makar jedan piksel u 945/1.010 prozora; medijalni capture je 36.71% za N=1.008 validnih target/crop parova. Širi prozori su bolji među onima koji stanu, ali mnogi rasteri su premali.
- Nijedan grid nije usvojen. Dodani su [metod i izvještaj](docs/research/CFSDS_FULL_DAY_PAIR_SCREEN.md), [JSON receipt](reports/real-fire-data/cfsds-train-full-day-pair-screen.json), [case/domain CSV](reports/real-fire-data/cfsds-train-full-day-pair-screen.csv), ADR-023 i EXP-013.
- Nema FireCase-a, C++ replaya, fuel/terrain/weather završetka, benchmarka ili treninga. Sljedeće: FBP vintage/source i non-fuel scar importer gateovi, zatim nedostajuća provenance/suppression i mali preregistrovani train replay.

## 2026-10-31: TASK-015 TRAIN spatial feasibility audit

- Isti 25 TRAIN parova je target-blind centriran prema day n−1 na 2, 3, 4 i 6 km; dodatno poređeno 40×40/100 m. Day-n coverage je mjeren tek nakon crop izbora.
- Na 2 km samo 4/25 prozora sadrže target pixel (median 0%); na približno 4 km 19/25 ali median capture 1.95%; na 6 km median 15.31% uz dvije premale source slike. Nijedan novi grid nije usvojen.
- Uočena protokolska ograda: raniji parovi zahtijevaju day-n summary i pozitivnu firearea, pa day-pair membership nije dokazano potpuno outcome-independent.
- [ADR-022](docs/specs/DECISION_RECORDS.md#adr-022), [EXP-012](docs/research/EXPERIMENT_LOG.md#exp-012--train-only-target-blind-spatial-domain-feasibility-2026-10-31), [metod](docs/research/CFSDS_SPATIAL_FEASIBILITY.md), [audit receipt](reports/real-fire-data/cfsds-train-spatial-feasibility.json).
- Provjera: puni testovi 61/61, strict OKF 71 Markdown fajl, synthetic CLI smoke i git diff check prolaze. Nema resamplinga inputa, FireCase builda, replaya, treninga ili heldout rastera. Sljedeće: preregistrovati day-pair pravilo pa screenirati cijeli TRAIN prostor.

## 2026-10-31: TASK-015 target-blind početno stanje i train screen

- Početni crop/front sada koriste samo pre-target podatke: crop se centrira na day n−1 centroid, sigurni unutrašnji n−1 pikseli su aktivni front, a rub izreza ostaje scar. Builder odbija stare screenove/candidate redove bez eksplicitnih target-blind oznaka; screen CLI je train-only i odbija heldout godine.
- TRAIN `2018_747` invariance proof: promjena svih 19 target piksela nije promijenila crop, 20×20 scar/front niti `InitialState.csv`; target truth se promijenio. To je uslovni proof za fiksni event/day par, ne validacija dnevnog fronta ili cohort-day odabira.
- Screen shortlist od 25 TRAIN kandidata ima target pixel u samo 4 prozora (median capture 0; max 1.0402%). Ovo je naknadna dijagnostika, ne izborni kriterij; fiksni 2×2 km reality-check prostor ostaje upitan. Nema replaya, case rebuilda ni treninga.
- [ADR-021](docs/specs/DECISION_RECORDS.md#adr-021), [EXP-011](docs/research/EXPERIMENT_LOG.md#exp-011--train-only-target-blind-crop-and-initial-state-proof-2026-10-31), [input QC](docs/research/CFSDS_TRAIN_INPUT_QC.md), [invariance receipt](reports/real-fire-data/cfsds-target-blind-input-invariance.json), [train screen](reports/real-fire-data/cfsds-train-target-blind-window-screen.json).
- Fokus testovi: 12/12 prolaze; puni suite 58/58, strict OKF za 70 Markdown fajlova i synthetic CLI smoke prolaze. Sljedeće: prostorna podobnost bez targeta, fuel-vintage cutoff/succession i NF-scar importer; no-action replay gate ostaje blokiran.

## 2026-10-31: TASK-015 pre-target maska i NF-scar importer

- Dodani su TRAIN-only mask audit i unit testovi. Za `2018_747`, target DOY 228, `arrival_day < 228` bira 881 pixel prije targeta; 19 target pixela je izostavljeno, a test pokriva i synthetic budući dan n+1.
- Izolovani C++ fixture reprodukuje da trenutni importer odbija historijski `burnt` scar na `NF` ćeliji; nema promjene C++/case builder ponašanja.
- Godišnja fuel mapa nije generisana: v2014b per-pixel cutoff nije potvrđen, v20191114 succession tree nije transkribovan/validiran, a current case builder bira aktivni n-1 front prema targetu n. Taj target-aware input mora se zamijeniti prije nepristrasnog benchmarka. Bez replaya, treninga, heldout podataka ili tuning-a.
- [Input QC i odluka](docs/research/CFSDS_TRAIN_INPUT_QC.md), [mask receipt](reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json), [C++ receipt](reports/firehose-verification/nonfuel-initial-scar-compatibility.json), [ADR-020](docs/specs/DECISION_RECORDS.md#adr-020).
- Provjera nakon izmjena: 46/46 testova, strict OKF za 70 Markdown fajlova, novi synthetic CLI smoke, train-only proof i izolovani C++ expected-rejection verifier prošli; `git diff --check` čist. Nema godišnje fuel mape, CFSDS replaya niti treninga.
- Prvi sljedeći korak u [handoffu](docs/NEXT_SESSION.md): definisati target-blind n−1 front, preregistrovati ga i dokazati da promjena target maske ne mijenja početni input.

## 2026-10-31: train-only input QC i fuel-vintage provenance

- Input audit je izmjerio 3/20 dostupnih CFSDS train FireCase paketa: sva tri imaju usklađene 20×20/100 m ASCII gridove, po 400 validnih terrain ćelija i 24 uredna vremenska reda. Weather point je 2.436–5.195 km od CFSDS centroida; dnevni FWI se ponavlja kroz satne redove.
- Pregledani su službeni fuel izvori 2014b, 2019 development i 2024, objavljena W.I.S.E. annualization metoda, MRDEM, ERA5/Open-Meteo, CNFDB i licence. Nijedan novi map vintage nije odobren kao leakage-safe zamjena; 2014b nema eksplicitan burn-record cutoff, a suppression ostaje unknown.
- Metoda, mjerenja, izvori, ADR-019, EXP-009, TASK-015 status/backlog i handoff su ažurirani. Nema novog replaya, kalibracije, benchmarka, treninga niti heldout ishoda.
- Provjera: 42/42 testova, strict OKF 70 Markdown fajlova, synthetic CLI smoke i git diff --check su prošli. [Input QC](docs/research/CFSDS_TRAIN_INPUT_QC.md), [receipt](reports/real-fire-data/cfsds-train-input-qc.json). No-action gate ostaje pao.

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
