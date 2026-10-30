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
