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

## ADR-016 — SimFire/FEDS benchmark i pre-agent crosswalk gate, accepted 2026-11-03

Korisnik je promijenio aktivni benchmark pravac: koristiti SimFire kao zajednički
simulator, postojeću FPA-FOD incidentnu kohortu spojiti sa FEDS-CONUS vremenskim
obodima, a FLE/ICS-209 koristiti kao post-hoc operativni kontekst. Test ostaje zatvoren.
Ova odluka superseduje ADR-013 kao aktivni plan za novu benchmark granu; raniji CFSDS/
Cell2Fire rezultati ostaju sačuvani kao historijska, odvojena putanja.

Prije porta simulatora ili treniranja važi fiksni crosswalk gate: najmanje 20 train i
8 validation požara moraju imati najmanje dva uzastopna FEDS stanja na 12h koraku.
Join koristi samo FPA-FOD discovery date, izvornu tačku i FEDS `t_st`; 3 km je fiksna
prostorna tolerancija, a datum prozor je -1/+2 dana. Završna površina/obod, FLE ishodi
i test događaji ne biraju FEDS ID. Spajanje ostaje provisional jer FPA tačka i datum
imaju nepoznatu event-level nesigurnost.

Audit 2026-11-03 našao je 17/40 train slučajeva sa jedinstvenim FEDS događajem; svih
17 ima ≥2 uzastopna stanja i ≥5 poludnevnih stanja. Validation ima 12/20 sa istim
vremenskim minimumom. Zato prag validation=8 prolazi, ali train=20 pada i cijeli gate
je **FAIL**. FLE summary je spojen za 0/40 train i 13/20 validation slučajeva; dostupni
ArcGIS rezultat je grupisani incidentni sažetak, ne line-level geometrija. SimFire
adapter, no-op gate, budžetske akcije i PPO nisu implementirani niti pokrenuti.

**Posljedica:** zaustaviti se prije agenta. Sljedeći posao je train-only refiniranje
FPA-FOD kohorte pod istim join pravilom, bez pristupa testu; ako se kohorta ili pravilo
moraju promijeniti, dodati novu odluku prije izmjene. FEDS-MTBS može biti zaseban,
endpoint-conditioned prikaz jer koristi konačni MTBS obod; ne predstavljati ga kao
nezavisnu zamjenu za FEDS-CONUS no-action gate. Dok se FLE stari ID-jevi ne razriješe,
sve politike dobijaju jednake standardne budžete i ne tvrdi se uzročna efikasnost
konkretne historijske linije.

Evidence: [FPA↔FEDS↔FLE crosswalk audit](../research/FPA_FEDS_CROSSWALK.md),
[kombinovani JSON](../../reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json),
[train/validation manifest](../../data/manifests/fireline-benchmark-cohort-v1.json).

## ADR-017 — strogi početni FEDS join i potvrda data gatea, recorded 2026-11-03

Prva eksplorativna crosswalk provjera je našla 17/40 train i 12/20 validation
slučajeva, ali je dozvoljavala da FEDS obod priđe FPA-FOD tački bilo kada u toku
požara. To nije dovoljno pouzdano za izbor početnog stanja simulatora. Ovaj ADR
bilježi stroži kriterij koji je primijenjen u ovom auditu (nije promjena korisnički
odobrenih pragova): kandidat mora imati barem jedan obod najviše 3 km od FPA-FOD tačke
između FEDS `t_st` i `t_st + 24 h` uključivo, uz isti FEDS start-date prozor -1/+2 dana
i jedinstveno poklapanje. Potom mora imati najmanje dva uzastopna 12h stanja. Pragovi
ostaju 20 train / 8 validation; završni obodi/površine i test i dalje su zabranjeni za
izbor kandidata.

Strogi audit nalazi 13/40 train i 7/20 validation događaja. Gate je **FAIL za oba
splita**. Train je manji od praga za 7, validation za 1. Validation rezultat je
deterministički izveden iz prethodno sačuvanog izvještaja kandidata: najranije vrijeme
unutar radiusa dovoljno je da primijeni novo 24h pravilo bez pristupa testu. Novi
mrežni upit nije uspio zbog nedostupnog Zenodo DNS-a; izvorni kandidatski izvještaj je
sačuvan i način postfiltriranja zabilježen. Ograničenje je evidentirano u izvještaju.

**Posljedica:** ne implementirati SimFire adapter niti pokretati no-op poređenje ili
trening dok nova, unaprijed definisana train/validation kohorta ili drugi izvor ne
zadovolji pragove. Ne podešavati radius, datum prozor ili prag na osnovu ishoda. Test
ostaje zatvoren. Potrebna je nova odluka prije izmjene splita ili eksperimentalnog
ugovora.

Evidence: [strogi FEDS crosswalk](../research/FPA_FEDS_CROSSWALK.md),
[combined JSON](../../reports/real-fire-data/fpa-feds-fle-crosswalk-v1.json),
[sačuvani kandidati](../../reports/real-fire-data/fpa-feds-fle-crosswalk-validation-candidate-search-v1.json).

## ADR-018 — prošireni FPA-FOD candidate frame nakon lokalnog crosswalk audita, provisional 2026-11-03

Kompletne FEDS `lf_perimeter` arhive za 2018, 2019. i 2023. preuzete su u ignorisani
`.local/` i provjerene službenim MD5 checksumima. Ponovljeni audit prvobitne 60-case
kohorte nalazi 19/40 train i 7/20 validation; prag 20/8 ostaje nepromijenjen i stari
uzorak zato ne prolazi.

Da se izbjegne proizvoljno dodavanje jednog požara nakon gledanja FEDS ishoda, aktivni
feasibility frame uzima sve redove iz unaprijed sačuvanih FPA-FOD screenova za iste
godine i split po požar-godini: 208 train 2018/2019, 56 validation 2023. Screen pravilo
je poznata lokacija/datum, MTBS ID, deset zapadnih država i prijavljena završna površina
≥5.000 acres. Posljednja dva ograničenja čine uzorak selektovanim za velike požare;
prijavljena površina ne bira FEDS fireID, ne ulazi u policy input/reward i nije metrika
benchmarka.

Pod istim ranijim vremensko-prostornim FEDS joinom, 99/208 train i 20/56 validation
kandidata imaju jedinstven match i najmanje dva uzastopna 12h stanja. Svih 119 imaju
pet očekivanih 12h stanja od početnog opažanja do +48h, pa širi frame prolazi pre-agent
coverage gate. FPA/FEDS mapiranje ostaje provisional zbog nesigurne incidentne tačke i
vremena; FEDS obodi su satelitske procjene. Test 2024 nije preuzet ni učitan.

**Posljedica:** nastaviti samo na širem, jasno označenom candidate frame-u do train-only
no-op replay gatea. Originalni 60-case rezultat i dalje je sačuvan i ne prolazi. Ne
počinjati PPO trening dok SimFire no-op ne uporedi observed growth s persistence i
elipsnom referencom te ne prođe map-boundary/QC provjere. Ovaj ADR mijenja cohort frame,
ne pragove, join pravilo, test pristup ni zaključak da benchmark rezultat važi unutar
simulatora, a ne kao stvarna causalna korist.

Evidence: [kandidat-frame manifest](../../data/manifests/fpa-feds-candidate-frame-v1.json),
[119-case episode manifest](../../data/manifests/feds-episode-cohort-v1.json),
[novi crosswalk](../../reports/real-fire-data/fpa-feds-candidate-frame-crosswalk-v1.json),
[originalna kohorta lokalno ponovljena](../../reports/real-fire-data/fpa-feds-original-cohort-crosswalk-local-v1.json),
[FEDS/SimFire environment record](../research/SIMFIRE_ENVIRONMENT.md).

## ADR-019 — SimFire/FEDS prostorna mreža, weather granica i setup gate, accepted 2026-11-03

FEDS početno stanje rasterizuje se na 256×256 ćelija od 180m u UTM projekciji,
centrirano na centroidu tačnog početnog `lf_perimeter` stanja. Početni poligon čuva
kumulativni burn scar; tačni `fireID+t` `lf_fireline` segmenti postaju burning ćelije.
FEDS ulazna nominalna rezolucija ostaje 375m i ne predstavlja se kao 180m ground truth.
Preflight koji uključuje samo početna stanja potvrđuje da svih 119 train/validation
požara stane u mrežu; eventualni neuspjeh izvatka ili fuel kodova mora se prijaviti.

gridMET se koristi kao dnevni, ex-post simulator forcing na četiri 12h segmenta kroz
48h. FEDS naive `t` pretpostavlja se UTC, a gridMET day label računa po njegovoj MST
granici; budući dnevni weather segmenti se ne daju agentu kao observation niti se
predstavljaju kao operativna prognoza. `th` NetCDF varijabla je `wind_from_direction`;
adapter je rotira za 180° radi SimFire downstream smjera. `vs` m/s i `fm100` procenti
pretvaraju se uz eksplicitan wind-adjustment faktor i procenat/razlomak konverziju.
Faktor još nije izabran i ne smije se fitovati prema svakom požaru posebno.

Uspješan one-hour Plateau smoke koristi demonstracijski vjetar/vlagu i potvrđuje samo
da SimFire v2 prima multi-cell scar/front i LANDFIRE mape. U smoke configu aktivno
trajanje ćelije je 90 update-a, što je šestostruko skaliranje 15 update-a prema omjeru
180m/30m, a ne fit prema opaženom budućem obodu. Ovo nije no-op gate.

**Posljedica:** prije PPO implementirati train-only 48h no-op replay, persistence i
zajedničku elipsnu referencu, te map-edge/area provjere. Zajedničke postavke se zaključaju
na trainu, validation se koristi samo za izbor, a 2024 test ostaje zatvoren. Ako no-op
ne nadmaši reference ili sistematski udara rub, zaustaviti agentni trening i prvo
dijagnosticirati kalibraciju ili podatke.

Evidence: [active-front audit](../../reports/real-fire-data/feds-active-front-coverage-v1.json),
[grid preflight](../../reports/real-fire-data/feds-simfire-grid-preflight-v1.json),
[gridMET archive coverage](../../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json),
[one-case SimFire smoke](../../reports/real-fire-data/feds-simfire-input-smoke-v1.json),
[environment record](../research/SIMFIRE_ENVIRONMENT.md).

## ADR-020 — train-only no-op diagnostics and unselected timebase, provisional 2026-11-03

All 99 train FEDS starts now have checksum-audited LANDFIRE FBFM13 and LF2020 elevation
maps on the fixed 256×256/180m grid. A historical-weather 48h no-op runner updates
SimFire from gridMET at 12h intervals and scores cumulative burn against future FEDS
perimeters only after each segment.

A single Plateau train case is highly sensitive to wind adjustment: WAF 0.20–0.60
produces only three new cells and 61.56ha; WAF .65 produces 1,244ha by +12h, and .75–1.0
overgrow substantially and eventually touch the map edge. This is an exploratory
single-event diagnostic, not evidence about the whole cohort and not a valid setting.
No WAF is selected. A 5-minute internal step preserves the nominal 90-minute active-cell
lifetime as 18 updates; the high-spread 48h pilot on this step took about 40 seconds,
while agent decision cadence remains 12h. The 5-minute timestep is also unselected
pending train-only cohort comparison.

**Posljedica:** do not use either pilot setting for validation selection or RL. Calibrate
a small shared parameter set and choose the internal timestep using TRAIN rollouts,
compare no-op with persistence and a prespecified ellipse, then fetch validation maps
and evaluate frozen settings. Stop before PPO if the calibrated no-op misses those
baselines or exhibits map-edge artifacts. 2024 remains closed.

Evidence: [99-case train input coverage](../../reports/real-fire-data/feds-simfire-input-train-coverage-v1.json),
[single-case parameter pilot](../../reports/real-fire-data/feds-simfire-noop-pilot-v1.json),
[runner](../../scripts/run_feds_noop_episode.py),
[environment record](../research/SIMFIRE_ENVIRONMENT.md).

## ADR-021 — expose a TRAIN-only PPO execution path before benchmark calibration, accepted 2026-11-03

At the user's direct request, make it possible to run local PPO training now rather than
leave the project in another setup-only cycle. This is an execution-path decision, not
an acceptance of SimFire calibration or scientific validity. The existing no-op gate
and the unselected shared wind/timebase remain open for any benchmark, baseline, or
policy-benefit claim.

The new `FedsSimFireEnv` samples only the 99 manifest TRAIN cases, runs four 12h
decisions over 48h, and never loads future FEDS outlines for observation or reward.
Its current discrete prototype is no-op plus eight directional short fireline actions;
each line costs one budget unit, no-op stays available at zero budget, cumulative burn
is preserved, and the episode continues after budget exhaustion or fire extinction.
The CPU CLI trains a fresh MaskablePPO and stores checkpoints under ignored `.local/`.
The chosen wind factor is required explicitly and remains labeled provisional.

The bounded 64-step training smoke is only a runtime proof. Validation maps remain
unfetched, the 2024 TEST split remains closed, and this technical path does not replace
TRAIN-only no-op comparison against persistence and a predeclared ellipse.

Evidence: [environment record and command](../research/SIMFIRE_ENVIRONMENT.md),
[environment](../../src/wildfire_rl/feds_simfire_env.py),
[training CLI](../../scripts/train_feds_simfire.py),
[budget/damage tests](../../tests/test_feds_simfire_env.py).

## ADR-022 — TRAIN no-op screen fails; no shared WAF accepted, recorded 2026-11-03

Completed the paired historical-weather no-op screen over all 99 manifest TRAIN cases
for WAF `0, 0.0025, 0.01, 0.025, 0.05, 0.10, 0.20, 0.605`, with seed 0, 5-minute
internal updates, four 12-hour forcing segments, and 48-hour episodes. Each candidate
has 396 scored case-timepoints and 99/99 successful cases. The future FEDS perimeters
are loaded only after each simulator episode and used only for scoring.

The reference scores are mean IoU .5343 / mean absolute area error 2,351.7ha for
persistence and .5308 / 2,346.6ha for the fixed 2:1 ellipse. The best candidate mean
IoU is .4769 (WAF .0025); the lowest candidate area error is 2,262.1ha (WAF .01). High
WAF values create map-edge artifacts; low WAF values avoid the edge but remain materially
below both references on IoU. **No candidate satisfies the screen** (complete cohort,
zero edge contacts, and better mean IoU plus lower area error than both references). No
WAF or internal timestep is accepted.

**Consequence:** technical PPO smoke remains possible, but benchmark/policy-benefit
training is blocked. Diagnose shared forcing, rasterization, and SimFire response; then
repeat the unchanged TRAIN gate with an explicitly documented candidate set. Do not
fetch validation maps until a TRAIN candidate passes and settings are frozen; keep 2024
TEST closed. This is a TRAIN-only model screen, not physical validation because FEDS
perimeters are satellite-derived estimates and gridMET values are coarse proxies.

A follow-up sensitivity run at WAF .01 with a 1-minute internal step also completed
99/99 cases with no edge contact and mean IoU .4771, effectively unchanged from .4769
at 5 minutes. The supported 3/10/15-minute steps were not run; no timebase is selected.

Evidence: [cohort screen report](../../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json),
[environment record](../research/SIMFIRE_ENVIRONMENT.md),
[TRAIN evaluator](../../scripts/evaluate_feds_train_noop.py).

## ADR-023 — diagnosed no-op deficit and preregistered spread-threshold candidates, accepted 2026-11-04

Under the user's overnight mandate (2026-11-03: work through roadmap steps 5–8 without
questions; if the gate fails again, continue clearly labelled as exploratory), the
TRAIN inputs were rebuilt on a second machine. All 99 LANDFIRE fuel/elevation/start-mask
hashes and all nine gridMET archive hashes equal the committed reports, and the WAF .01
cohort rerun reproduces ADR-022 exactly (mean IoU .476852, area error 2,262.1ha).

[Diagnosis](../../reports/real-fire-data/feds-simfire-train-noop-diagnosis-v1.json):
the entire mean-IoU deficit sits in the third of timepoints where FEDS barely grows
(observed/initial ≤1.36). There SimFire adds ~262 cells against ~59 observed, with 2.9%
precision. In the fastest-growing third SimFire already beats persistence (+.035).
Even at WAF .01 SimFire grows in 63% of timepoints regardless of observed growth. The
failure is discrimination of *which* fires grow, not heading. Many static FEDS fires were
probably contained or suppressed, which a free-burning no-op cannot represent.

SimFire ignites a neighbour only when accumulated spread exceeds the 180 m cell within
the active-cell lifetime (90 min), i.e. R ≥ ~6.6 ft/min. A shared rate-of-spread
multiplier below one therefore acts as a spread threshold: weak no-wind/slope spread
stops, while windier or drier segments still grow. The preregistered set, fixed before
any run, is the 3×3 grid `ros_multiplier ∈ {0.35, 0.5, 0.7}` × `WAF ∈ {0.05, 0.2,
0.4}`, with lifetime 90 min, 5-min internal step and seed 0, scored with the unchanged
strict rule and unchanged persistence/ellipse references.

**Selection rule:** if any candidate passes, freeze the passing candidate with the highest
mean IoU (tie: lower area error). If none passes, freeze the zero-edge candidate with the
highest mean IoU among these nine plus the reproduced WAF .01/ROS 1.0 run, labelled
`gate_status: FAIL_exploratory`; steps 6–8 then proceed as exploratory only. Validation
is scored once with the frozen record and is not used for re-selection. 2024 TEST stays
closed.

Evidence: [diagnosis tool](../../scripts/diagnose_feds_noop_gate.py),
[shared setup](../../src/wildfire_rl/feds_simfire_setup.py),
[evaluator](../../scripts/evaluate_feds_train_noop.py).

## ADR-024 — gate result frozen as FAIL; separate free-burn stress scenario for steps 7–8, accepted 2026-11-04

None of the nine ADR-023 candidates passed. The best zero-edge candidate, ROS 0.35 /
WAF 0.05, reaches mean IoU .5266 and area error 2,350.5ha against persistence .5343 /
2,351.7ha and the ellipse .5308 / 2,346.6ha. By the preregistered rule it is frozen in
[the gate freeze record](../../configs/frozen/feds-simfire-gate-freeze-v1.json) as
`FAIL_exploratory`. Higher WAF or ROS created map-edge contacts and lower IoU.

That frozen setting approaches persistence by suppressing spread: on TRAIN the median
fire adds 0 cells in 48h, only 30/99 fires grow at all and 2/99 add ≥50 cells. A fireline
benchmark on it cannot discriminate policies, because there is almost nothing to stop.
The gate itself is structurally biased toward persistence: many FEDS fires were
evidently contained, while a no-op simulator burns freely.

So steps 7–8 use a second, separately labelled **free-burn stress scenario**, chosen from
no-op statistics only and before any policy run: the zero-edge TRAIN candidate with the
lowest mean absolute area error across ADR-022/023 and the reproduction, i.e. WAF .01 /
ROS 1.0 / 90-min lifetime / 5-min step (2,262.1ha, below both references; IoU .4769,
below both). [Stress record](../../configs/frozen/feds-simfire-stress-scenario-v1.json),
`gate_status: FAIL_stress_scenario`. Results on it are simulator policy comparisons, not
calibrated or physically validated suppression effects.

Both records are scored once on VALIDATION no-op and are not re-selected afterwards. Note
for the audit trail: the validation LANDFIRE fetch was started about one minute before the
gate freeze commit; no validation case was simulated or scored before either record was
committed. 2024 TEST remains closed.

**Consequence / recommendation for the team (not adopted here):** consider a growth-aware
gate (e.g. scored only on fires that FEDS shows growing, or with a containment model)
before treating any no-op setting as calibrated.

## ADR-025 — step-7 intervention unit, matched heuristics and paired benchmark, accepted 2026-11-04

**Budget unit.** One unit is one 20-person handcrew shift. It builds one straight fireline
segment of seven 180 m cells: about 1.26 km on an axis, up to about 1.8 km diagonally.
NWCG sustained production tables for 20-person crews list roughly 2–15 chains/h
(about 40–300 m/h) depending on fuel and crew type, i.e. about 0.3–2.4 km per 8h shift
([NWCG Firefighter Math 9.8 / PMS 410-1 Appendix A](https://www.nwcg.gov/course/ffm/math-terms-and-statistics/98-production-rates),
consulted 2026-11-04 through search excerpts; the tables are based on pre-1980 sources
and real rates vary widely). The segment length sits inside that range. Line is placed
instantly at the 12h decision; travel time, build-over-time, holding, burnout and line
failure are not modelled. This simplifies TASK-020 (16 sectors, crew-hours over time).
That remains future work.

**Action and placement.** Discrete(9): no-op or one of eight sectors. The new
`front_edge` placement anchors the segment two cells (360 m) beyond the active-front cell
that leads in the chosen sector, perpendicular to it. Only unburned cells receive line.
The older centroid placement is kept for the earlier smoke. Budgets per 48h episode are
0, 1, 2 and 4; at most one line per 12h decision; no-op always legal; the episode always
runs four decisions. Damage is SimFire cumulative burned area added after the FEDS start;
the reward is its negative (cells/100). Future FEDS outlines are never used.

**Matched heuristics** decide from the same observation dictionary and action mask as
PPO, never the full-resolution map: no-op, uniformly random legal line, downwind (current
12h wind-to heading) and advancing-front (pooled burned-area centroid → active-front
centroid). Each spends a unit at the first legal opportunity.

**Benchmark** ([script](../../scripts/benchmark_feds_policies.py)): every policy runs on the
same scenarios, budgets, horizon, simulator record and seed, paired by scenario. At B=0
every policy must reproduce no-op exactly (determinism check). VALIDATION requires a
TRAIN freeze record. A smoke on seven TRAIN cases passed the B=0 check.

## ADR-026 — step-8 budget-adaptation protocol, accepted 2026-11-04 (before any policy result)

Simulator: the ADR-024 free-burn stress record only. Training uses the 99 TRAIN cases;
evaluation uses the 20 VALIDATION cases once; TEST stays closed.

- **Base ("pretrained") policy:** MaskablePPO from scratch at reference budget B=2, 8,064
  decisions (7 parallel envs × 16-step rollouts, batch 56, 4 epochs, γ=1, lr 3e-4,
  entropy 0.01, MLP 64×64, observation budget scale fixed at 4).
- **Adaptation:** each base is fine-tuned for 3,024 decisions at B=1 and at B=4. The
  **matched control** is the same-length fine-tune at B=2, which separates "more training"
  from "budget-specific adaptation".
- **Seeds:** 11, 12 and 13 in the first round. Measured throughput (16.7 min per base) leaves
  room for seeds 14 and 15; they are added now, before any evaluation, and run
  unconditionally if time allows. The report states how many seeds finished.
- **Evaluation:** paired by VALIDATION scenario at B ∈ {0,1,2,4} for no-op, the ADR-025
  heuristics, every frozen base and every fine-tune (deterministic actions). Primary
  contrasts: fine-tuned-at-B minus frozen base at B, and fine-tuned-at-B minus matched
  control at B, for B ∈ {1,4}. Seed-averaged scenario bootstrap 95% intervals; per-seed means
  reported too. B=0 must reproduce no-op exactly.
- Compute: local CPU only, about 6–8k decisions/h per process group. This is a small,
  underpowered study; null or negative results are reported as such.

## ADR-027 — step-8 result: base PPO helps, budget fine-tuning shows no gain, recorded 2026-11-04

The ADR-026 protocol ran to completion: five seeds (11–15), each with a base PPO at B=2
(8,064 decisions) and three 3,024-decision fine-tunes (B=1, B=4, matched control B=2),
for 20 policies. With no-op and the three ADR-025 heuristics, that is 24 policies × 20
VALIDATION fires × 4 budgets = 1,920 paired episodes, with no errors. At B=0 every policy
equals no-op; the 1,280 episodes shared with an earlier three-seed pass are bit-identical.

On the free-burn stress scenario, no-op adds 324.3ha per fire on average. Seed-averaged
deltas (scenario bootstrap 95% CI):

| Contrast | B=1 | B=2 | B=4 |
|---|---|---|---|
| frozen base − no-op | −5.1 [−10.9, −0.4] | −16.6 [−35.4, −3.7] | −19.7 [−42.0, −4.1] |
| fine-tuned − frozen base | −0.4 [−1.2, 0.4] | +1.3 [−3.0, 6.8] (control) | +0.6 [−1.5, 2.3] |
| fine-tuned − matched control | +0.9 [−1.3, 3.6] | — | −1.6 [−8.7, 4.1] |
| downwind heuristic − no-op | −9.1 [−21.7, 0.0] | −28.0 [−69.7, −0.2] | −28.0 [−69.7, −0.2] |

**Reading:** a learned policy beats doing nothing in this simulator, but budget-specific
fine-tuning gives no measurable benefit over the frozen base or over equal extra training.
A simple downwind rule is at least as good as PPO. Per-seed results differ widely, and
several seeds converge on downwind-like behaviour. Most simulated fires stop within 12h
(90-min active cells), so extra budget rarely finds a legal placement. That, the
single-segment action and 20 scenarios bound this null result. It is a simulator
finding, not evidence about real suppression.

Evidence: [benchmark summary and training receipts](../../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json),
[figure](../../reports/real-fire-data/feds-simfire-policy-benchmark-v1.png),
[analysis](../../scripts/analyze_budget_adaptation.py).

### ADR-027 addendum — seed-level intervals, recorded 2026-11-04

The ADR-027 table intervals resample scenarios after averaging seeds, so they omit
seed-to-seed variation, which dominates here. Recomputed on the same 1,920 episodes
(no new simulation), with a two-level bootstrap over seeds then scenarios (95%):

| Contrast | B=1 | B=2 | B=4 |
|---|---|---|---|
| frozen base − no-op | −5.1 [−13.2, +0.5] | −16.6 [−43.0, −2.8] | −19.7 [−46.7, −3.1] |
| fine-tuned − frozen base | −0.4 [−5.4, +3.8] | +1.3 [−17.9, +20.9] (control) | +0.6 [−14.5, +15.6] |
| fine-tuned − matched control | +0.9 [−4.8, +8.3] | — | −1.6 [−17.8, +15.2] |

Corrected reading: the base policy's benefit over no-op holds at B=2 and B=4 and is
marginal at B=1. Budget fine-tuning shows no measurable gain, but with five seeds effects
of roughly ±12–20ha at B=2/4 cannot be excluded. These intervals, and the per-seed t-intervals in the
[summary](../../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json), are the ones to quote.

In-sample supplement (same day, after the VALIDATION result, TRAIN only): on all 99 TRAIN
fires (9,504 episodes) the frozen base again beats no-op (−35.9/−71.3/−99.8ha at B=1/2/4
against 1,343.6ha). Fine-tuning again shows no gain (two-level CIs span zero), and downwind
is at least as good. Budget fine-tuning does not help even on the fires it was trained on,
so the null is not an overfitting artefact. It points to a weak budget signal in this action
and simulator design.

### ADR-024 addendum — verbatim approval and validation-use rule, recorded 2026-11-04

The user's words in the session, verbatim (2026-11-03, about 23:50 CET):

- Request: "da do 6 ujutro pokusas uraditi do (i ukljucujuci) 8. zadatka da li mislis da
  bi to mogao da uradis, koristeci internet resurse, lokalne resurse koje imas, i
  pokusavajuci da napredujes ka tome da uradis to najbolje sto mozes" and "da mene ne
  pitas nista jer necu biti tu da odgovorim".
- The option proposed to them, including the starred defaults: "Ako gate ponovo padne: ★
  nastavljam korake 6–8 sa najboljim TRAIN kandidatom, jasno označeno kao *eksploratorno,
  gate FAIL*." Downloads: "★ dozvoljeni validation LANDFIRE/FEDS rasteri, ako gate prođe ili
  po tački 1".
- Reply: "potvrdjujem sve sto si rekao".

**Validation-use rule:** every VALIDATION result was produced after the TRAIN gate failed
and was **not** used to choose candidates, tune parameters, or decide that the gate
passes. The stress record was chosen from TRAIN no-op statistics before any validation
scoring. If a later TASK-019 fix makes the TRAIN gate pass, rerun the gate on TRAIN first,
then validation, and mark the exploratory step 6–8 results superseded.

## ADR-028 — synthetic CA training with physically bounded units; real FEDS cases only for the final test, accepted 2026-11-04

The user asked on 2026-11-04 to stop training on real cases and to train and validate
on synthetic fires whose spread probability depends on cell fuel type. Units must obey
real-world limits: finite count, no teleporting, bounded line production. Human life
has priority. Real cases are kept for testing the trained agent. The previous path
(ADR-021–027) trained on real FEDS cases in an uncalibrated SimFire and placed line
instantly in 12h steps, so its policy results cannot support a transfer claim.

Decision:
- **Simulator.** A new numpy CA ([spec](../research/SYNTHETIC_CA_ENV.md)) on 180 m
  FBFM13 grids. Per-pair contact rates come from Anderson (1982) ROS with a
  Rothermel-style wind term and an Alexandridis-style slope term. A contact calibration
  makes the emergent head rate on flat line fires match the table within about 15%.
  It is a training simulator, not a validated fire model.
- **Data roles.** Training uses procedurally generated landscapes, weather and ignitions
  (seed ≥ 1,000,000). In-training validation uses fixed seeds 0–255. The 119 local FEDS
  cases (99 ex-TRAIN, 20 ex-VALIDATION, reported separately) are touched only by the
  final test of locked policies, plus a calibration-gap diagnostic (no-op versus FEDS
  growth) that is reported but never used as a gate. TEST 2024 stays closed.
- **Units.** 20-person hand crews and dozers. Line rates come from PMS 410-1 App. A,
  travel speeds from Sullivan et al. 2020 or stated assumptions. Units arrive over time
  2–4 km from the fire, cannot enter burning cells or water, retreat automatically
  when fire is within two cells, and are lost if their cell ignites.
- **Reward.** The user's intent ("reward lower fire growth, penalise same or higher")
  is implemented counterfactually. `r_t = (D_noop,t − D_agent,t) / max(W_noop, 20) −
  1.0 × units lost`. D is weighted new damage (vegetation 1, urban 91 = 50), and the
  no-op rollout uses common random numbers. The episode return is the fraction of no-op
  damage saved. Both rollouts continue 12h past the horizon with lines held, so merely
  delaying the fire earns nothing. A literal growth-trend reward would telescope and
  pay for natural burnout; it is not used.
- **Headroom gate before PPO (preregistered here).** On synthetic validation seeds
  0–127 (full curriculum), the best scripted tactic must reach a mean saved fraction
  ≥ 0.05, with a paired bootstrap 95% CI for (best − random) above 0. If this fails, unit
  or simulator settings change first, not the RL setup.
- **PPO acceptance (preregistered here).** A checkpoint is chosen only by synthetic
  validation. It counts as learned if, on validation seeds 0–255, its mean return beats
  the best scripted tactic with a paired 95% CI above 0 and it loses no more units than
  that tactic. The real-case test is then run once per locked checkpoint.

Consequences: results are simulator-only. The calibration gap to FEDS growth bounds any
real-world reading. The old SimFire/FEDS path remains historical and unchanged.

### ADR-028 addendum — headroom gate history, recorded 2026-11-04

All runs use synthetic validation seeds 0–127 on the full curriculum, scored as the
paired saved fraction against the random policy.

| Version | Environment change | Best tactic, mean saved | CI (best − random) | Units lost (best) |
|---|---|---|---|---|
| v1 | as accepted | direct flank 0.058 | [0.026, 0.086] | 16 |
| v2 | resample fires whose no-op adds < 30 cells (the v1 median was 15 cells) | 0.117 | — | 33 |
| v3 | BFS escape at 4 cells | 0.029 | — | 31 |
| v4 | overrun with an open neighbour = close call (−0.1, displaced); surrounded = loss (−1.0); escape at 2 cells | **0.116** | **[0.069, 0.135]** | **0** |

v1 passed narrowly, but half of its episodes carried no signal. v2 to v4 change the
environment, not the gate. The 180 m cell is far wider than the tabled flame length (at
most ~6 m, Anderson 1982), so working next to the fire edge is realistic. Only being
surrounded is treated as an entrapment. **Gate: PASS on v4.** PPO training uses v4.

### ADR-028 addendum — validation bar, stop rule and selection bias, recorded 2026-11-04 (main-1 at 200k steps)

- **Comparable bar.** The training callback validates on seeds 0–63 with the full
  curriculum on the current environment, which includes the per-variant staging key.
  The heuristics measured on the same seeds and environment:

  | Policy | Mean saved | Mean return |
  |---|---|---|
  | direct_flank | 0.087 | **0.062** |
  | protect_urban | 0.062 | 0.045 |
  | downwind_indirect | 0.040 | 0.030 |
  | random | 0.010 | −0.007 |
  | no-op | 0 | −0.017 |

  The v4 headroom figure of 0.116 used seeds 0–127 before the staging change and is not
  this bar.
- **Stop rule for main-1 (written before the 300k result).** Stage B starts at 450k, so
  judge only from 600k onward. If three consecutive validations bring no new best and the
  best validation return is still below direct_flank's 0.062, stop main-1 and switch to
  plan B. Plan B is a behaviour-cloning warm start: copy direct_flank (plus
  protect_urban) actions on training seeds ≥ 1M only, then MaskablePPO fine-tuning with
  the same environment and reward. Documentation must then say that the policy starts
  from the scripted tactic.
- **Selection bias.** The best checkpoint is chosen on seeds 0–63, while acceptance runs
  on 0–255, which contains them. Acceptance stays as preregistered, and 64–255 is also
  reported as the selection-free result.

### ADR-028 addendum — main-1 result: FAIL against the best heuristic, recorded 2026-11-05

The main-1 run used MaskablePPO with 1.5M steps (stage A to 450k, then B), 6 environments,
fire reuse ×4 and about 4.3h of compute. Validation return on seeds 0–63 went 0.037
(100k), 0.024 (400k), 0.038 (800k), 0.044 (1.1M), **0.058 (1.2M, best)** and 0.035
(1.5M). The stop rule never triggered, because a new best kept arriving.

A diagnosis at 400k showed the policy built more line than direct_flank (613 versus 242
cells on 12 seeds), but with a median distance to the fire of 14 cells against 3. Most
of its line was therefore too far away to matter within the horizon, which is a
credit-assignment failure.

Acceptance (preregistered) on seeds 0–255, best checkpoint, deterministic:

| Policy | Mean return | Mean saved | Units lost |
|---|---|---|---|
| direct_flank | **0.088** | 0.123 | 0 |
| protect_urban | 0.062 | 0.088 | 0 |
| PPO main-1 | 0.047 | 0.052 | 0 |
| downwind_indirect | 0.031 | 0.051 | 1 |
| random | 0.010 | 0.020 | 1 |
| no-op | −0.010 | 0 | 2 |

PPO − direct_flank = −0.042, 95% CI [−0.071, −0.012]. On the selection-free seeds 64–255
it is −0.054, CI [−0.091, −0.019]. **FAIL.** The learned policy beats random and
downwind_indirect and loses no units, but it is worse than the simple flank rule. Per
the stop-rule addendum the next step is plan B: a behaviour-cloning warm start from
direct_flank, the best tactic, on training seeds ≥ 500M only, then PPO fine-tuning.
Evidence: [acceptance report](../../reports/synthetic/acceptance-main1-best.json),
[validation curve](../../reports/synthetic/main-1-validation.jsonl).

### ADR-028 addendum — plan B: BC warm start and fine-tuning, recorded 2026-11-05 (before fine-tune results)

- **bc-2.** Behaviour cloning of direct_flank, initialised from main-1 final weights. 40
  rounds × 42 episodes on training seeds ≥ 500M; each fit uses the last 3 rounds, 8
  epochs, lr 1e-3. Agreement with the teacher on slots that had a real choice reached
  about 95–96%. A first attempt (bc-1) took too few gradient steps and was stopped at 41%.
- **bc-2 on validation seeds 0–63:** return 0.093 (saved 0.115, 0 units lost), against
  direct_flank's 0.062. The clone outperforms its teacher on these seeds.
- **ft-1.** MaskablePPO fine-tuning from bc-2, stage B only, 600k steps, lr 1e-4, entropy
  0.001, clip 0.1.
- **Candidate selection.** The candidates are bc-2 itself and every ft-1 validation
  checkpoint. The one with the highest return on seeds 0–63 is locked and goes through the
  preregistered acceptance on 0–255, with 64–255 reported as the selection-free result.
- **Reporting.** Documentation must say the policy starts from the scripted tactic.

### ADR-028 addendum — policy-v1 locked; acceptance FAIL (tie with direct_flank), recorded 2026-11-05

The ft-1 validation return on seeds 0–63 was 0.086, **0.109** (200k), 0.088, 0.087, 0.065
and 0.101 (600k). The 200k checkpoint beats bc-2 (0.093) and is locked as
`policy-v1` (sha256 `701ccce2…6ad9`, [hash file](../../reports/synthetic/policy-v1.sha256)).

Acceptance on seeds 0–255 (paired, deterministic):

| Policy | Return | Saved | Units lost | Close calls |
|---|---|---|---|---|
| policy-v1 | **0.091** | 0.122 | 1 | 70 |
| bc-2 | 0.090 | 0.118 | 0 | 72 |
| direct_flank | 0.088 | 0.123 | 0 | 90 |
| protect_urban | 0.062 | 0.088 | 0 | 66 |
| downwind_indirect | 0.031 | 0.051 | 1 | 42 |
| random | 0.010 | 0.020 | 1 | 14 |
| no-op | −0.010 | 0 | 2 | 5 |

- **Against direct_flank:** policy-v1 − direct_flank = +0.003, CI [−0.026, +0.032],
  wins 102 and losses 111. On selection-free seeds 64–255 it is −0.012, CI [−0.047,
  +0.021]. Policy-v1 also loses one unit more. **FAIL**: the learned policy is
  statistically tied with its teacher. The 0.109 measured on 0–63 was inflated by
  selection.
- **Against no-op:** +0.101, CI [0.075, 0.129], wins 162 and losses 38. The agent clearly
  reduces simulated damage relative to doing nothing.
- **Next step.** Per ADR-028 the locked checkpoint is now tested once on the 119 real
  cases, and the calibration-gap diagnostic is run. The real cases did not influence any
  training, selection or simulator setting up to this point.

Evidence: [acceptance report](../../reports/synthetic/acceptance-policy-v1.json),
[ft-1 validation](../../reports/synthetic/ft-1-validation.jsonl).

### ADR-028 addendum — one-time real-case test and calibration gap, recorded 2026-11-05

Locked checkpoints (policy-v1, plus bc-2 and main-1 best for reference) were tested once
on the 119 local FEDS cases. Each case uses its real LANDFIRE fuel and terrain, gridMET
weather and initial FEDS perimeter. The CA computes the outcome, with 48h + 12h tail and
the same units for every policy: 2 dozers and 2 hand crews arriving at 30–120 min.

| Contrast (all 119) | Saved fraction | Return |
|---|---|---|
| policy-v1 − no-op | **+0.120** [0.089, 0.154], wins 100 / losses 2 | +0.076 [0.040, 0.115] |
| policy-v1 − direct_flank | +0.002 [−0.026, 0.031] | **+0.048** [0.012, 0.084] |
| policy-v1 − protect_urban | +0.034 [0.008, 0.062] | +0.052 [0.015, 0.088] |

- **Groups.** Ex-train (99) and ex-validation (20) point the same way. The 20-case
  intervals are wide.
- **Return.** The return advantage over direct_flank comes from safety: 53 close calls
  against 107, with no units lost by either. The saved area is the same.
- **Totals.** Urban cells burned: no-op 1,623, direct_flank 1,543, policy-v1 1,513.
  Saved area: policy-v1 about 56,000 ha, direct_flank about 60,000 ha.
- **Caveats.** In 34 of 119 cases the no-op fire reaches the crop edge, and 4 cases have
  initial cells outside the crop.

Calibration gap: the no-op CA compared with the observed FEDS perimeters. This is a
diagnostic only, never a gate, and it was run after locking.

| Hour | Median sim/obs area (ex-train / ex-val) | Median IoU | Sim grows more |
|---|---|---|---|
| 12 | 1.29 / 1.00 | 0.52 / 0.58 | 67% / 50% |
| 24 | 1.25 / 1.11 | 0.35 / 0.38 | 66% / 60% |
| 48 | 1.60 / 1.24 | 0.27 / 0.30 | 65% / 65% |

The simulator overgrows the typical real fire, which is expected for unsuppressed spread
against suppressed reality. It undergrows about a third of the cases.

**Reading.** In the CA, on real landscapes, weather and ignitions it never trained on,
the agent trained only on synthetic fires keeps its synthetic behaviour. It clearly
beats doing nothing and matches the best scripted tactic in saved area with fewer
close calls. It did not pass the preregistered synthetic acceptance against
direct_flank. The outcomes are simulated, the simulator is uncalibrated (median IoU
0.27–0.30 at 48h), and nothing here is evidence about real suppression.
Evidence: [real-case test](../../reports/synthetic/real-cases-test-v1.json),
[calibration gap](../../reports/synthetic/calibration-gap-v1.json).

### ADR-028 addendum — real-case exposure and edge sensitivity, recorded 2026-11-05

- **Exposure before locking.** Before policy-v1 was locked, all 119 real cases were
  loaded for shape, fuel-code and crop checks. One train case (plateau) was smoke-run
  through the gap diagnostic (no-op only) to test the script. No simulator, reward,
  training or selection setting was changed after that.
- **Edge sensitivity.** The test was recomputed from the same report on the 85 cases
  where the no-op fire never reaches the crop edge and no initial cells lie outside the
  crop:

  | Contrast (85 cases) | Saved fraction | Return |
  |---|---|---|
  | policy-v1 − no-op | +0.149 [0.110, 0.193], wins 67 / losses 2 | +0.119 [0.078, 0.165] |
  | policy-v1 − direct_flank | +0.017 [−0.019, 0.054] | +0.044 [0.000, 0.087] |

  - Close calls: 26 against 49. Units lost: 0 against 0.
  - Saved area: 35,400 ha against 32,900 ha, out of 223,200 ha of no-op damage.
- **Conclusion.** The headline holds without the edge cases.

## ADR-029 — results of ADR-022 to ADR-028 invalid pending rerun; remediation plan, recorded 2026-11-09

A review of PRs #3–#5 (2026-11-09) found a data bug that affects every SimFire and CA
result built on real FEDS starts. This ADR supersedes the *results* of ADR-022 through
ADR-028 (including all ADR-028 addenda). Their protocols, code and preregistrations stay
as history; their numbers must not be cited as findings until rerun.

**The bug (fixed).** `scripts/sample_gridmet_episode_weather.py` cached the nearest gridMET
cell per (year, variable) and reused the first case's cell for every later case of that
year. The committed-era weather file had one cell per year: 97/99 TRAIN and 19/20
VALIDATION episodes got weather from another fire (median 782 km, max 1,774 km away). The
fix (commit e18a265, merged with PR #3) selects the cell per case, records its distance and
refuses cells beyond 5 km; a local regeneration gives 118 distinct cells for 119 cases
(two FPA records share one FEDS fire) and a maximum distance of 2.8 km. The old ignored
`.local/gridmet/feds-episode-weather-v1.json` (sha256 `7b0aa405…`) is the defective file.

**What this invalidates.**
- ADR-022 and ADR-023/024: SimFire gate numbers for all WAF/ROS candidates and the ellipse
  reference (its heading uses the first-segment wind). Persistence numbers are unaffected.
- ADR-024 validation scoring, ADR-025–027 benchmark and budget study: comparisons remain
  internally paired, but the inputs are not the fires' historical weather.
- ADR-028 real-case test and calibration gap (116/119 cases had foreign weather).

**Other confirmed defects** (each gets its own fix PR before any rerun):
1. Metrics: IoU includes the shared initial burn (growth-only IoU is ~0.1, not 0.27–0.5);
   the "downwind" ellipse is symmetric about the front centroid.
2. SimFire environment: diagonal lines touch only at corners (4 of 6 links) and SimFire
   spreads 8-connected, so fire leaks through; line strength depends on the internal step
   (fixed ROS attenuation after `R *= update_rate`); the policy observes the exact
   weather of the next 12h; the VALIDATION freeze guard exists only in CLI scripts; the
   two-level bootstrap/t-interval have no tests; some line episodes burn more than no-op.
3. Benchmark reading: base PPO is not distinguishable from a random legal line
   (B=2: −15.1 ha, 95% CI [−41.1, 1.8]); the downwind −28 ha rests on 4/20 fires.
4. Synthetic CA: build progress resets whenever the action changes, even in the same cell;
   line cells inside the no-op footprint count as saved; real-case return is dominated
   by the close-call penalty, so "+0.048 return vs direct_flank" is a safety-standoff
   difference, not better suppression.
5. CI installs no NumPy, so 14–18 numeric tests skip; green CI does not cover them.

**Decision.** Merge PRs #3–#5 as history (merge commits, branches kept) with this notice,
then fix in separate PRs (TASK-021–024), record the open choices in a new ADR before any
rerun (TASK-025), and only then rerun (TASK-026). No result may be cited from ADR-022–028
until TASK-026 replaces it. TEST 2024 stays closed. Plan and acceptance:
[NEXT_SESSION](../NEXT_SESSION.md), [BACKLOG](../BACKLOG.md).

## ADR-030 — rerun decisions: observation, line strength, growth-aware gate, statistics, staged rerun, accepted 2026-11-09

Closes TASK-025 from ADR-029. Accepted by the user (Harun) on 2026-11-09 from the options
proposed after the PR #3–#5 review. Fixed before any rerun; nothing below was chosen after
seeing a new result. Supersedes the corresponding parts of ADR-019 (weather visibility),
ADR-022/023 (gate rule and references) and ADR-026 (seed count and contrasts).

**1. Weather in the observation.** Policies and heuristics observe the forcing of the
*previous* 12h segment; at decision 0 they observe the initial conditions. The upcoming
segment's forcing is never observed. A perfect-forecast variant may be run later only as
a labelled ablation.

**2. Line strength and internal step.** The fireline rate-of-spread attenuation is scaled
with the internal update interval (implemented in our wrapper, not by patching SimFire), and
the internal step is fixed at 5 minutes for every SimFire experiment. A test must show the
same fire and line give the same outcome at 1 and 5 minutes within tolerance.

**3. Growth-aware no-op gate (replaces the ADR-022/023 strict rule).**
- *Metric.* Growth-only IoU: cells outside the initial FEDS mask, as implemented in TASK-022.
  Persistence has growth IoU 0 by construction, so the reference is the downwind 2:1 ellipse
  (initial fire at the rear focus, 180 m per 12h head advance), as implemented in TASK-022.
- *Strata, outcome-blind to SimFire.* A TRAIN case is *growing* when its observed FEDS
  burned area at +48h is at least 1.10 × its initial area (same 180 m rasterization);
  otherwise *non-growing*.
- *Pass rule.* All TRAIN cases complete without errors; zero SimFire map-edge contacts in
  any case; on growing cases, SimFire mean growth IoU over the four timepoints is higher
  than the ellipse's.
- *Non-growing cases* are reported separately (overgrowth in ha and cells) as the known
  limitation of a free-burning no-op against contained fires; they do not decide the gate.
- *Candidates, fixed now.* The ADR-022 WAF list {0, .0025, .01, .025, .05, .10, .20, .605}
  at ROS multiplier 1.0, plus the ADR-023 grid ROS {0.35, 0.5, 0.7} × WAF {0.05, 0.2, 0.4};
  active-cell lifetime 90 min, 5-min step, seed 0.
- *Selection.* If any candidate passes, freeze the passing candidate with the highest
  growing-case growth IoU (tie: lower mean absolute area error). If none passes, record
  FAIL, freeze nothing, and stop before stage 2 for a user decision.
- VALIDATION is scored once with the frozen record and never used for selection; TEST 2024
  stays closed.

**4. Benchmark statistics (replaces the ADR-026 plan).**
- 10 seeds per trained configuration.
- Primary contrasts: base PPO − random legal line and base PPO − best heuristic, at
  B = 1, 2, 4 (six tests). The best heuristic is the one with the largest mean reduction
  versus no-op at B = 2 on TRAIN; it is chosen before any VALIDATION run.
- Inference: paired by scenario on seed-averaged deltas; exact sign-flip test, Holm
  correction across the six primary tests at α = .05; two-level (seed × scenario) bootstrap
  95% CIs. Every contrast also reports the number of scenarios that changed and the result
  without the largest scenario. Contrasts against no-op are reported as sanity checks only.
- Budget fine-tuning contrasts (fine-tuned − frozen base, fine-tuned − matched control)
  follow the same inference and are secondary.

**5. Synthetic CA evaluation.** The training reward keeps its safety penalties. For
acceptance, the primary outcome is saved fraction with the TASK-024 line-credit rule (a
line cell that burns under no-op is not saved). Safety is a non-inferiority condition: the
policy may not have more close calls or more lost units than the comparator heuristic.
Return is reported but does not decide acceptance.

**6. Cohort duplicate.** FPA records `fpa-fod-400305302-sugar-pine` and
`fpa-fod-400389825-columbus` join the same FEDS fire (fireID 58826, same start). Rule: keep
one record per FEDS fire, the one with the lower FPA `fod_id` (sugar-pine), giving 98 TRAIN
cases. The manifest change and its new hash land in stage 1, before the weather
regeneration.

**7. Staged rerun (TASK-026); each stage needs the user's explicit go-ahead.**
1. *Stage 1 — no training.* Prerequisites: TASK-021–024 merged; FEDS timestamp timezone
   checked (TASK-027); duplicate removed. Then regenerate gridMET with the fixed sampler and
   record its hash in the reports, run the gate above on TRAIN, freeze, score VALIDATION once.
2. *Stage 2 — SimFire benchmark and budget study* with the frozen record, 10 seeds, the
   ADR-030 statistics plan. Only if stage 1 passes, or the user labels it exploratory.
3. *Stage 3 — synthetic CA retraining and locking*, then the one-time real-case test and
   calibration with growth metrics. Only after the user decides which simulator is primary
   for the poster, informed by stages 1–2.

Context: ADR-029 above; plan and status in [NEXT_SESSION](../NEXT_SESSION.md).

### ADR-030 addendum — line charge stays in the training reward, accepted 2026-11-09

Raised by the TASK-024 fix (PR #11). A line cell that the paired no-op fire burns is
charged as agent damage (it is consumed, not saved). The user decided that this charge is
part of the **training reward**, not only of evaluation: training and evaluation use one
damage rule, and an evaluation-only charge would keep rewarding line placed on cells that
burn anyway, which is the bias ADR-029 removed. The safety penalty weights (1.0 per lost
unit, 0.1 per close call) are unchanged.

The charge is applied in the decision where the line cell appears inside the no-op
footprint, not when the no-op fire would reach it. Undiscounted totals, and therefore all
evaluation numbers, are identical; under PPO discounting early line inside the footprint
pays a small extra cost. This is accepted as is and recorded here; charging at the no-op
burn time would need a per-cell burn index and is not planned.

### ADR-030 addendum — gate reference and case score made exact, recorded 2026-11-09

The review of PR #9 (TASK-022) found that the ADR-030 §3 text could not be computed as
written. These clarifications were fixed before any gate run on the corrected weather or the
new metrics; no result exists that could have informed them.
- **Ellipse size.** "180 m per 12h" is the semi-major axis growth, as in ADR-022. With the
  ignition point at the rear focus the head reaches about 336 m per 12h downwind and the back
  about 24 m upwind. (Read as a 180 m head advance, the 12h ellipse would be under one cell
  wide.)
- **Ignition point.** The leading edge of the initial active front along the heading (mean of
  the front cells within half a cell of the most downwind one), not the front centroid, which
  can lie inside the scar so that the ellipse adds no cell. This makes the reference stronger,
  not weaker. The report counts cases where the ellipse still adds no cell.
- **Case score.** A case's growth IoU is pooled over its four timepoints (sum of overlaps /
  sum of unions). A plain mean over timepoints is undefined when neither mask has grown yet,
  and dropping undefined timepoints per method would unpair SimFire and the ellipse. Persistence
  scores 0 on every growing case. The gate statistic is the mean case growth IoU over growing
  cases.
- The ADR-022/023 `strict_screen` stays in reports for comparison only and is marked as
  superseded by `growth_gate`.

### ADR-030 addendum — synthetic CA comparator and the real-case test, recorded 2026-11-09

From the review of PR #11 (TASK-024), fixed before any rerun of locked or new policies.
- **Comparator.** "The comparator heuristic" in §5 is the scripted heuristic with the highest
  mean saved fraction on the synthetic acceptance seeds. Safety non-inferiority is measured
  against that same heuristic, so the primary and the safety comparison stay paired. This is
  the bar with the most suppression, not the safest one; the safety block reports every
  heuristic so a reader can see the difference.
- **Real-case test.** The one-time test on the 119 FEDS starts is descriptive, as ADR-028
  intended: the comparator is fixed before the run (`--comparator-heuristic`, the synthetic
  acceptance comparator) and no pass/fail is produced per group.

### ADR-030 addendum — SimFire observation, line strength and benchmark details, recorded 2026-11-09

From the review of PR #12 (TASK-023), fixed before any rerun.
- **Observation (§1).** gridMET is daily, so two 12h segments often share one daily record;
  "the previous segment" still showed the upcoming forcing in 244 of 396 TRAIN decisions.
  At decision k the policy and the heuristics now see the latest gridMET day strictly before
  segment k's day; decision 0 sees a pre-start record (the day before segment 0), which the
  weather sampler now writes. Weather files without it are refused, so stage 1 must
  regenerate the weather.
- **Line strength (§2).** Pinned SimFire subtracts the line attenuation on every update even
  with no fire nearby, so an idle line banks negative burn and becomes a near-absolute
  barrier. Line burn amounts are now floored at zero, and the attenuation is scaled by the
  internal step and by 1 / ros_multiplier, so a line holds iff the effective spread reaching
  it stays below 980 ft/min, independent of the step, the multiplier and the time since
  placement.
- **Benchmark (§4).** The best heuristic is chosen among the scripted heuristics only; the
  random legal line already has its own primary contrast. The six primary tests use exact
  sign-flip p-values (Monte Carlo above 22 changed scenarios) with Holm correction. PPO
  checkpoints, including fine-tuning bases, are loaded only when their training receipt
  matches the run's settings; legacy checkpoints need an explicit, recorded flag in the
  benchmark and are refused for fine-tuning.
- **Split guard.** The SimFire no-op runner and evaluator use the same freeze guard as the
  environment and benchmark (allowlisted record, every simulator field, weather hash) and
  accept only the 5-minute step.

### ADR-030 addendum — FEDS `t` is a local-solar overpass label; duplicate removed, accepted 2026-11-09

From TASK-027, before any stage-1 run. Evidence and links:
[SimFire environment record](../research/SIMFIRE_ENVIRONMENT.md).
- **Finding.** FEDS-CONUS was built with fireatlas v1.4.1, which assigns each VIIRS detection
  to AM or PM by local solar hour (UTC + longitude / 15) and writes the label as hour 0 or 12
  without a zone. `t` is therefore the AM/PM overpass label (SNPP near 01:30 and 13:30 local
  solar time), not a UTC instant. The earlier mapping read it as UTC, which put every 00:00
  state about 8–10 h too early and moved 236 of 472 segment days and 66 pre-start days by one
  day.
- **Decision (user, option 2 of three proposed).** A FEDS state at `t` is the overpass at
  01:30 (AM) or 13:30 (PM) local solar time at the case's weather sample point, converted to
  UTC with longitude / 15 (`feds_overpass_utc`). Segments and the pre-start record are built
  from that instant in one function. Keeping UTC (option 1) was rejected as contradicted by
  the source; a fixed MST reading (option 3) gives the same daily labels on this cohort, but
  only because of its longitude range.
- **Robustness.** Segment midpoints stay at least 3.2 h from the MST day boundary across
  the cohort (minimum 3.235 h, at the westernmost case), so the daily labels do not depend
  on the equation of time or swath-edge spread that longitude / 15 ignores. The observed
  daily record always ends before its decision's segment starts (at least 1.3 h). An
  overpass that falls on another UTC date than the label is refused, because fireatlas
  dates `t` by the UTC acquisition date.
- **Guards.** Weather files must state `temporal_mapping.feds_time_reference` =
  `feds_t_viirs_overpass_local_solar/v1`, or loading is refused. Real-case CA episodes start
  at segment 0's UTC start, and a naive FEDS time is never parsed as UTC.
- **Effect on the §1 observation addendum.** Under this mapping each daily record covers two
  consecutive segments. That addendum's "244 of 396" was 99 decision-0 cases plus 145 of 297
  later decisions where the previous segment shared the upcoming day, under the UTC reading.
  On the 98 TRAIN cases it is now 150 of 294 later decisions; decision 0 shows the pre-start
  day, so it never shows forcing. With the strictly-earlier rule, the observed record changes
  at 144 of 294 later decisions, and in AM-start cases decisions 0 and 1 both observe the
  pre-start day. This is the intended information lag, not a new rule.
- **Duplicate (§6).** It is implemented in the manifest generator as a rule (lowest
  `fod_id` per FEDS fire, keyed like the crosswalk by fireID and start time, because
  FEDS-CONUS numbers fires per yearly file), with excluded records listed in the manifest; columbus is
  dropped and TRAIN has 98 cases. The generator also refuses a FEDS fire joined from both
  TRAIN and VALIDATION. §6 did not ask for this; it is a leakage guard, and no such case
  exists.
- **Regenerated weather.** sha256 `7a51aadd46b894d9cd80835d7953107271b3182c776d7bb464d7abae826afac1`
  from manifest `013be9a1632abcbc29d86f4bc16af89d3c074503f5899d1e39903d76ec2c28d5`. All
  118 cases have a pre-start record and one cell each (118 distinct, at most 2.80 km). The
  receipt is the [weather coverage report](../../reports/real-fire-data/feds-gridmet-weather-coverage-v1.json),
  which compares the file with the defective file `7b0aa405…`: 3 distinct cells for 119
  records, no pre-start, and 115 of 118 cases on another cell.
- **Real-case test count.** "The 119 FEDS starts" in the synthetic CA addendum above now
  means the manifest's 118 starts; the stage-3 run has not happened.

### ADR-030 addendum — autonomous stages 1 and 2, accepted 2026-11-09

The user (Harun) decided this on 2026-11-09, after PR #15 (TASK-027) was merged and before
any stage-1 run. It replaces §7's "each stage needs the user's explicit go-ahead" for
stages 1 and 2 only.
- **Stage 1** may run without a further go-ahead: the gate on TRAIN, the freeze, and one
  VALIDATION score.
- **Stage 2** may follow without a further go-ahead **only if stage 1 passes**: the SimFire
  benchmark and budget study, run locally, with 10 seeds and the §4 plan.
- **If stage 1 fails**, the agent records FAIL, freezes nothing, does not score VALIDATION,
  and stops for a decision.
- **Spread ordering.** Stage 2 keeps `spread_aggregation="last_write"` (pinned SimFire). The
  number of episodes where a line burns more than no-op is reported as a known limitation;
  `"max"` would need its own decision and gate.
- **Merges stay with the user.** Agents may push branches and open PRs, with an independent,
  narrow-context review.
- **Unchanged:** stage 3 still needs the user's decision, and TEST 2024 stays closed. No gate
  rule, candidate, metric or statistic may change after a result is seen.

The agent prompt is [HANDOFF_STAGE_1_2](../HANDOFF_STAGE_1_2.md).

## ADR-031 — stage 1 result: growth gate PASS on TRAIN, WAF 0.10 / ROS 1.0 frozen, VALIDATION scored once, recorded 2026-11-09

Stage 1 of TASK-026, run under the autonomy addendum above. This is the first gate result on
the corrected inputs (weather `7a51aadd…`, manifest `013be9a1…`, metrics
`feds-spread-metrics/3`). It replaces the gate results of ADR-022–024. Nothing in ADR-030 §3
was changed after a result was seen.

**Fixed before the runs.** The selection script and its tests were committed before any
candidate ran (commit e988493). Two details that §3 leaves open were fixed there: the
tie-break "mean absolute area error" is taken over all TRAIN case-timepoints, as in ADR-022,
and a tie on both criteria stops the selection for a user decision. Neither was needed.

**TRAIN gate (17 candidates × 98 cases, seed 0, 5-min step, lifetime 90 min).**
- Every candidate completed 98/98 cases without errors. The strata are the same for all:
  82 growing and 16 non-growing cases. The ellipse scores a mean case growth IoU of 0.0258
  and adds cells in every case.
- 8 of 17 pass. 7 fail on map-edge contact (WAF .20 and .605 at ROS 1.0; WAF .40 at every
  ROS; WAF .20 at ROS .5 and .7). 2 fail on growth IoU below the ellipse (WAF .05 at ROS .35
  and .5).
- **Selected: WAF 0.10 / ROS 1.0**, growth IoU 0.0958 on growing cases against 0.0258
  (+0.0700), no edge contact. Next passing candidate: WAF .05 / ROS 1.0 at 0.0706. WAF .20 /
  ROS 1.0 scores 0.0992 but touches the map edge in 14 cases, so the rule excludes it.
- SimFire beats the ellipse in 59 of the 82 growing cases; in 10 of them it adds no cell
  by +48h. Median case growth IoU is 0.072 against 0.007.

| WAF | ROS | Growth IoU (growing) | Edge-contact cases | Mean abs. area error (ha) | Non-growing overgrowth (ha) | Gate |
|---:|---:|---:|---:|---:|---:|---|
| 0 | 1.0 | 0.0545 | 0 | 2,345 | 1,513 | pass |
| .0025 | 1.0 | 0.0548 | 0 | 2,348 | 1,533 | pass |
| .01 | 1.0 | 0.0570 | 0 | 2,343 | 1,567 | pass |
| .025 | 1.0 | 0.0602 | 0 | 2,448 | 2,578 | pass |
| .05 | 1.0 | 0.0706 | 0 | 2,726 | 4,005 | pass |
| **.10** | **1.0** | **0.0958** | **0** | **4,120** | **8,976** | **pass, selected** |
| .20 | 1.0 | 0.0992 | 14 | 8,389 | 18,487 | edge |
| .605 | 1.0 | 0.0483 | 76 | 34,578 | 40,100 | edge |
| .05 | .35 | 0.0071 | 0 | 2,367 | −31 | below ellipse |
| .20 | .35 | 0.0317 | 0 | 2,387 | 1,564 | pass |
| .40 | .35 | 0.0684 | 8 | 3,619 | 5,273 | edge |
| .05 | .5 | 0.0120 | 0 | 2,356 | 108 | below ellipse |
| .20 | .5 | 0.0649 | 1 | 2,781 | 4,123 | edge |
| .40 | .5 | 0.0818 | 21 | 6,440 | 10,978 | edge |
| .05 | .7 | 0.0306 | 0 | 2,417 | 900 | pass |
| .20 | .7 | 0.0932 | 6 | 4,353 | 9,625 | edge |
| .40 | .7 | 0.0796 | 34 | 11,858 | 17,921 | edge |

Non-growing overgrowth is the mean SimFire growth beyond observed growth at +48h per
non-growing case.

**Freeze.** `configs/frozen/feds-simfire-growth-gate-freeze-v1.json` (sha256 `7639e3a9…`)
states all six simulator fields, the weather and manifest hashes and the gate report hash.
It was added to the VALIDATION allowlist in the same commit (de0e42f), before any VALIDATION
scoring.

**VALIDATION, scored once (20 cases, not used for selection).** 20/20 without errors, no edge
contact, 18 growing and 2 non-growing. Growth IoU 0.0983 against the ellipse's 0.0278
(+0.0705); SimFire is ahead in 13 of 18 growing cases and adds no cell in 2. Mean overgrowth
on the two non-growing cases is 823 ha.

**What the PASS does and does not show.**
- It shows that, under the rule fixed in ADR-030, SimFire places new growth better than a
  fixed geometric ellipse on fires that grew, on TRAIN and again on VALIDATION.
- Both growth IoUs are below 0.10. The selected setting overgrows contained fires: on the 16
  non-growing TRAIN cases the no-op run adds about 2,770 cells (8,976 ha) more than FEDS
  observed by +48h. Mean absolute area error is 4,120 ha against 2,371 ha for persistence;
  full-mask IoU is 0.355 against 0.532 on TRAIN and 0.406 against 0.543 on VALIDATION. The
  superseded ADR-022 strict screen would still fail.
- The frozen record is therefore a free-burning scenario that passes the pre-set gate, not a
  calibrated or physically validated spread model. Stage 2 results inherit this limit.

**Consequence.** Stage 2 (SimFire benchmark and budget study, ADR-030 §4) proceeds with this
record. Merges and stage 3 stay with the user; TEST 2024 stays closed.

Evidence: [TRAIN gate summary](../../reports/real-fire-data/feds-simfire-train-growth-gate-v1.json),
[VALIDATION score](../../reports/real-fire-data/feds-simfire-validation-growth-gate-v1.json),
[freeze record](../../configs/frozen/feds-simfire-growth-gate-freeze-v1.json), EXP-019 in the
[experiment log](../research/EXPERIMENT_LOG.md).
