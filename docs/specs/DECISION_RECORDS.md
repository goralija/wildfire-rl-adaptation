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
