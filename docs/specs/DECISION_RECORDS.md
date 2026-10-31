---
type: Decision Log
title: Odluke (append-only)
---
# Odluke (append-only)

## ADR-001 — trajna projektna memorija u repozitoriju, accepted 2026-10-28
Korisnik traži lak nastavak. Biramo Markdown, JSON konfiguracije/manifeste i mali Python
paket. Alternativa vanjska baza/servis uvodi održavanje bez koristi u početku.
Privatni originali ostaju ignorisani; javni sažetak čuva relevantne zahtjeve.

## ADR-002 — Firehose kao kandidat, synthetic samo za pilot, provisional 2026-10-28
Cell2Fire nije obavezan. Zadržavamo mogućnost postojećih težina, ali legacy setup,
fiksni seed i interaktivni fork moraju proći TASK-004. SimFire je fallback, ne automatski
bolji izbor. Trošak pogrešne odluke ograničen je feasibility timeboxom.

## ADR-003 — intervencija i pošteno računovodstvo, accepted for pilot 2026-10-28
Jedna ćelija, trajni tretman, cost=1, no-op=N; B potrošen ne završava epizodu.
Ever-burned je trajni damage; time-limit je truncation, ne containment.
Glavni backend mora eksplicitno dokazati istu semantiku ili dokumentovati razliku.

## ADR-004 — dva odvojena environmenta, accepted 2026-10-28
Moderni optional Gymnasium/SB3 smoke odvojen od legacy Firehose reprodukcije.
Ne pokušavati tiho učitavanje SB3 1.5.0 težina u novi Dict env i 401 akciju.
Glavni minimalni pristup zadržava arhitekturu i fine-tunira po B; budget-conditioned
model je dodatni pravac nakon definisane migracije i kontrola.

## ADR-005 — lokalni završetak bez remote promjena, accepted for bootstrap 2026-10-28
Repo je prazan. Pravimo lokalnu baznu historiju i izolovanu feature granu, commit i
bundle. Ne kreiramo remote main, PR ili cloud zadatke bez naloga za objavu.
Posljedica: GitHub ostaje prazan dok se grana ne objavi; lokalni rezultat je pregledljiv.

## Otvorene odluke
OD-001: licenca našeg koda i redistribucija mapa/modela.
OD-002: deadline, compute i glavni matriks nakon runtime mjerenja.
OD-003: legacy runtime ili migracija težina; no-op learned ili prisilni wrapper.
OD-004: prostorni/meteorološki test split i granica tvrdnji o generalizaciji.

## ADR-006 — Firehose runtime potvrđen, accepted 2026-10-28
Nastavak ADR-002/004: izvorni fork kompajliran je i oba postojeća 20×20 checkpointa
izvršena su bez treniranja. Zadržavamo Firehose za narednu fazu; promjena simulatora
sada nije opravdana. Legacy okruženje je odvojeni Docker image (Python 3.8 / SB3 1.5),
moderni .venv ostaje za sintetički pilot. Probe čuva 400-action glavu i RGB opažanje;
budžet nameće forced no-op, pa još ne uči vrijeme intervencije.

Runtime PASS nije research-ready: dokazani reset/cumulative-damage problem i spajanje
active/burnt stanja zahtijevaju TASK-004c. Ne koristiti upstream done za containment.
Dataset se za početak sastoji od pinovanih map/terrain/weather inputa i scenarija;
RL iskustvo generiše simulator. Nema obaveze skupljanja označenih intervencija ili
regionalnog GIS-a. Raw data/weights i Docker image ostaju lokalni dok licence nisu provjerene.

## ADR-007 — historijski podaci imaju zasebnu validacijsku ulogu, accepted 2026-10-28
Korisnik je ispravno razdvojio simulator inpute od dataseta opaženih požara i tražio
dobar stvarni dataset. Osnovno istraživačko pitanje ostaje adaptacija politike unutar
simulatora; ne uvodimo obavezu supervised labela intervencija ili novu forecasting temu.

Preporučen početak je Dogrib 2001 sa opaženim scarom i pripremljenim Cell2Fire inputima;
zatim mali CFSDS podskup za nezavisnije događaje, uslovno dostupnim kompletnim inputima.
Izbor konkretnog holdout skupa je provisional. Mali uzorci su preuzeti i pregledani,
ali fizička validacija nije izvršena. Dogrib dijeli fuel/elevation blok s Firehose
Sub20, pa služi kao povezana referenca/kalibracijski slučaj, ne nezavisan test.

Historijski ishodi ne identifikuju ishode novih RL intervencija. Mjerenje sličnosti
požara odvajamo od paired policy benchmarka. Event split i vremenski alignment
preduslovi su za vanjske tvrdnje, ne razlog da odgađamo popravku TASK-004c.
Pinovati CFSDS fajlove: rad opisuje 180 m v1, pregledani v1_1 uzorak ima 90 m.
Raw ostaje ignorisan, manifesti/hashovi/profili i odluke idu u Git. Detalji i
ograničenja: research/REAL_FIRE_DATASETS.md; implementacija provjere je TASK-011.

## ADR-008 — objava grane i PR za timski handoff, accepted 2026-10-28
Korisnik je sada izričito zatražio commit, PR cijelog dosadašnjeg rada i handoff
za kolegu. Time je odobrena remote objava koja je u ADR-005 bila odgođena.
GitHub repo je i dalje prazan: objaviti postojeći prazni bazni commit kao `main`,
zatim `feature/project-bootstrap` sa cjelokupnim radom i otvoriti PR prema mainu.
Ne mergeati PR automatski. Sačuvati historiju, postojeći worktree i lokalne artefakte.

HANDOFF.md daje prenosive upute bez Harunovih lokalnih putanja/okruženja. Objavljuju
se naš kod, dokumentacija, mali rezultati i manifesti. Raw podaci, težine, treći repo,
image, .venv i privatni originali ostaju izvan Gita. Ovo nije izbor licence za tim
niti dozvola za redistribuciju tuđih modela/podataka. Sljedeći tehnički posao ostaje TASK-004c.

## ADR-009 — dataset refinement je prvi projektni korak, accepted 2026-10-28
Korisnik je nakon handoffa ukazao da uloga, izbor i obim podataka nisu do kraja
usaglašeni. Raniji handoff je pomiješao poznati sljedeći tehnički posao sa sljedećim
projektnim korakom. Ovo zamjenjuje redoslijed iz ADR-007/008 gdje se može čitati
da TASK-004c treba odmah početi, prije refinementa.

Prvi fokus je TASK-012: dokumentovati i usaglasiti uloge simulator inputa, RL iskustva
i stvarnih referenci, izbor/obim, mapiranje na model, scenarije/splitove i metrike.
Dogrib/CFSDS preporuke ostaju provisional; preuzimanje/profilisanje nije konačan izbor
ili spreman evaluacijski dataset. Ovaj zapis usvaja redoslijed, ne zatvara te odluke.
TASK-004c ostaje poznati tehnički nastavak prema usaglašenom obimu i preduslov glavne
evaluacije postojećeg pristupa. Runtime nalazi i svi raniji dokazi ostaju važeći.

## ADR-010 — repo kao OKF 0.2 knowledge bundle, accepted 2026-10-28
Korisnik je zatražio samostalnu bazu znanja u repozitoriju, OKF 0.2 i agent onboarding,
u istom PR-u. Biramo repo root kao bundle root: postojeći docs/reports ostaju kanonski
koncepti, dodaju se typed frontmatter, lowercase indeksi, root log i knowledge playbookovi.
Ne pravimo paralelne kopije cijelog docs stabla niti vanjski servis/MCP kao preduslov.

Root index/AGENTS usmjeravaju čitanje; mali CLAUDE/GEMINI/Copilot ulazi dijele ista
pravila. Spec pin je GoogleCloudPlatform/open-knowledge-format commit ad30107c….
Validator i odvojeni CI knowledge job provjeravaju strukturu i projektne lokalne
linkove/dostupnost; PyYAML je samo alatna zavisnost, osnovni engine ostaje bez nje.
Migracija ne dodaje izmišljenu provenance, ljudsku potvrdu ili naučnu verifikaciju.

TASK-012 ostaje prvi istraživački korak; dataset odluke su otvorene. Raw/težine,
treći repo, environmenti i privatni originali ostaju van bundlea uz recovery manifeste.
Lokalni START_HERE/backup i chat nisu izvor istine ili preduslov za novog saradnika.

## ADR-011 — glavni klon direktno u mpvi, accepted 2026-10-28
Korisnik traži da mpvi bude klon, worktree-i u mpvi/.worktrees i lokalni ignorisani
prostor za fajlove koji ne pripadaju Git historiji. Postojeći glavni Git direktorij
promovišemo iz repository/ u root, a postojeći PR checkout selimo Git move/repair
postupkom. Grane, commitovi i PR ostaju isti; main se ne mergea tim zahvatom.

`.worktrees/` i `.local/` su versionisano ignorisani u feature grani. Dok main još
nema projektnu .gitignore, lokalni info/exclude čuva iste granice. Postojeći backup-i
i lokalni ulazni fajl sele u .local, a originalni ignored podaci/modeli/venv ostaju
uz isti worktree. Python apsolutne putanje treba uskladiti i provjeriti testovima.
Kanonski runbook je knowledge/workspace-layout.md. TASK-012 ostaje prvi istraživački posao.

## TASK-012 istraživački prijedlog — 2026-10-30, usaglašavanje čeka

Desk review je dopunjen CFSDS v1.1 evaluacijom iz 2026, zvaničnim izvorima za fuel
mape i Alberta historijske perimetre. Preporuka je zadržati glavno pitanje na
Firehose/Cell2Fire i kompatibilnoj Sub20 mapi; RL iskustvo generisati online u
simulatoru. Dogrib bi bio samo povezan, opcioni sanity-check; CFSDS opcioni dnevni
model-verification track nakon provjere kompletnosti inputa i vremena.

Ovo je istraživački prijedlog, **nije ADR prihvatanja dataseta**. Tim još treba
usaglasiti obim; nema izabranog historijskog uzorka, train/test manifest ili tvrdnje
o prostornoj generalizaciji. Detalji, izvori, potrebni environmenti, otvorena pitanja
i predloženi TASK-014/015 su u `docs/research/REAL_FIRE_DATASETS.md` i backlogu.
ADR-009 ostaje važeći za redoslijed: refinement/upravljanje podacima prije TASK-004c.

## TASK-012 addendum — real-derived training scenarios i multi-cell initial state, 2026-10-30

Korisnik je dodatno precizirao da RL scenariji trebaju biti zasnovani na stvarnim
požarima/raspodjelama, a ne samo postojećim synthetic mapama, te da se historijski
događaji koriste i za provjeru. Ovo pojašnjava projektni cilj. Ne potvrđuje konačan
izbor geografije, dataseta, licencu, fire IDs ili test split.

Pregledani kandidati zavise od modela/geografije: CFSDS v1.1 (Kanada, 5,435 događaja,
90 m) najbolje odgovara postojećem Canadian FBP/Cell2Fire; FireSpread_MedEU v2
(Evropa/Mediteran, 103 događaja, 320 približno 3 m koraka) ima detaljnije progresijske
granice ali nema Canadian FBP mapu. Dogrib je formatni primjer i dijeli teren sa Firehose
Sub20; nije nezavisan spatial holdout. Zenodo zapis za FireSpread_MedEU ne prikazuje
dataset-license polje, pa se licenca arhive mora potvrditi odvojeno od CC-BY članka.

Izvorni kod je pregledan i pokazuje važan feasibility gate: trenutni C++ `Ignitions.csv`
parser uzima jednu početnu ćeliju po simulacijskoj godini. Više redova iz Python helpera
ne predstavljaju istovremeno višepikselni front. Historijski day n-1→day n replay zato
zahtijeva TASK-004c adapter i TASK-017 multi-cell initial-state podršku prije TASK-016
geospatial konvertera. Uz to postojeći provjereni PPO je 20×20/400 akcija (100 m po
ćeliji ≈400 ha), pa ne pokriva cijeli veliki požar bez izričitog crop/state-boundary plana.

Odvajamo: (1) real-derived uslove za online RL scenarije, (2) target history za no-action
spatial check, i (3) simulated counterfactual policy comparison. Ne zaključivati da bi
agenta u stvarnosti sigurno izgorjelo manje; taj rezultat važio bi samo za Cell2Fire
parametre i njegovu apstraktnu ćelijsku intervenciju. Source/geography recommendation i
koraci su u `docs/research/REAL_CASE_PIPELINE.md`, `REAL_FIRE_DATASETS.md`, TASK-015/017/016.

## TASK-012 BiH spatial-screen addendum — 2026-10-30

FireSpread_MedEU v2 je lokalno preuzet samo za prostorni pregled (ZIP je pod Git-ignorisanom
`data/raw/`; checksum i screening metod su u `reports/real-fire-data/medeu-spatial-screen.json`).
Presjek sa Natural Earth 1:110m granicom našao je 7 prvih EFFIS kandidata koji dodiruju
BiH; preciznu lokaciju još treba potvrditi službenim EFFIS podacima/preciznijom granicom.
`EFFIS_id=205938` je kvalitetan svakodnevni historical reference, ali puni obuhvat je oko
4.14×4.18 km. `EFFIS_id=43482` je manji po površini, ali bounding extent 2.56×1.71 km.
Oba prelaze postojeći 20×20/100m policy window u barem jednoj dimenziji.

Dodatna lokalna provjera je preuzela EFFIS European Fuel Map 2017 i presjekla je s
finalnim poligonima `205938` i `43482`. Raster je 250 m EPSG:3035, NFFL/Anderson kodovi;
obuhvaćeni su kodovi 4/5/9 uz no-data za `205938`, te 3/5 za `43482`. EFFIS web licenca
kaže CC BY 4.0 za EU-owned sadržaj osim posebnih napomena; zadržati slojsku provenance,
citat i prerade. Ovo pronalazi gorivni izvor, ali ne zatvara simulator izbor: postojeći
Firehose C++ build je Canadian FBP i ne može direktno uzeti EFFIS NFFL kodove. FIRE-RES
100 m/Scott–Burgan karta je kandidat za provjeru, ali njena BiH pokrivenost, izvoz i
uslovi nisu potvrđeni; ne tretirati je kao spreman input.

Stoga nema jedinstvene dataset preporuke: CFSDS je putanja za reuse postojećeg Canadian
FBP/Cell2Fire; MedEU je putanja ako je važnija BiH geografija, uz prethodni izbor i
validaciju regionalnog fuel/spread modela, ZIP license provjeru, event location potvrdu
i novu grid/agent scale odluku. Dnevne granice su no-action/model targets, ne akcijske
etikete. Ovaj nalaz ne potvrđuje fizičku tačnost, trening ili RL prednost. Dataset izbor
je i dalje prijedlog koji čeka timsku odluku.

## ADR-013 — odabir glavne real-fire putanje, accepted 2026-10-30

Korisnik je izričito rekao da geografija nije ograničenje i da treba uzeti izvor koji
najbolje odgovara postojećem simulatoru i omogućava bolje scenarije/testne prikaze.
Odabrana je **Canada + Canadian Fire Spread Dataset (CFSDS) v1.1 + Canadian FBP /
Cell2Fire**. CFSDS daje mnogo stvarnih kanadskih požara s dnevnim satelitski procijenjenim
danom gorenja; postojeći simulator već koristi Canadian FBP gorivne klase. FireSpread_MedEU
i EFFIS ostaju mogući zaseban BiH track, ali njihovi NFFL kodovi nisu direktan input
trenutnom simulatoru i tražili bi drugi ili prošireni model.

Historijski target ostaje odvojen od agentovog ulaza i nagrade. Trening iskustvo generiše
simulator na stvarno izvedenim uslovima; sljedeća opažena granica služi no-action
reality-checku. Izbor ne znači da CFSDS target predstavlja satni ground truth niti daje
odgovor šta bi se desilo pod novom RL akcijom. Raw arhive i teži GeoTIFF-ovi ostaju
ignorirani od Git-a; commitujemo kod, provenance, hashove i sažete nalaze.

Početni geometrijski cohort screen drži do pet kandidata godišnje iz 2014–2024 (20 train,
9 validation, 15 test), podijeljene po godini cijelog požara. Ovo je preliminarna lista,
neiscrpna i ne znači da su fuel/weather/suppression svi provjereni ili da je test skup
zamrznut. Prvi train pilot je `2018_747`, target 16.08.2018. Službeni FBP 2014b fuel
vintage kompatibilan je s ovim pilotom, ali 2019/2024 slojevi i event suppression metadata
su potrebni prije šire validacije.

Pilot je konvertovan i pokrenut šest puta u C++ no-action režimu (seedovi 123–128). Svih šest
runova dalo je identičnu mapu od 66 ha novog gorenja prema CFSDS cilju 15.39 ha, IoU=0.2187,
te je dotaklo 19 ćelija ruba 2×2 km prozora; vrijeme simulacije se razlikovalo. Status gašenja je nepoznat. Zato je to mismatch dijagnostika;
ne smije se kalibrisati/validirati na ovom jednom događaju niti koristiti kao dokaz
prednosti agenta. Glavni trening čeka više train-only replaya, input/domain provjere,
preostali terminal/damage adapter i zamrznut event holdout.

Evidence: `data/manifests/cfsds-v1_1-pilot-cohort.json`,
`reports/real-fire-data/2018_747-case.json`,
`reports/real-fire-data/2018_747-day228-replay.json` i `.png` karta.

## ADR-014 — multi-cell initial-state importer i pilot replay, accepted 2026-10-30

TASK-017 je implementiran lokalno kao patch prema pinovanom Firehose/Cell2Fire sourceu.
`InitialState.csv` sadrži one-based row-major `ncell` i odvojeno `burnt` ili `burning`
stanje; C++ učita scar i istovremeni front, Python wrapper čuva ekvivalentno stanje.
Patch/image nisu upstream izmjena i ostaju dokumentovani s checksumom. Potvrđeni su mali
fixture (1 scar + 2 front ćelije) i pravi `2018_747` ulaz (175 scar + 31 front ćelija).

TASK-016 FireCase builder je izgradio poravnate 20×20/100m fuel/DEM/slope/aspect/weather/
initial-state fajlove, a target raster je ostao u zasebnoj `truth/` fascikli. Šest C++ no-action
replaya uspješno se izvršilo bez RL treninga i bez intervencija; svih šest imalo je isti završni raster. `--fire-map` opcija sada
prihvata case mapu, a CSV converter koristi LF redove zbog strogog C++ zaglavlja.

Preostali rizik: prognoza znatno veća od opaženog može biti posljedica nepoznatog gašenja,
weather/FWI ulaza, kalibracije/ROS, male karte ili modela; jedan rezultat ih ne razdvaja.
Dok se mismatch ne razjasni kroz više train događaja/seedova, simulator nema physical
validation gate za policy benefit. Originalni 20×20 pretrained agent i budžetski adapter
nisu trenirani/poređeni na ovom pilotu.

## ADR-015 — no-action gate je obavezan prije treniranja, accepted 2026-10-30

Nakon početnog CFSDS pilota izvršena su još dva train day-paira `2018_241` i
`2018_1770`, oba bez intervencija i sa početnim stanjem učitanim u C++. Rezultati su
237 ha prema 12.153 ha (IoU .0376) i 73 ha prema 12.151 ha (IoU .1361); oba dotaknu
rub 20×20 mreže. `2018_747` ostaje 66 ha prema 15.387 ha (IoU .2187; šest seedova).
No-warmup replayi su ponovili glavne rezultate, pa početnih 20 simulator-minuta nije
uzrok prekomjernog širenja.

Geometrijski prihvatljiv train kandidat `2014_538` konverter odbija prije simulacije:
historijska scar/front/target ćelija pada na Water ili Non-fuel u FBP 2014b sloju.
To potvrđuje da geometrijski crop screen nije dovoljan i da kohortu treba dodatno
filtrirati gorivom, vremenom, FBP parametrima i stanjem domene.

**Odluka:** ne pokretati fine-tuning ili heldout policy poređenja dok no-action razlika
ne bude dijagnosticirana na train slučajevima i dok TASK-004c terminal/damage mjerenje
ne bude dovršeno. Historijski suppression status ostaje nepoznat; CFSDS je satelitski
interpolisani dnevni target, zato rezultat nije sam po sebi dokaz greške Cell2Firea.
Evidence: `reports/real-fire-data/2018_241-day227-replay.json`,
`2018_1770-day224-replay.json`, `2014_538-fuel-rejection.json` i
`reports/real-fire-data/README.md`.

## ADR-016 — train-only fuel gate and next diagnostic order, 2026-10-30

TASK-015 per-cell QC je primijenjen samo na 20 kandidata iz train particije koristeći
Canadian FBP 2014b, trenutno raspoloživi trening-period sloj. `PASS_FUEL_ONLY` znači
isključivo da audit nije našao native 90 m fire-mask piksele niti majority 100 m
model-grid fire-mask ćelije na Water, Non-fuel, Wetland, Urban, Vegetated Non-fuel,
Unknown ili unmapped kategoriji. Sub-majority preklop se zasebno prijavljuje za review.
Ovo je konzervativno projektno pravilo, inspirisano fuel filterima u W.I.S.E. radu,
ali nije reprodukcija njegovog protokola; u ovom auditu i raniji scar ulazi u provjeru.

Nalaz: 10/20 train događaja `PASS_FUEL_ONLY`, 10/20 `FAIL_FUEL_OVERLAP`, bez processing
grešaka. Sva tri već replayana događaja prolaze samo fuel provjeru. To ne potvrđuje
terrain/weather/suppression ni fizičku tačnost i ne znači da su pass događaji puni
caseovi. Kohort manifest i combined crop-screen JSON sa svim split metadata su učitani za train selekciju,
ali nijedan validation/test raster nije otvoren ili overlay-an. Raw ostaje ignorisan;
commituju se kod, hashovi i sažet rezultat.

**Operativni nastavak:** sljedeći TASK-018 prvo poredi postojeće train FireCase manifest-e,
FWI/weather, FBP parametre, početni front i crop/domain te predlaže minimalne kontrolisane
train-only provjere. Ne podešavati validation/test ciljeve. TASK-004c damage/terminal
adapter i no-action gate ostaju preduslov za policy benchmark/fine-tuning prema ADR-015.
Ako se kasnije nađu fuel-vintage ili suppression podaci, ponoviti QC pod novim reportom;
ne prepisivati historijski receipt.

Evidence: `docs/research/CFSDS_TRAIN_QC.md`, `reports/real-fire-data/cfsds-train-fuel-qc.json`.

## ADR-017 — compare no-action growth at a declared time and track grid/horizon end, 2026-10-30

TASK-018 compared the three existing train-only FireCase manifests, hashes, fuel/FBP
settings, hourly ERA5-Seamless rows, daily CFSDS FWI values, initial scar/front and
20×20 domain. All three use the same Canadian FBP 2014b layer/lookup; no M1/M2/M3/M4/O1
special parameter is missing in their C2/C3/D1 map crops. This means the simple fuel-code
overlap gate passes, not that the map or ROS is physically calibrated. Suppression remains
unknown.

Saved grid histories at fixed 30–1,440 minute checkpoints show that growth timing differs
by event. Each run reaches the crop boundary within 34–52 minutes; `2018_241` fills its
400-cell crop, `2018_1770` reaches the 24-hour weather horizon and `2018_747` ends earlier
with no active cells remaining. The existing replay receipts do not expose a typed C++
terminal reason, so these conclusions are derived from the source and saved grids. A
daily interpolated CFSDS target does not provide an observed minute-of-day for comparison.

**Decision:** preserve the diagnostic checkpoint curves without using them to choose an
event-specific burn duration or claim performance. Future no-action and policy comparisons
must declare the same fixed time horizon, identify whether the simulator ended by horizon,
extinction or exhausted grid, and report edge contact. Do not calibrate on validation/test
targets. The no-action gate remains failed; policy benchmarking/training waits for TASK-004c
and additional train-only input checks.

The C++ source caps rows-mode weather to `WeatherRows × 60 / FirePeriodLen`; for the 24
hourly rows and one-minute fire period, that is 1,440 minutes. `steps_per_action=8` means an
agent action interval of eight simulated minutes. The probe had incorrectly reported
`60 × steps_per_action=480` as total weather horizon. The probe now counts actual
`Weather.csv` rows and multiplies by the 60-minute weather period. This metadata fix does
not change any already-run simulation.

Evidence: `docs/research/CFSDS_NO_ACTION_DIAGNOSIS.md`,
`reports/real-fire-data/cfsds-no-action-timeline.json`,
`scripts/analyze_cfsds_replay_timeline.py`, `src/wildfire_rl/firehose_probe.py` and its
focused tests. Context only: the CFSDS v1.1 W.I.S.E. benchmark reports default-setting
overprediction and grid-boundary contact at scale [S-019](../research/SOURCES.md#s-019);
that engine's metrics are not results for this project.

## ADR-018 — make the C++ terminal receipt canonical for episode damage, 2026-10-30

TASK-004c is implemented in the isolated Firehose image. When the categorical output grid
uses `-1` for treatment, a cell affected during the same simulator interval can be hidden
from its positive-grid history. The C++ terminal receipt's `ever_affected_ncells` is therefore
the episode-level source of truth; the patched Python adapter copies it into `cells_burned`
and copies the terminal front/treatment sets into their corresponding counters before
returning final `info`. IDs in the receipt are one-based row-major. Agent actions remain
zero-based and `-1` remains the no-op.

The probe's terminal/grid consistency check requires every positive cell in every saved
grid to exist in the C++ cumulative set. Any extra C++ affected ID must also be in the
C++ treated set, which accounts for the grid's treatment precedence. This is a traceability
check, not an independent fire-damage model. Named simulator reasons are `weather_horizon`,
`front_extinguished`, `grid_exhausted`, and `no_ignition`; timeout, adapter step limit,
missing output and subprocess failure remain separate adapter/process outcomes. The
terminal active front is captured before the horizon transition marks it burnt.

The checkpoint contract remains RGB 3×20×20, `Discrete(400)`, and reward/action semantics
unchanged. Fixture plus 12/12 existing Sub20 inference runs passed, Python and C++ cumulative
counts matched in every case, and all five checkpoint inference cases retained identical
weights. The matrix did not exercise the C++ `front_extinguished`, `grid_exhausted`, or
`no_ignition` paths; all cases ended on `weather_horizon`. No training or physical validation
was performed. The CFSDS no-action gate still fails, so policy benchmarking and fine-tuning
remain blocked pending train-only input QC and a separate replay gate decision.

Evidence: `docker/firehose/task004c_state_export.patch`,
`src/wildfire_rl/firehose_probe.py`, `tests/test_firehose_probe.py`,
`docker/firehose/verify_batch.py`, and
`reports/firehose-verification/task004c-adapter-smoke.json`.

## ADR-019 — distinguish reproducible pilot inputs from as-of-event inputs, recorded 2026-10-31

The train-only input audit measured three materialized FireCases out of 20 train
candidates. Their 20×20/100 m terrain grids align and contain 400 valid cells each;
their weather files have 24 ordered hours on the target local date. This is evidence
of file/grid alignment only, not historical-input or physical validation.

Official source review found that v2014b metadata uses NFDB/NBAC to identify burned
areas but gives no explicit per-pixel temporal cutoff. Therefore the v2014b version
label cannot certify that every 2014–2018 event input is as-of-event. A v20191114
250 m CanFG raster exists in the CWFIS development directory, lists 2017 inventory
and NBAC, and is about 2 GB; it is not adopted as a past-event base map. The official
2024 raster also postdates every current train target. The W.I.S.E. annual fuel-map
recipe is a published candidate method, not a project implementation or result.

The reviewed 2014b and v20191114 directory/metadata sources do not state a license;
confirm terms with NRCan before distributing those rasters. The 2024 fuel map and
MRDEM portal records state the Open Government Licence - Canada. Open-Meteo states
CC BY 4.0 for API data, while free-service terms are separate. Record attribution
and source-specific conditions in any future shared data release.

Decision: preserve v2014b for exact reproduction of existing saved pilot runs, but
do not describe it as a leakage-safe annual vintage for new training cases. A future
fuel map must document its base-map time provenance and hashes, apply only known
pre-target burn history, exclude target-day/future fire information, and test the
interaction between non-fuel scars and the imported initial scar/front. Do not
download the large development raster unless a bounded technical need is established.

Terrain-source tile hashes/acquisition dates are absent from the three saved case
manifests. The ERA5-Seamless response is at a 2.4–5.2 km point-to-centroid distance;
the saved manifests do not preserve field-by-field source mapping or an hourly
FWI trajectory. Suppression remains unknown for all 20 train events. CNFDB agency
perimeters are incomplete and its data require an End-User Agreement; no terms were
accepted and no event-level action timeline was joined.

This decision record does not certify a complete train cohort. TASK-015 remains
partial; the no-action gate remains failed. No simulator replay, calibration,
fine-tuning, benchmark, or heldout outcome inspection was performed for this audit.
Evidence: [train input QC method](../research/CFSDS_TRAIN_INPUT_QC.md),
[machine receipt](../../reports/real-fire-data/cfsds-train-input-qc.json),
[sources S-031–S-037](../research/SOURCES.md).

## ADR-020 — block annual fuel reclassification until provenance and scar semantics are proven, recorded 2026-10-31

A train-only temporal mask was exercised on `2018_747` (target DOY 228). It selected
valid arrival pixels strictly before day 228, included day 227, and excluded day 228
and later values. The complete raster contains 881 pre-target pixels and 19 target
pixels; the selected 23×23 simulator crop contains 272 pre-target pixels, including
the day n-1 front. This proves only the event-time predicate. It does not supply a
safe base fuel vintage or a cross-event annual scar history.

Review of the W.I.S.E. paper distinguishes two fuel operations: annual map succession
using the v20191114 ruleset and the daily same-fire pre-target perimeter mask. The
paper also states that its initial active edge selects day n-1 pixels adjacent to
target day n, explicitly acknowledging future-perimeter information. The current
`build_cfsds_case.py` uses the same target-aware rule; omitting target raster from the
agent observation does not remove this side channel. Replace it with a predeclared
target-blind day n-1 front before an unbiased agent benchmark. The exact succession
tree is referenced in the paper but has not yet been transcribed/validated here.

A network-isolated C++ fixture marked Sub20 cell 4 (`NF`) as historical `burnt` and
cell 1 as active `burning`. The pinned importer rejected the scar with
`InitialState.csv marks a non-fuel/harvested cell as burned` before creating a grid.
The probe's follow-on `IndexError` is a secondary missing-grid symptom, not the
simulator's rejection reason. Receipt:
[`nonfuel-initial-scar-compatibility.json`](../../reports/firehose-verification/nonfuel-initial-scar-compatibility.json).

Decision: implement and retain the strictly pre-target perimeter mask, but do not
reclassify any fuel pixels or alter case-builder/importer behavior yet. The official
v2014b source still lacks a verified per-pixel burn-history cutoff; the v20191114
succession tree has not been transcribed/validated for this project, and raster reuse
terms need confirmation. Before a map is emitted, also define how a non-fuel historical
scar remains in cumulative damage, choose a target-blind day n-1 front, and prove its
import/spread contract. No CFSDS replay, calibration, training, benchmark or
validation/test outcome was used.

Evidence: [TRAIN mask proof](../../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json),
[importer fixture](../../docker/firehose/nonfuel_initial_scar_fixture.csv),
[verification method](../../docker/firehose/verify_nonfuel_initial_scar.py),
[TASK-015 input QC](../research/CFSDS_TRAIN_INPUT_QC.md),
[sources S-031–S-038](../research/SOURCES.md),
[W.I.S.E. paper](https://doi.org/10.1071/WF26072).

## ADR-021 — make CFSDS crop and initial state target-blind, recorded 2026-10-31

The former crop/front selection used day n target geometry to choose day n−1 pixels
adjacent to that target. That gives the agent future spatial information through its
initial state even when target rasters are stored separately. The CFSDS source provides
daily interpolated arrival masks, not exact hourly flame locations, so the project needs a
declared proxy based only on inputs available before day n.

**Decision:** select the fixed 23×23 native crop using only valid arrivals strictly before
day n. Its center is the eligible crop center nearest the centroid of all day n−1 pixels;
the crop must contain at least three day n−1 pixels in its one-cell safe interior. Every
day n−1 pixel in that interior is active front; day n−1 pixels in the crop border and all
older pre-target arrivals are historical burnt scar. Distance ties prefer more interior
front pixels, then more pre-target history, then row/column order. The day-n mask is
computed only after crop/state selection as separate evaluation truth. Source weather
lookup target is calculated from the safe-interior day n−1 centroid, not the day-n summary
centroid. The proof does not fetch or validate a weather response; supplied weather files
and their locations/lineage remain a separate input-provenance task.

The rule was fixed before its TRAIN-only cohort screen. A perturbation proof on
`2018_747` changes all 19 day-n pixels while preserving the pre-target values; crop offset,
model scar/front masks and serialized `InitialState.csv` remain identical, while target
truth changes. Receipt: [target-blind invariance](../../reports/real-fire-data/cfsds-target-blind-input-invariance.json).
The separate 2014–2018 screen selects five candidates per year using only pre-target
event-day/state metrics. Target coverage is measured after selection as a feasibility
diagnostic only: 4/25 shortlisted windows contain any target pixel; median capture is 0,
maximum 1.0402%. Do not use this result to adjust crop offsets, candidate ranking, or
hyperparameters. The screen tool defaults to years 2014–2018 and refuses held-out years;
the case builder defaults to this train-only report and rejects legacy reports/candidate
rows without explicit target-blind flags. Receipt: [train-only window screen](../../reports/real-fire-data/cfsds-train-target-blind-window-screen.json).

This establishes only input-mask invariance for one TRAIN event and a target-blind
prototype; it does not validate the daily-front proxy or fire spread. The low target
coverage warns that the fixed 2×2 km domain may not support a useful next-day
reality-check for most shortlisted events. Resolve spatial feasibility from pre-target
information or independently justify a model-domain change before replay. Keep ADR-020's
annual fuel-map and non-fuel-scar blockers. No case replay, calibration, training,
benchmark or validation/test inspection was performed. Existing saved pilot FireCases
remain historical target-aware prototypes. The earlier 10/20 fuel-only pass/fail audit
used their former cohort/windows and cannot be transferred to this new shortlist.

Evidence: [helper and focused tests](../../scripts/cfsds_initial_state.py),
[case builder](../../scripts/build_cfsds_case.py),
[TRAIN-only screen code](../../scripts/profile_cfsds_cohort.py),
[input QC](../research/CFSDS_TRAIN_INPUT_QC.md),
[CFSDS source S-015](../research/SOURCES.md#s-015).

## ADR-022 — bound the current TRAIN domain audit; do not adopt a wider grid yet, recorded 2026-10-31

The fixed target-blind window from ADR-021 was spatially screened on the same 25
2014–2018 TRAIN event/day pairs at five predeclared physical configurations: 20×20 at
100/150/200/300 m and 40×40 at 100 m. The 25 pairs were held fixed; target-day pixels
were measured only after each pre-target crop was selected. Validation/test rasters were
not opened. The existing pair screen does, however, require a day-n CFSDS record and
positive `firearea`, so full target-independent event/day membership has not been proven.

The 20×20/100 m option finds any target pixel in only 4/25 crops (median capture 0%,
maximum 1.04%). At an approximately 4 km footprint, both 20×20/200 m and 40×40/100 m
capture a target pixel in 19/25, but median capture is only 1.95%. The 6 km 20×20/300 m
option finds a window for 23/25 pairs; 22/23 valid windows contain target pixels, with
15.31% median and 50.08% P75 target capture. Its 67×67 native window does not fit source
rasters `2014_932` or `2015_895`. Capture counts are native 90 m raster pixels and do not
represent a resampled simulator grid.

**Decision:** the current 2×2 km domain is inadequate for reality-checking these 25
shortlisted pairs. Do not choose or adopt a wider grid from this post-selection target
diagnostic; no new FireCase, simulator replay, or RL run is authorized by this spatial
receipt. Wider windows improve coverage but neither resolve the modest 4 km capture nor
prove that coarse 20×20 cells preserve FBP physics. The 40×40 option changes the
checkpoint's observation/action dimensions. Next establish day-pair membership and
domain-screen rules before examining outcomes across the full TRAIN opportunity set;
then assess simulator/cell-scale compatibility on train only. Keep the fuel-vintage,
non-fuel-scar, terrain/weather, suppression, and no-action blockers.

Evidence: [method and interpretation](../research/CFSDS_SPATIAL_FEASIBILITY.md),
[audit code](../../scripts/audit_cfsds_train_spatial_feasibility.py),
[geometry helper/tests](../../scripts/cfsds_spatial_feasibility.py),
[machine receipt](../../reports/real-fire-data/cfsds-train-spatial-feasibility.json).

## ADR-023 — preregister a target-independent TRAIN day-pair screen, recorded 2026-10-31

The prior CFSDS shortlist used target-day metadata and positive `firearea` for pair
eligibility. Its target-blind crop rule did not make its day-pair membership
outcome-independent. To complete the all-TRAIN spatial screen without requiring an
observed target, the screen rule was specified in code before reading target coverage:
for each 2014–2018 fire arrival raster, select the earliest DOY with at least three valid
native 90 m arrival pixels as input day, and use the next calendar day as target. Do not
require a target-day group-table row, positive area, weather field, or target pixel.
Retain a pair with no mapped next-day pixels and record that outcome as
`no_mapped_pixels_on_next_day`; do not call it confirmed zero physical growth.

For each fixed domain (20×20 at 100/150/200/300 m; 40×40 at 100 m), choose a window only
from input-day and older arrival pixels, requiring at least three input-day pixels in the
safe interior. Compute target coverage after pair and window selection. The screen
removes target and later labels and re-selects the day for every raster; the selected input
day remained unchanged in all 1,301 cases.

**Decision:** adopt this as the operational TRAIN day-pair rule for the full-cohort
geometry pre-screen, not as final benchmark eligibility or proof of a useful training
scenario. It yields 1,301 pairs, 1,010 with mapped target pixels and 291 without. At
20×20/100 m, 1,295 windows are available and median target capture is 36.71% among 1,008
observed-target pairs with an available window. Larger windows capture a greater fraction
among cases where they fit, while 254 source rasters cannot fit the roughly 4 km windows
and 566 cannot fit the roughly 6 km option. These target metrics do not choose a domain;
no grid is adopted. The existing 20×20/100 m policy shape remains the only compatible
option in the measured set, but geometry alone is not a physical/model recommendation.

All five TRAIN year archives were opened; validation/test years and group CSV tables were
not. The scan performed no fuel overlay, resampling, FireCase build, simulator run,
calibration, benchmark, RL training, or heldout inspection. Daily interpolated CFSDS
arrivals are not exact intraday flame truth. The as-of-event fuel vintage, succession
crosswalk, non-fuel scar importer, complete terrain/weather provenance, suppression, and
no-action gate remain unresolved.

Evidence: [full method/results](../research/CFSDS_FULL_DAY_PAIR_SCREEN.md),
[scanner](../../scripts/audit_cfsds_train_full_day_pairs.py),
[aggregate receipt](../../reports/real-fire-data/cfsds-train-full-day-pair-screen.json),
[per-pair/domain table](../../reports/real-fire-data/cfsds-train-full-day-pair-screen.csv).

## ADR-024 — keep fuel vintage blocked; record CWFIS reuse terms and distinguish base rules from succession, recorded 2026-10-31

The source review followed the all-TRAIN target-independent screen. Official v2014b
metadata lists 2011 land cover, CanFI2000, ecological inputs, and NFDB/NBAC use to
identify burn scars, but gives no explicit date/cutoff for those burn records. The
v20191114 metadata lists 2017 kNN inventory and NBAC reassignment; the 2024 map
postdates the current TRAIN targets. The official current-year 2026 product describes
annual pre-season updates incorporating prior-year burned-area data, but this does not
establish the historical v2014b cutoff. The W.I.S.E. paper describes a separate
post-fire succession ruleset and same-fire pre-target non-fuel mask.

The official 2018 *FBP Fuel Layer Decision Rules* and *FBP Fuel Layer Base Layers*
documents describe baseline class assignment from inventory/land-cover inputs; they are
not the post-fire succession tree cited by the paper. The CWFIS download-site notice
states Open Government Licence - Canada and requests Canadian Forest Service/CWFIS
attribution, correcting the earlier file-level-only review that found no licence text.
Some component inputs have separate availability/terms notes.

**Decision:** retain the saved v2014b-based FireCases for exact reproduction, but do not
certify v2014b as an as-of-event baseline or use v20191114/2024/2026 directly for new
2014–2018 cases. Do not generate annual fuel maps until the base-map burn-history cutoff,
post-fire succession crosswalk, target-time mask, per-cell provenance, and historical
non-fuel-scar importer contract are resolved. General CWFIS reuse terms are recorded as
Open Government Licence - Canada with attribution; this does not resolve temporal
validity or independent component-source terms. No raster was downloaded/generated and
no FireCase, replay, calibration, benchmark, training, or heldout inspection occurred.

Evidence: [fuel-vintage review](../research/CFSDS_FUEL_VINTAGE_REVIEW.md),
[input QC](../research/CFSDS_TRAIN_INPUT_QC.md),
[source register S-031–S-041](../research/SOURCES.md),
[pre-target mask receipt](../../reports/real-fire-data/cfsds-train-fuel-vintage-mask-proof.json).

## ADR-025 — represent provenance-confirmed non-fuel scars explicitly, recorded 2026-10-31

The pinned Cell2Fire importer previously rejected every historical `burnt` row whose
fuel code was non-burnable. Silently changing the fuel class would corrupt simulator
inputs, while silently accepting any `burnt`/`NF` overlap could turn water, urban, or
no-data mapping mistakes into valid history.

**Decision:** extend `InitialState.csv` with an explicit `scar_nf` state for a
historically burned cell whose exact simulator fuel class is `NF`. This token is a
caller-provided provenance assertion; the importer does not infer it from a generic fuel
class or CFSDS arrival layer. A `scar_nf` cell remains in C++ `burntCells`, output scar
grid code `1`, and the terminal/Python cumulative `ever_affected` set. It is excluded
from `burningCells` and from available fuel cells, so it cannot join or spread the active
front. Ordinary `burnt` on `NF`, `burning` on non-fuel/harvested, and `scar_nf` on any
class other than `NF` remain invalid. `ND`, Water, Urban, and harvested cells are not
eligible.

The Python serializer accepts an optional explicit nonfuel-scar mask only when it is a
subset of the historical burnt mask. It does not look up fuel classes or mark cells
automatically. The CFSDS case builder's current nonfuel/water initial-state rejection is
unchanged. Use `scar_nf` in a real case only after the event history and post-fire fuel
succession provenance identify that exact cell as an NF burn scar.

The bundled Sub20 fixture passed the full no-action episode to `weather_horizon`:
initial scar cell 4 was present in terminal affected IDs `[1,2,3,4]`, absent from the
active front at every recorded step, and terminal C++ damage matched both Python counters
and exported grids. Three companion fixtures confirmed the invalid inputs remain
rejected. This is an importer/state contract test, not fire-behavior validation, a CFSDS
case, or RL training. Machine receipt and hashes:
[`nonfuel-initial-scar-contract.json`](../../reports/firehose-verification/nonfuel-initial-scar-contract.json).

The annual fuel-map gate remains blocked on the dated base-map cutoff, verified
succession rules, and per-cell lineage. Existing saved pilot cases and their historic
receipts are unchanged.

## ADR-026 — correct fuel-tree status and record unresolved train-input provenance, recorded 2026-10-31

Follow-up to ADR-024 located the public W.I.S.E. article Figure 2. The tree can be
transcribed from the figure: preserve pre-fire O-1 Grass; otherwise assign C-2 Spruce
after more than 21 years, M-2 Mixedwood C25% after more than 5 years, D-2 Aspen after
more than 2 years, and Non-Fuel otherwise. This corrects ADR-024's implication that no
public transcription was available. The exact date arithmetic, special-class behavior,
and correspondence to the actual v20191114 rules artifact remain unverified. Official
v2014b metadata still gives no dated NFDB/NBAC burn-history cutoff.

The three saved pilot FireCases are outputs from the prior target-aware builder and are
not regenerated, clean benchmark inputs. Their MRDEM-30 VRT and bilinear 30 m to 100 m
terrain conversion and output hashes are known, but upstream tile/cell lineage and
per-cell acquisition dates are not. Saved Open-Meteo responses contain resolved point,
timezone, fields/units and response hashes; the original request coordinates/query are
missing, so target-blind weather-location selection cannot be demonstrated for those
historic files.

Official Alberta metadata identifies a 2006–2025 fire-level dataset with fire location,
dates/duration, weather, staffing and physical suppression resources. Its official CSV
and dictionary were not retrieved: the direct CSV request returned HTTP 403 from this
workspace. No CFSDS event has been joined. A matched record could support fire-level
suppression evidence, but the catalogue does not promise a day-by-day action timeline;
BC events require an appropriate BC source.

**Decision:** correct the record that the W.I.S.E. Figure 2 tree is publicly
transcribable, while retaining the annual fuel-map block until the v2014b cutoff, age
rules, special classes and per-cell history are verified. Do not promote the three
historic FireCases to a clean benchmark, infer weather-location independence from the
resolved point, or convert absent suppression records into `none`. The next independent
source task is to obtain the Alberta file through an official accessible route and test
fire ID/date/coordinate/perimeter joins on TRAIN only, in parallel with the fuel cutoff
and tree-verification gate; retain DEM/weather lineage gaps. No raster or CSV was
downloaded, no FireCase/replay/training was run, and
no validation/test data were inspected.

Evidence: [fuel-vintage review](../research/CFSDS_FUEL_VINTAGE_REVIEW.md),
[TRAIN input QC](../research/CFSDS_TRAIN_INPUT_QC.md),
[source register S-034–S-043](../research/SOURCES.md),
[Alberta open-data record](https://open.canada.ca/data/en/dataset/a221e7a0-4f46-4be7-9c5a-e29de9a3447e).

## ADR-027 — use BC historical perimeters to identify saved TRAIN incidents, recorded 2026-10-31

The Alberta suppression file was not downloaded after its public CSV endpoint returned
HTTP 403. To identify the jurisdiction/source needed for the three existing TRAIN pilot
cases, each case manifest's target-day summary centroid was queried against the official
BC Wildfire historical-perimeter layer, filtered to `FIRE_YEAR=2018`. Each point
intersected exactly one 2018 polygon:

| CFSDS case | Candidate BC incident | Fire date | Cause | Reported polygon area |
| --- | --- | --- | --- | ---: |
| `2018_1770` | N12395 | 2018-08-10 | Person | 955.7 ha |
| `2018_241` | C11937 | 2018-08-01 | Lightning | 13,433.1 ha |
| `2018_747` | N12413 | 2018-08-10 | Lightning | 713.7 ha |

These are **strong candidate spatial crosswalks**, not a shared ID join: CFSDS does not
carry the BC fire number, and the match uses the target-day centroid within a final
historical perimeter. Use them to locate BC event records and verify chronology before
updating the case manifest. The historical perimeters were captured after the simulated
target day and are identity evidence only; do not put them in the pre-target simulator
state or use them to choose a case.

**Decision:** search BC operational records using N12395, C11937 and N12413, then confirm
the incident identity from year/date/perimeter chronology. The perimeter layer records
fire date, cause, size and capture provenance, not crews, resources or daily actions; all
three suppression labels remain `unknown`. Alberta's file may still apply to other
TRAIN candidates after their jurisdiction is identified. No new FireCase, replay,
training or heldout inspection occurred.

Evidence: [crosswalk receipt](../../reports/real-fire-data/cfsds-train-bc-perimeter-crosswalk.json),
[input QC](../research/CFSDS_TRAIN_INPUT_QC.md),
[source register S-044](../research/SOURCES.md),
[BC historical perimeter layer](https://delivery.maps.gov.bc.ca/arcgis/rest/services/whse/bcgw_pub_whse_land_and_natural_resource/MapServer/6).

## ADR-028 — record partial BC operational evidence without promoting suppression labels, recorded 2026-10-31

A TRAIN-only search of public BC operational reporting followed the three candidate
incident numbers from ADR-027. A contemporaneous August 12 report relaying BC Wildfire
Service information documents containment-line work, five heavy-equipment units and
one helicopter at candidate Coal Creek fire N12395 on the `2018_1770` target date.
Reports for the Lost Dog Complex candidate N12413 describe a planned ignition and
complex-level resources on August 15, one day before the `2018_747` target; later
complex-level staffing/equipment is reported for August 17. For candidate North
Baezaeko C11937, the official August 16 PECC snapshot gives 2,500 ha and 0% contained,
but no crews or actions. That status does not prove suppression was absent.

The BC IDs are still spatial/date candidates without a shared CFSDS key. Local public
updates are snapshots, not a machine-readable dispatch log; complex-level resources
cannot be assigned to a single fire without evidence. **Decision:** preserve all saved
case-manifest suppression labels as `unknown`; record the dated observations separately.
Do not convert reported totals into simulator actions, cell-level treatment masks, or
proof of an action-free target. Observed growth where suppression is documented cannot
be treated as a direct no-action counterfactual. Continue searching for event-keyed
operational records and retain the limitations if none are available.

No FireCase, replay, calibration, benchmark, training, or heldout inspection occurred.
The input and fuel-vintage gates remain open.

Evidence: [operational evidence receipt](../../reports/real-fire-data/cfsds-train-bc-operational-evidence.json),
[input QC](../research/CFSDS_TRAIN_INPUT_QC.md),
[source register S-045–S-047](../research/SOURCES.md),
[BC Wildfire season summary](https://www2.gov.bc.ca/gov/content/safety/wildfire-status/about-bcws/wildfire-history/wildfire-season-summary),
[PECC Situation Report package](https://docs.openinfo.gov.bc.ca/Response_Package_PSS-2018-86747.pdf).
