---
type: Project Status
title: Trenutno stanje — 2026-10-31
sources:
- resource: /reports/firehose-verification/verification.json
- resource: /reports/firehose-verification/task004c-adapter-smoke.json
- resource: /reports/real-fire-data/cfsds-train-spatial-feasibility.json
- resource: /reports/real-fire-data/cfsds-train-full-day-pair-screen.json
- resource: /reports/firehose-verification/nonfuel-initial-scar-contract.json
- resource: /docs/research/CFSDS_FUEL_VINTAGE_REVIEW.md
- resource: /docs/WORK_LOG.md
---
# Trenutno stanje — 2026-10-31

## Baza znanja u repozitoriju
Repo je OKF 0.2 bundle s [root indeksom](../index.md),
[sažetim kontekstom](../knowledge/project-context.md), [mapom koda](../knowledge/code-map.md)
i [pravilima održavanja](../knowledge/maintenance.md). Dokumenti imaju tipove,
lowercase indekse i navigaciju; agent ulazi dijele isti AGENTS kontekst. Zaseban
knowledge checker/CI čuva strukturu i lokalne linkove. Migracija ne zatvara dataset
refinement niti uvodi naučnu/humanu verifikaciju sadržaja.
Provjera: [63 Markdown fajla, 15 knowledge testova i clean-clone dokaz](../reports/knowledge-validation.json).
Osnovni aplikacijski paket i dalje nema dodatne zavisnosti; PyYAML je samo knowledge alat.

## Lokalni workspace
Projektni bootstrap PR #1 je spojen u `main`; baza za ovaj nastavak je commit `ea5b8a7a`.
Train-only fuel QC je urađen u zasebnom task worktreeu na grani `research/cfsds-train-qc`.
Glavni klon i drugi postojeći worktree sačuvani su. Sirovi podaci i treći Firehose
checkout ostaju izvan commita. Runbook za worktree raspored je u
[workspace layout dokumentu](../knowledge/workspace-layout.md).
[Provjera preseljenja](../reports/workspace-relocation.json): 13,246 ne-venv fajlova
i 11 backup fajlova sa istim hashovima, 19 sačuvanih verzija paketa, ispravljene
lokalne venv putanje, 26 aplikacijskih/15 knowledge testova i 64-file OKF provjera.

## Najnoviji pomak
**Cell2Fire je kompajliran i oba postojeća 20×20 Firehose PPO checkpointa rade.**
Izvršeno je 12 kratkih inference rollouta, bez treniranja, u odvojenom Linux ARM64
kontejneru sa SB3/contrib 1.5.0 i Gym 0.21.0. Runtime gate je prošao.

- Isti input/seed ponavlja kompletan niz akcija/state hashova; drugačiji C++ seed mijenja širenje.
- Budžet B=8 se poštuje; zatim no-op do simulator done. Težine ostaju nepromijenjene.
- Svi subprocess returncodeovi su 0. Kontrole: no-action, min-L2, max-L2 i dva checkpointa.
- Zabilježen input hash, izvorni commitovi, model hashovi, verzije i Docker image ID.
- Dataset card: 141 fajl, 400 ćelija (307 gorivih), 130 weather fajlova sa po 8 redova.

## Izabrani real-fire podaci i stvarni pilot — 2026-10-30

Odabrana je **Canada + CFSDS v1.1 + Canadian FBP/Cell2Fire** jer najbolje odgovara
postojećem simulatoru i 20×20 agentu. CFSDS v1.1 ima 5,435 kanadskih požara za
2002–2024, 90 m satelitski interpolisanu dnevnu kartu gorenja. Službeni CFSDS rad
opisuje MODIS/VIIRS hot-spot interpolaciju; noviji W.I.S.E. rad ponavlja da je za
kompatibilan no-action benchmark potrebno znatno strože birati događaje. [CFSDS rad](https://doi.org/10.1038/s41597-024-03436-4), [W.I.S.E. procjena](https://doi.org/10.1071/WF26072).

Preuzeto je 23 godišnja ZIP para 2002–2024 (102,405,239 bajtova ukupno) lokalno u
Git-ignorisan `data/raw/cfsds-v1_1`; datoteke su provjerene prema OSF manifestu. Prvi
screen za godine 2014–2024 pregledao je 3,141 događaj/82,015 dnevnih redova i
zadržao najviše pet geometrijski pogodnih događaja po godini: ukupno 44, podijeljena
po godini požara u 20 train, 9 validation i 15 test kandidata. Ovaj spisak nije
iscrpan niti pun benchmark; svi dani jednog požara ostaju u istoj particiji.
[Screen izvještaj](../reports/real-fire-data/cfsds-cohort-screen.json),
[kohort manifest](../data/manifests/cfsds-v1_1-pilot-cohort.json).

**Prvi simulator slučaj `2018_747`, target 16.08.2018:** napravljena je 20×20 × 100 m
karta s Canadian FBP 2014b gorivima, MRDEM 30 m terenom, ERA5-Seamless satnim vremenom,
prethodnim požarnim stanjem i zasebnim targetom za naredni dan. Sve ćelije u scar/front
/target su na podržanom C-3 ili D-1 gorivu. C++ je prihvatio 175 ranije opožarenih i
31 aktivnu ćeliju. Šest no-action seedova (123–128; bez treniranja/intervencija) završilo
je uspješno. Svih šest dalo je istu mapu od 66 ha prema CFSDS cilju 15.39 ha (IoU 0.2187),
a novo širenje dodirnulo je 19 rubnih ćelija našeg 2×2 km isječka. Trajanje runova se
razlikovalo. Dakle konverzija radi, ali
ovaj replay pokazuje veliko neslaganje i rubni efekat; ne validira fiziku niti dokazuje
korist agenta. Ovaj spremljeni pilot koristi historijski target-aware crop i ne smije se
predstavljati kao target-blind niti retroaktivno mijenjati. [Replay mjere](../reports/real-fire-data/2018_747-day228-replay.json),
[mapa](../reports/real-fire-data/2018_747-day228.png).

**Dodatne train provjere, bez treniranja:** `2018_241` i `2018_1770` su pretvoreni i
pokrenuti od historijskog stanja bez početnog zagrijavanja. Bez gašenja je simulator u
prvom slučaju zahvatio svih 400 ćelija: 237 ha novog gorenja prema 12.15 ha opaženih
(IoU 0.0376). U drugom je dodao 73 ha prema 12.15 ha (IoU 0.1361). `2018_241` je dao
iste mjere i kad uključimo 20 minuta zagrijavanja, pa to zagrijavanje nije glavni uzrok
neslaganja. Kandidat `2014_538` nije prošao konverziju jer dio historijskog scar/fronta
upada na vodu ili ne-gorivo u FBP 2014b karti. Ovi nalazi potvrđuju da geometrijski
odabrani kandidati još nisu provjereni slučajevi. [2018_241 mjere](../reports/real-fire-data/2018_241-day227-replay.json),
[2018_1770 mjere](../reports/real-fire-data/2018_1770-day224-replay.json),
[odbijeni `2014_538`](../reports/real-fire-data/2014_538-fuel-rejection.json).

Nakon izmjene probe opcije i C++ initial-state podrške, novi isolated Docker image je
ponovo prošao svih 12 kratkih postojećih Sub20 inference slučajeva; PPO težine su ostale
iste. Sažetak: [regression receipt](../reports/firehose-verification/real-case-image-regression.json).

CFSDS target je dnevna satelitska procjena, ne tačan satni ground-truth front; suppression
status nije spojen. FBP karta je 250 m resamplovana na 100 m, DEM 30 m, a vrijeme je
reanalysis tačka 5.2 km od centra. Dnevni FWI kodovi su ponavljani kroz 24 sata zbog
nedostatka satnih vrijednosti u CFSDS. Za heldout 2019/2022–24 još treba odgovarajuće
fuel-map vintages (2019/2024) i kvalitetni inputi. BiH/MedEU ostaje kasnija odvojena
studija jer njegovi evropski NFFL fuel kodovi nisu isti kao Canadian FBP.

## Train-only no-action mismatch dijagnostika — 2026-10-30

TASK-018 dijagnostička faza je završena na sačuvanim train replayima. Poređeni su
manifesti/hashovi, vrste goriva i FBP parametri, satno vrijeme i dnevni FWI, početni
front, trajanje i rubovi 20×20 domena. Analiza fiksnih vremenskih presjeka pokazuje da
area i IoU snažno zavise od vremena, a tri slučaja rastu različito. Za 30/120 minuta
simulator prognozira 18/42 ha (`2018_747`), 8/46 ha (`2018_241`) i 0/13 ha
(`2018_1770`), dok su ciljevi 15.39/12.15/12.15 ha. Završna predviđanja su 66/237/73 ha.

Sva tri dodiruju rub mreže u prvih 34–52 minuta; `2018_241` popunjava svih 400 ćelija.
Ispostavilo se i da je raw probe metapodatak horizon-a pogrešno računao 480 minuta iz
intervala akcije. Stvarni C++ weather limit je 24 reda × 60 minuta = 1.440 minuta;
probe sada računa horizon iz broja redova. To ne mijenja stare replays. Tačan razlog
završetka i dalje nije u output adapteru, suppression je nepoznat, a CFSDS target nema
tačno intradnevno vrijeme. Zato je dijagnostička faza završena, ali fizički uzrok
neslaganja i no-action gate nisu zatvoreni.

Potvrđene činjenice i hipoteze: [dijagnoza](research/CFSDS_NO_ACTION_DIAGNOSIS.md),
[timeline receipt](../reports/real-fire-data/cfsds-no-action-timeline.json).

TASK-004c adapter je lokalno završen: C++ šalje kumulativni affected/treatment skup,
odvojeni aktivni front i reason (`weather_horizon`, `front_extinguished`, `grid_exhausted`,
`no_ignition`); Python ga prenosi u episode `info` i uskladi cumulative counter. Fixture
i 12/12 inference rollouta prolaze. Ako se ćelija istovremeno pojavi kao affected i
treated, C++ terminalni skup je mjerodavan jer grid prikazuje `-1`; provjeravač zahtijeva
da je svaka takva razlika objašnjena treated skupom. RGB/action/reward/checkpoint ugovori
nisu promijenjeni. [Receipt i ograničenja](../reports/firehose-verification/task004c-adapter-smoke.json).

TASK-015 ostaje djelimičan. Input audit je izmjerio 3/20 raspoloživih train FireCase
paketa; fuel/weather/terrain/suppression poravnanje još nije zatvoreno za cijelu kohortu.
FBP 2014b nema dokumentovan pixel-level vremenski cutoff; 2019 CanFG je u razvojnom
direktoriju i koristi NBAC. Terrain tile provenance nedostaje, weather API field lineage
treba eksplicitno snimiti, a suppression ostaje unknown za svih 20. Batch je runtime
provjera na Sub20, ne CFSDS fizička validacija; no-action gate ostaje pao, nema dokaza
o agentovom smanjenju štete i benchmark/fine-tuning su na čekanju.
Validation/test ciljevi se ne koriste za QC/tuning.

## Train-only input alignment gate — 2026-10-31

Dodani su [lokalni input audit](../scripts/audit_cfsds_train_case_inputs.py),
fokusirani testovi i [mašinski report](../reports/real-fire-data/cfsds-train-input-qc.json).
Tri raspoloživa train FireCase paketa imaju usklađene 20×20/100 m ASCII gridove,
400 terrain ćelija bez NoData i 24 uređena vremenska reda na lokalni target datum;
weather lokacije su 2.436–5.195 km od CFSDS summary centroida. Preostalih 17 input
paketa nije materijalizovano u ovom checkoutu. W.I.S.E. annual-fuel metod i službene
2019/2024 mape su pregledani, ali nijedna se ne proglašava sigurnom zamjenom zbog
vremenskog porijekla/NBAC i potrebe za leak-free succession mapom. Suppression ostaje
unknown, bez novog C++ replaya ili treninga. Vidi
[detaljnu metodu i otvorena pitanja](research/CFSDS_TRAIN_INPUT_QC.md).

## Train-only fuel-vintage mask proof — 2026-10-31

Dodani su [pre-target mask audit](../scripts/prove_cfsds_train_fuel_vintage.py), testovi i
[mašinski receipt](../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json).
Samo TRAIN događaj `2018_747` je obrađen: maska `arrival_day < 228` obuhvata 881 ćeliju
u 48×50 source rasteru (272 u simulator cropu), dok je 19 ćelija dana 228 izostavljeno;
u ovom event rasteru nema poslije-target ćelija. Unit test dodatno provjerava da se
synthetic dan n+1 isključuje. Ovo dokazuje vremensko pravilo maske, ne godišnju FBP kartu.

Isti audit je otkrio dodatni evaluation blocker: raniji `build_cfsds_case.py` birao je
day n-1 aktivne ćelije provjeravajući dodiruju li target day n. Taj target-aware izbor
zamijenjen je target-blind prototipom; detalji i nezavisni invariant dokaz su u odjeljku
ispod. W.I.S.E. paper navodi i priznaje buduću informaciju u svom frontu, pa njegovu
target-aware metodu ne koristimo za naš unbiased benchmark.

Izolovani C++ fixture (`NF` cell 4 kao `burnt`, uz gorivnu cell 1 kao `burning`) potvrdio
je poruku `InitialState.csv marks a non-fuel/harvested cell as burned`; importer odbija
scar prije prvog grid exporta. To je očekivana odbijenica u
[kompatibilnosnom receipt-u](../reports/firehose-verification/nonfuel-initial-scar-compatibility.json),
ne simulator PASS. Nijedna fuel klasa nije promijenjena, nije pokrenut CFSDS replay ni RL
trening i nisu otvoreni validation/test rasteri.

Odluka [ADR-020](specs/DECISION_RECORDS.md#adr-020) blokira godišnje reclassifikovanje dok
se ne potvrde per-pixel vintage/succession tree i importer/damage contract. Target-aware
front je zamijenjen target-blind prototipom, ali post-selection screen pokazuje slabu
target pokrivenost na fiksnom gridu, a no-action gate ostaje pao. Train terrain/weather
provenance i suppression takođe nisu zatvoreni.

## TRAIN-only target-blind initial-state proof — 2026-10-31

Uvedeno je pravilo [CFSDS initial-state helpera](../scripts/cfsds_initial_state.py):
prozor 23×23 se bira samo iz arrival vrijednosti prije target DOY i njegov centar se
postavlja što bliže centroidu svih day n−1 piksela. Za početni model front uzimaju se
day n−1 pikseli unutar sigurnog unutrašnjeg prstena; n−1 pikseli na samoj ivici prozora i
stariji pre-target pikseli ostaju burnt scar. Dnevna satelitski interpolisana oznaka je
proxy, ne satna mjera plamena.

Na samo TRAIN događaju `2018_747` promjena pozicije svih 19 day-n target piksela promijenila
je zasebnu target truth mapu, ali nije promijenila crop offset, 20×20 scar/front maske ni
serijalizovani `InitialState.csv`: `PASS_TARGET_MASK_INVARIANCE`. Target-blind crop sadrži
17/19 target piksela (0.894737), ali ta pokrivenost je samo post-selection dijagnostika.
Pogledati [invariance receipt](../reports/real-fire-data/cfsds-target-blind-input-invariance.json)
i [implementaciju/testove](../scripts/cfsds_initial_state.py).

Drugi screen otvarao je samo godišnje CFSDS rastere 2014–2018 (train). 25 kandidata,
pet po godini, odabrani su po target-independent pre-target front/history mjerama; target
coverage je izračunat nakon izbora. Samo 4/25 prozora sadrže makar jedan target pixel;
medijana target capture je 0, a maksimum 0.010402. Ovaj rezultat upozorava da trenutni
fiksni 2×2 km model prozor često ne zahvata sljedeći dnevni rast. Nije korišten da se
promijeni crop, rangiranje ili parametar; reality-check podobnost i domena ostaju otvoreni.
Pogledati [train-only screen receipt](../reports/real-fire-data/cfsds-train-target-blind-window-screen.json).

Nije napravljena godišnja fuel mapa, obnovljen FireCase, C++ replay, tuning ni trening.
Target-mask invariance je jedan matematički/implementacijski dokaz, ne dokaz ponašanja
požara. No-action gate, model-domain prikladnost, annual fuel provenance/importer contract,
weather/terrain izvori i suppression i dalje blokiraju benchmark i fine-tuning.
Raniji rezultat 10/20 `PASS_FUEL_ONLY` važio je za prethodnu kohortu/target-aware cropove;
ne kvalifikuje novi target-blind shortlist, koji još nema ponovljen fuel audit. Sačuvani
pilot FireCase-ovi ostaju historijski prototipi i nisu retroaktivno preimenovani u
target-blind slučajeve.

## TRAIN-only prostorni audit domena — 2026-10-31

Isti 25 TRAIN event/day kandidata upoređeni su na 20×20/100, 150, 200 i 300 m te
40×40/100 m. Prozor svakog slučaja prvo je izabran oko day n−1 centroida iz pre-target
rastera; target geometrija je mjerena tek nakon izbora. Za 20×20/100 m target ulazi u
4/25 prozora (median capture 0%, max 1.04%). Na oko 4 km, target se vidi u 19/25, ali
medijalno je pokriveno samo 1.95%. Oko 6 km medijana je 15.31%, no dvije source slike su
premale za 67×67 raster prozor. [Metoda i tumačenje](research/CFSDS_SPATIAL_FEASIBILITY.md),
[mašinski report i hashovi](../reports/real-fire-data/cfsds-train-spatial-feasibility.json),
[ADR-022](specs/DECISION_RECORDS.md#adr-022).

**Odluka:** postojeći 2×2 km domen nije dovoljan za reality-check ovih shortlisted parova;
ne usvaja se širi domen samo zato što target coverage raste. Audit ne resampluje gorivo,
teren ni vrijeme i ne pravi simulator ulaze. 20×20 na 200/300 m zadržava checkpoint oblik
ali mijenja fizičko značenje akcija; 40×40 na 100 m ne odgovara postojećem checkpointu.
Stari day-pair shortlist uslovljen je target-day summary zapisom i pozitivnom firearea,
pa je ovaj bounded audit ostao historical-only. Puni target-independent screen je naknadno
završen; pogledati [EXP-013 izvještaj](research/CFSDS_FULL_DAY_PAIR_SCREEN.md) i
[receipt](../reports/real-fire-data/cfsds-train-full-day-pair-screen.json). Nije otvoren
validation/test raster; nema novog casea, replaya, kalibracije ili treninga.

## Train-only fuel quality gate — 2026-10-30

Implementiran je [per-cell audit](research/CFSDS_TRAIN_QC.md) za svih 20 preliminarnih
train day-pair kandidata. Deset prolazi `PASS_FUEL_ONLY`, a deset dobija
`FAIL_FUEL_OVERLAP`; processing grešaka nema. Aktivni front i naredni target su u svih
20 geometrijski validni i većinski na modelskom gridu ne dodiruju rub. To nije potvrda
potpunog simulator slučaja: terrain/weather, suppression i reality-check su posebne
provjere. Sve tri postojeće replay studije (`2018_747`, `2018_241`, `2018_1770`) prolaze
gorivni gate, pa fuel preklop sam ne objašnjava njihovo preveliko širenje.

Audit je koristio samo train slučajeve za overlay. Cohort manifest i zajednički crop-screen
JSON, koji sadrže i druge podjele, bili su učitani radi selekcije train redova;
validation/test fuel i source rasteri nisu otvarani. Rezultati su zapisani i u train
redove [kohort manifesta](../data/manifests/cfsds-v1_1-pilot-cohort.json). Nije bilo
simulator replaya, RL treninga ili kalibracije.
Suppression je nepoznat za svih 20. [Detaljni report](../reports/real-fire-data/cfsds-train-fuel-qc.json).

## Environment reproducibility — 2026-10-30

U feature checkoutu je napravljen moderni Python 3.12.4 `.venv` s optional RL, GIS i
knowledge alatima. Geospatial stack je izolovan: rasterio 1.4.4, geopandas 1.2.0,
pyproj 3.8.0, xarray/rioxarray, netCDF4, SciPy, CDS API klijent i ostale zavisnosti;
GeoTIFF nearest-neighbour reprojection/import smoke je prošao. Kombinovani freeze je
`requirements/research-macos-arm64-py312.freeze.txt`. Prošlo je 26 aplikacijskih testova, 15 knowledge testova, strogi checker za
67 Markdown fajlova, synthetic CLI smoke i 1,024-koračni synthetic PPO
smoke. Legacy Firehose image je svježe izgrađen na Linux ARM64 iz pinovanih upstream
commitova; 12/12 inference slučajeva su prošli, sa ugašenom mrežom i bez treninga.
Tačne verzije i image/source hashovi su u [environment receipt](../reports/environment-setup/README.md).
TASK-004c adapter mismatch je riješen u izmijenjenom izolovanom imageu; environment/runtime
PASS i dalje nije research-ready zbog neriješenog CFSDS no-action mismatcha, nepoznatog
suppressiona, domena i intradnevne ground-truth granice.

Dogrib gorivo/elevation dijele blok sa Sub20 mapom, pa nije nezavisan test prostorne
generalizacije. MedEU je zaseban mogući evropski track, ali nije potreban za glavni
Canadian FBP projekat i još nije pretvoren u simulator input.

## Ograničenja koja su stvarno potvrđena
Stari rollout receipt bilježi reset/brojač razliku 206 naspram 207; TASK-004c sada
sinhronizuje reset observation i na terminalnom C++ receiptu provjerava/sinhronizuje
kumulativnu štetu. Novi 12-case matrix daje isti Python/C++ cumulative count u svim
slučajevima. Svi slučajevi u toj matrici ipak završe na `weather_horizon`; druge C++
terminal grane nisu direktno pokrivene batchom. Stvarni CFSDS pilot ima multi-cell
importer, ali njegovo fizičko neslaganje ostaje. Zbog toga **research_ready=false**.

## Ostalo što radi
Baza zahtjeva/rubrike/literature/odluka, synthetic-v1 engine i pet baseline politika,
upareni eksperimenti i manifesti, 300-epizodni sintetički replay, moderni Gym/PPO smoke.
Prethodni sintetički artefakti ostaju historijski dokaz; nisu Cell2Fire rezultati.

## Dokazi
- [Runtime nalazi](research/FIREHOSE_VERIFICATION.md), [dataset](research/DATASET.md).
- `reports/firehose-verification/`: input inventar, legacy 12-case receipts i
  [TASK-004c adapter receipt](../reports/firehose-verification/task004c-adapter-smoke.json).
- 38 aplikacijskih testova prolazi s modernim environmentom; strict OKF provjera i
  synthetic CLI smoke takođe prolaze nakon TASK-004c izmjena.
- Originalni Firehose i contrib checkouti ostaju neizmijenjeni; samo build flagovi i
  eksplicitna dijagnostika reset/seed ponašanja su dodani u naš kod.
- Docker/legacy i moderni .venv su odvojeni. Legacy inference je bez treniranja i
  plaćenog compute-a. Kod/dokumentacija su objavljeni kroz [PR #1](https://github.com/goralija/wildfire-rl-adaptation/pull/1).

Sljedeće: potvrditi vremenski siguran FBP fuel vintage/succession, riješiti importer
semantiku non-fuel historijskog scar-a i zatvoriti terrain/weather/suppression provenance
samo na train događajima → unaprijed definisani train-only kontrolisani no-action replayi sa zajedničkim horizontom
→ zasebna odluka o no-action gateu → tek zatim zamrznuti event-level heldout ID-jeve →
frozen benchmark/trening samo nakon prihvatljivog replay gatea.
Nema provjere fizike simulatora na BiH podacima, potvrde RL prednosti ili generalizacije.
Deadline/compute i licence za sirove podatke ostaju otvoreni.

## Pregled i odgođena sitnica
I bootstrap i novi runtime pregled su prošli bez kritičnih ili važnih nalaza.
Novi pregled nezavisno potvrđuje testove, evidence/provenance i dataset hashove.
Jedan stari minor ostaje TASK-010:
JSON null config u synthetic CLI-u daje traceback umjesto uredne poruke.

## Handoff za kolegu
[HANDOFF](../HANDOFF.md) sadrži prenosiv clone/setup, put do legacy runtimea,
pribavljanje lokalnih podataka i trenutno stanje replaya.
Za objavu ponovo prolazi svih 26 testova u modernom environmentu. Čisti lokalni
Git klon s novim venvom i bez dodatnih paketa prolazi 22 testa (4 optional preskočena)
i synthetic smoke; originalni lokalni setup nije preduslov za taj početak.
Bootstrap rad je spojen kroz [PR #1](https://github.com/goralija/wildfire-rl-adaptation/pull/1).
Ova statusna grana sadrži zaseban naredni train-data QC korak.

## Puni TRAIN target-independent day-pair i prostorni screen — 2026-10-31

Skripta [audit_cfsds_train_full_day_pairs.py](../scripts/audit_cfsds_train_full_day_pairs.py)
pregledala je samo godišnje CFSDS arrival rastere 2014–2018: 1.301 TIFF, svi sa validnim
parom po pravilu „najraniji DOY sa najmanje tri 90 m arrival piksela, pa naredni
kalendarski dan“. Group CSV tabele, `firearea`, weather i target geometrija nisu korišteni
za članstvo. Za svih 1.301 par ostaje u auditu; 1.010 imaju target piksele, 291 ima status
`no_mapped_pixels_on_next_day`. Uklanjanje target i kasnijih raster oznaka ne promijeni
izabrani input dan ni u jednom slučaju.

Na unaprijed zadatom 20×20/100 m prozoru (oko 2 km), 1.295/1.301 cropova imaju najmanje
tri input-front piksela u sigurnom unutrašnjem dijelu. Od 1.010 parova s mapiranim targetom,
945 imaju makar jedan target piksel unutar prozora; medijalni capture je 36.71% za 1.008
parova s opaženim targetom i prozorom. Veći fizički prozori povećavaju capture među
slučajevima gdje prozor stane, ali 254 slučaja ne mogu smjestiti 4 km opcije, a 566 ne mogu
smjestiti 6 km opciju. Capture je native-pixel naknadna dijagnostika, nije resamplana
Cell2Fire maska i nije korištena za izbor para ili domena. Nije usvojen novi grid.

Dokumentacija: [metoda i tumačenje](research/CFSDS_FULL_DAY_PAIR_SCREEN.md),
[JSON receipt](../reports/real-fire-data/cfsds-train-full-day-pair-screen.json) i
[case/domain CSV](../reports/real-fire-data/cfsds-train-full-day-pair-screen.csv).
Nema godišnje leakage-safe fuel mape, importer non-fuel scar ugovora, potpunog terrain/
weather/suppression paketa, no-action gate prolaza, nove FireCase konverzije, replaya,
benchmarka ili treninga. Sljedeće potvrditi vremenski siguran fuel/source ugovor i novi
target-blind slučajevi; target capture ostaje van izbora. **research_ready=false.**

## TRAIN-only FBP fuel-vintage source review — 2026-10-31

Pregledani su službeni CWFIS v2014b i v20191114 metadata, 2024/2026 fuel-map opisi,
CWFIS download licence, službeni 2018 FBP baseline-class rules/base-layer PDFs i
publisher tekst W.I.S.E. rada. v2014b metadata navodi Land Cover 2011 i NFDB/NBAC
identifikaciju scars, ali ne navodi datum snapshot-a niti vremenski cutoff spaljenih
poligona. Zato se v2014b zadržava za reprodukciju spremljenih pilota i nije potvrđen kao
as-of-event input za nove slučajeve. v20191114 ima 2017 kNN/NBAC i nije direktan vintage
za događaje 2014–2018; 2024/2026 mape takođe nisu TRAIN baseline. Sada je dokumentovano
da CWFIS download-site licenca navodi Open Government Licence - Canada uz CFS attribution.

Pronađena službena *FBP Fuel Layer Decision Rules* dokumentacija opisuje dodjelu osnovnih
FBP klasa; nije burn-scar succession stablo iz W.I.S.E. rada. Nije izrađena godišnja mapa,
preuzet raster, simulator input ili replay. Fuel vintage i succession ostaju blokirani;
sljedeći nezavisni mali task je ugovor/test za historical `burnt` stanje na `NF` gorivu.
Detalji: [fuel-vintage audit](research/CFSDS_FUEL_VINTAGE_REVIEW.md), [source register S-031–S-041](research/SOURCES.md),
[ADR-024](specs/DECISION_RECORDS.md#adr-024).

## NF historical-scar importer contract — 2026-10-31

TASK-015 importer podzadatak je završen. `InitialState.csv` sada prihvata poseban
`scar_nf` zapis samo kada caller izričito potvrdi da je ćelija historijski scar, a
pinovani C++ `Data.csv` klasu vidi kao tačno `NF`. Scar ulazi u cumulative affected
istoriju, ali ne postaje raspoloživo gorivo niti aktivni front. Obični `burnt` na NF,
`burning` na NF i `scar_nf` na gorivu se odbijaju. Python serializer podržava masku
koju caller dostavi, ali CFSDS case builder i dalje odbija nonfuel scar dok vremenski
fuel vintage i succession crosswalk nisu dokazani.

Sintetički Sub20 C++ rollout je završio na `weather_horizon`: početni scar `NF` ostaje
u završnom cumulative setu, C++ i Python cumulative damage se slažu, terminalni grid se
slaže s adapterom, a NF nikad nije u aktivnom frontu kroz tri prijelaza. Tri negativna
fixturea su odbijena s očekivanim porukama. Ovo provjerava format/stanje adaptera, ne
širenje požara u prirodi, CFSDS integraciju ili kvalitet treninga; nije pokrenuto
treniranje ni CFSDS replay. Vidi [ADR-025](specs/DECISION_RECORDS.md#adr-025),
[EXP-015](research/EXPERIMENT_LOG.md#exp-015--explicit-nonfuel-historical-scar-importer-contract-2026-10-31)
i [runtime receipt](../reports/firehose-verification/nonfuel-initial-scar-contract.json).

I dalje nema leakage-safe godišnje fuel mape: v2014b cut-off nije potvrđen, a javno
transkribovanoj Figure 2 nedostaje potvrđena age/special-class semantika i artifact check.
Naredni rad je preostali TRAIN input provenance (DEM, weather, suppression) za slučajeve
koji prođu source gate, pa unaprijed definisani no-action replay gate.
**research_ready=false.**


## TRAIN input provenance follow-up — 2026-10-31

The source review corrected an earlier open question: W.I.S.E. paper Figure 2 is public
and its succession tree is transcribed in the [fuel-vintage review](research/CFSDS_FUEL_VINTAGE_REVIEW.md).
It keeps pre-fire O-1 as grass; other burns become C-2 after >21 years, M-2 C25% after
>5, D-2 after >2, and Non-Fuel otherwise. The figure does not define exact date
arithmetic or treatment of special classes, and the v20191114 artifact has not been
checked. Official v2014b metadata still gives no NFDB/NBAC historical burn cutoff, so no
annual fuel map is safe to claim or emit.

The three saved FireCases are old target-aware builder outputs, not clean inputs for the
new benchmark. Their generated terrain grids are hashed and the MRDEM-30 VRT / bilinear
30 m to 100 m path is recorded, but upstream tile/cell IDs and acquisition dates are
missing. Their raw weather responses preserve resolved point/timezone/fields/units/hash,
but not the original request coordinate/URL, so selection of those historical points
cannot be shown target-blind.

A useful official suppression source is Alberta's 2006–2025 fire-level dataset. Its
catalogue describes location, dates/duration, weather, staffing and physical suppression
resources. The direct CSV endpoint returned HTTP 403 from this workspace; no file or
event join was produced. Fire-level resources would still not amount to a daily action
timeline. Two pilot centroids are in BC and one is near the Alberta/BC border, so
jurisdiction must be confirmed per event. See [source register S-034–S-043](research/SOURCES.md),
[ADR-026](specs/DECISION_RECORDS.md#adr-026) and [EXP-016](research/EXPERIMENT_LOG.md#exp-016--train-fuel-tree-correction-and-external-input-lineage-audit-2026-10-31).

No raster was downloaded/generated, no FireCase was rebuilt, and no replay or training
was run. No validation/test material was opened. **research_ready=false.**

Next: verify the fuel tree's artifact and age rules and seek a dated v2014b cutoff; obtain
the Alberta table through an official accessible route and attempt only TRAIN event
matches; then repair DEM/weather query lineage before preregistering a common-horizon
no-action gate.
