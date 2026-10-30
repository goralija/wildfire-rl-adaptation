---
type: Project Status
title: Trenutno stanje — 2026-10-31
sources:
- resource: /reports/firehose-verification/verification.json
- resource: /reports/firehose-verification/task004c-adapter-smoke.json
- resource: /docs/WORK_LOG.md
---
# Trenutno stanje — 2026-10-30

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
korist agenta. [Replay mjere](../reports/real-fire-data/2018_747-day228-replay.json),
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

Sljedeće: dovršiti TASK-015 leak-safe fuel-vintage i preostalu terrain/weather/suppression
provenance samo na train događajima → unaprijed definisani train-only kontrolisani
no-action replayi sa zajedničkim horizontom
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
