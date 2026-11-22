---
type: Playbook
title: Handoff za nastavak projekta
---
# Handoff za nastavak projekta

## TASK-043 završen — nijedan backend ne prolazi learning kriterij (ADR-052, 2026-11-22)

[Upareni PPO izvještaj](docs/research/PAIRED_PPO_LEARNING.md), `codex/paired-ppo-learning`,
plan d586c1bc prije numeričkog koda13a234ba. Svih6treninga završilo bez grešaka za
52,13min:45TRAIN fit/16ranije istraženih development evaluation,3model seeda po
backend-u,2.048koraka/model. Isti input/encoder/MLP/hiperparametri,B1,48h i charged
reward. CA spread0 je fiksiran; model seedovi nisu novi požari ili fizičke replike.

Na istih14joint-positive požara završni PPO mean saved%: **SF5,13 / CA6,03**.
Fiksni front: **SF11,29 / CA3,35**; fixed random_legal(seed0): **SF1,17 / CA9,49**.
Final−initial: SF−0,59pp[−2,69;+0,98], CA+1,73[−1,34;+5,45]. Final−front: SF−6,16pp
[−17,83;+2,32], CA+2,68[−1,72;+7,07]. CA−SF relative gap+8,84pp[−0,38;+20,02].
**Oba unaprijed zadana opisna learning kriterija su false.** Nema izbora modela/512
checkpointa ili tvrdnje o pouzdanoj RL prednosti. Sva18checkpointa i svi seedovi sačuvani.

CA greedy bira po jedan isti sektor na16/16slučajeva za sva3modela; SF2/3modela također.
Soft distribucije ostaju gotovo ravnomjerne (najveća vjerovatnoća SF11,66–11,85%,
CA12,00–12,28%). To je slab dokaz prilagođavanja, ne dokaz tvrde probabilističke
kolapsirane politike. Fixed random seed0 na ovom uzorku daje sektor7svuda, nije
Monte Carlo prosjek svih nasumičnih politika. Hektari/pooled i SFzero-noop2 su prijavljeni.

Nezavisno12.288koraka/3.072epizode,18checkpointova,288policy/128heuristic skorova,
96native putanja/480maski,610reference maski i132preflight putanje PASS. Restore
iz raspakovanog sourcea/61ulaza/18modela ponavlja svih96native putanja i288odluka,
logits/features/maske/akcije identično. Paket30.563.393B/1.035fajlova plus manifest,
svi hashovi provjereni, lokalno.413pinned/0skip,398modern/4skip,315core/48skip,
15knowledge,CLI/strict92PASS. Nema aktivnog treninga.

**Sljedeći prijedlog: TASK-044**, mali TRAIN audit signala nagrade/advantagea,
stvarne promjene politike i adekvatne uniformne/fiksne reference prije dodatnog
treninga. Nije pokrenut. Native mobile-unit parity ostaje otvoreni TASK-040 B,
TASK-039 odgođen; stvarni VALIDATION/TEST, fizička validacija i merge nisu rađeni.

### Objava TASK-043

Grana [codex/paired-ppo-learning](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/paired-ppo-learning)
je commitana i pushana. [CI rezultatskog commita cfc2a2a1](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/45076798202)
prolazi core3.11/3.13, numeric s tačnom skip listom i knowledge. Naknadna dopuna objave
ne mijenja numerički source/plan/rezultate. Lokalni paket nije uploadovan; nema novog PR-a/mergea.

## TASK-040 B.1 završen — zajednički PPO/reward ugovor (ADR-050, 2026-11-22)

[Zajednički interfejs](docs/research/COMMON_PPO_INTERFACE.md) na `codex/common-ppo-interface`,
iz45d41fcf: isti v2/terrain536, MLP64×64,9akcija,nonfuel maska,B1,48h/4×12h i opt-in
incremental charged reward. Privatni vlastiti no-op služi samo nagradi; nema future
FEDS-a u ulazima/maskama. Historijski raw reward/fizika ostaju nepromijenjeni.

Plan f1d46d22 prije koda011b85a1; metadata regresija/popravljeno bc0b58ba. Svih30no-op
maski identično arhivi;24scripted finalne požarne/linijske maske identične starim
tabelama. Četiri64-step treninga (2backend-a×2seeda), iste početne težine po seedu
i isti raspored16epizoda6/5/5. Ukupno256koraka,64epizode;12checkpoint replayeva
identično. Svi modeli/dijagnostika sačuvani; nema biranja najboljeg ili RL rankinga.

397pinned/0skip,382modern/4skip,308core/46skip,15knowledge,CLI/strict91 PASS. Nezavisni
union/return obračun36putanja/180maski,30reference maski i256koraka PASS. Lokalni paket
3.326.232B,217fajlova plus manifest, svi hashovi provjereni; restore iz kopiranog
sourcea/ulaza/4numeric checkpointa ponavlja12putanja/60maski i logits/akcije. Biblioteke
ponovo korištene, bez fresh installa/training resumea. Smoke119,91s,nice19/jedna nit.

**Sljedeći prijedlog:** novi unaprijed registrovan mali TRAIN learning pilot sa istim
slučajevima/seedovima/arhitekturom/koracima u oba backend-a. Prijaviti charged ha,
procenat prema vlastitom no-op i odnos prema istim heuristikama, uz zero-noop pravilo.
Ovo još nije mjera učenja/generalizacije ili fizička validacija. Native mobile-unit
parity ostaje zaseban otvoreni dio B; TASK-039 odgođen, TASK-037 opcionalan. Nema
automatskog dužeg treninga, stvarnog VALIDATION/TEST, novog PR-a ili mergea.

### Objava B.1

Grana [codex/common-ppo-interface](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/common-ppo-interface)
je pushana. [CI rezultatskog commita3ec5d5fc](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44965103408)
prolazi sva4posla: core3.11/3.13,numeric uz exact skip listu i knowledge. Naknadna
dopuna objave ne mijenja numerički source, plan ili rezultate. Nema novog PR-a/mergea.

## TASK-042 završen — svih 61 kompatibilnih TRAIN početaka (ADR-048, 2026-11-21)

[Prošireni audit](docs/research/EXPANDED_OBSERVED_GROWTH.md) je završen na `codex/ca-expanded-growth-audit`, iz2de00136.
Plan5d72b974 prethodi kodu9ab1f70a i novim ishodima. Parametri/metric source su isti.
Transparentno je ponovo korišteno64putanje starih16slučajeva,180novih putanja za45novih,
plus3tehnička CA ponavljanja. Svih45novih SF endpoint maski identično arhivi; prediction
freeze prije novih FEDS geometrija. Nije rađeno podešavanje, novi PPO ili stvarni holdout.

**Primarno:** areaMAE na61: SF6.642,37ha, CA0 2.132,29ha (67,90%manje). GrowthIoU na
istih57observed-positive: SF0,08664, CA0 0,12568. CA0−SF deltaIoU+0,03904, opisni95%
[+0,00861;+0,06963]; deltaMAE−4.510,08ha[−6.856,90;−2.414,21]. Sekundarni CA3mean
IoU0,13020/MAE2.110,41ha. To je povoljniji opisni TRAIN nalaz, ne fizička validacija.
Na novih45primary IoU0,11215vsSF0,08030; efekat slabiji, CA3mean interval uključuje0.

**Granice:** grupe su4bez opaženog rasta,1near-stalled,56growing. Oba modela prerastaju
sva4nulta slučaja, CA0u prosjeku3.147,66ha/SF9.455,94ha; na206CA0je i lošiji odSF.
Goldstone ostaje jedini near-stalled i CA0je lošiji. FEDS uzrok nerasta nije poznat;
buduće opažanje nije signal za gašenje. Goose Creek/Martin izlaze iz domene;59fully-covered
zapis ostaje povoljan. Svih305opažanja validno/monotono, početni raster/vrijeme konzistentni.
CA bridge nije native unit/PPO model; apsolutniIoU ostaje nizak,37TRAIN početaka isključeno
po ranijem input QC-u, nema nezavisnog fizičkog testa. Nijedna glavna predikcija ne dotiče rub.

388pinovanih/0skip,373modernih/4skip,306core/44skip iCLI PASS. Nezavisno2.928metric redova,
305rastera,45SF maski,32reuse NPZ-a, svih16starih metric zapisa i primarni intervali PASS.
Paket18.848.375B/1.064fajla plus manifest, svi hashovi provjereni; restore prvih5SF/3×5CA
maski, starog reusea i305opažanja identičan uz postojeće biblioteke. Nema aktivnog računanja.

**Sljedeći prijedlog: TASK-040 faza B.1**, zajednički PPO adapter/encoder i reward ugovor
nad postojećim common-line bridgeom za oba backend-a, pa kratak tehnički smoke. Isti
budžeti/akcije/informacije/horizont; nije duži trening ili rangiranje starih native PPO-a.
Mobilni resursi/native parity ostaju zaseban otvoreni dio faze B. TASK-039 odgođen,
TASK-037 opcionalni SimFire pravac. TEST/VALIDATION i merge nisu rađeni.

### Objava TASK-042

Grana [codex/ca-expanded-growth-audit](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-expanded-growth-audit)
je commitana i pushana. [CI kodnog/rezultatskog commita `aa3335a4`](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44907387597)
prolazi core3.11/3.13, numeric s tačnom skip listom i knowledge. Verification čuva
commit; kasnija dopuna objave ne mijenja numerički source, plan ili rezultate.
Veliki paket ostaje lokalni. Nema novog PR-a ili mergea; main i prethodni rad su sačuvani.

## TASK-041 završen — opaženi rast (ADR-046, 2026-11-21)

Na `codex/ca-feds-growth-audit`, iz640a910e, završen je [TRAIN audit](docs/research/PAIRED_OBSERVED_GROWTH.md).
Plan46e5371f/ADR-045 i kod7d04fca0 prethode novom scoringu. Isti16početaka i zamrznuti
SF/CA bridge, bez promjene parametara ili politika. SF16/16 iCA0 16/16 finalne maske
identične arhivama; CA1/2 brojevi32/32 isti. Predikcije su zaključane prije future FEDS-a.

**Nalaz:** na48h mean new-area IoU SF0,1029/CA0 0,1604; mean apsolutna greška novih
ha SF9.736,40/CA0 1.317,67,86,47%manja. Sekundarni prosjek3CA spread replike:
IoU0,1812/MAE1.231,94ha. CA0−SF deltaIoU+0,0575, opisni95%[−0,0219;+0,1344]
uključuje0; deltaMAE−8.418,74ha[−15.211,86;−2.619,71] ne uključuje0 u ovom obračunu.
CA0 je bolji po površinskoj grešci13/16, poIoU10/16; nisu svi slučajevi poboljšani.
Opaženi mean novi rast2.726,46ha; CA je bliži razmjeru, ali nije fizički validiran.

**QC/granice:** svih80exact-time stanja prisutno/validno/monotono, t0 scar i usvojeno
local-solar vrijeme se poklapaju16/16. Martin ima36,85%vektorske površine izvan domene
na48h. Fully-covered15 analiza daje SF/CA0 IoU0,1031/0,1665 iMAE7.844,47/1.149,77ha;
primarni spatial interval i dalje prelazi0. Goldstone ima samo3,24ha opaženog rasta,
a CA0/1/2 daje311/26/133ha: skoro zaustavljeni požari ostaju problem. Nema observed-zero
48hslučaja u ovih16. Native unit CA/PPO nije rangiran; nepoznate intervencije/opažajna
greška, kompatibilni TRAIN subset i15/16pokrivenost ograničavaju zaključak.

381pinovani test/0skip, moderni366/4skip, core299/44skip iCLI PASS. Nezavisno768metric
redova,80rasterizacija i10maski starog loader-a potvrđeno. Paket10.486.862B,436fajlova
plus manifest ima sve provjerene hashove; raspakovani source/ulazi ponavljaju prvih5SF
maski i3×5CA maski, te80FEDS rastera. Postojeće biblioteke, ne fresh install ili novi
naučni uzorak. Nema aktivnog računanja, novog treninga, stvarnog holdouta ili mergea.

**Preporuka:** CA ima bolju osnovu za nastavak istraživanja zbog manjeg neslaganja
razmjera u ovom testu. Sljedeći predloženi TASK-042 proširuje isti zamrznuti no-op audit
na svih61ulazno kompatibilnih TRAIN početaka, uz full future-domain QC i posebno
near-stalled/no-growth slučajeve, prije većeg treninga. Novi plan prije scoringa;
TASK-040 native faza B ostaje otvorena, TASK-039 odgođen. Bez automatske fizičke validacije.

### Objava TASK-041

Grana [codex/ca-feds-growth-audit](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-feds-growth-audit)
je commitana i pushana. [CI kodnog/rezultatskog commita21ff12f2](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44850220640)
prolazi sva četiri posla: core3.11/3.13, numeric s tačnom skip listom i knowledge.
Verification čuva tačan testirani commit; kasnija dopuna objave ne mijenja numerički
kod, plan ili ishode. Veliki paket ostaje lokalni, bez novog PR-a ili mergea.

## TASK-040 faza A završena — upareni simulatori (ADR-044, 2026-11-21)

Na `codex/ca-simfire-paired`, iz `722d5f2d`, završen je [upareni pilot](docs/research/CA_SIMFIRE_PAIRED.md).
Plan `56c460db` i ulazna dopuna `ae0d13af` prethode CA ishodima: 98 TRAIN ulaza,
61 kompatibilan početni front, 16 odabrano hash redoslijedom. Ista puna mapa 256×256,
48h, početne maske, ispravljeni gridMET, lagged v2 opažanje, jedna identična linija i
unweighted charged šteta. Fiksne heuristike imaju iste sekvence i cijele linijske
maske 16/16. Ovo je zajednički kontrolni interfejs, a ne native CA unit/PPO poređenje.

**Nalazi:** na 14 zajedničkih slučajeva s pozitivnim no-op rastom, SimFire / CA prosjek
tri unaprijed zadata spread seeda: random 1,17 / 8,01%, downwind 4,32 / 2,90%, front
11,29 / 5,30%, isti novi nested RBF postupak 2,44 / 5,85%. Primarni CA seed0 agent
je 1,42%; dodatni seed1/2 su 10,82 / 5,32%, bez refita ili izbora najboljeg. Sekundarni
CA−SF agent interval [−0,05; +7,05] p.p. uključuje nulu. Pooled front udio na svih16
obrće smjer: SF 2,89%, CA 3,67%; ponderisanje i no-op razmjer su bitni.

No-op novi rast na svih16: SF 11.363,69ha, CA 2.098,78ha (prosjek3), oko5,4puta manje.
Mean IoU novih maski SF/CA0 je0,0691; nijedan no-op ne dotiče rub. To je neslaganje
simulatora, nije dokaz koji je bliži stvarnom požaru. Rezultati su mješoviti i ne
opravdavaju automatski prelazak na CA ili tvrdnju da je SimFire fizički bolji.

369 pinovanih testova/0skip; moderni354/3skip, core287/41skip, CLI PASS. Deset native
SF replayeva i33 CA ishoda identični; nezavisno rekalkulisano1.056 mask-scoreova.
Lokalni paket14.888.989B,562 fajla plus manifest, svi hashovi provjereni; iz raspakovanog
sourcea/podataka prvih33 CA ishoda ponovljeno identično uz postojeće biblioteke.
Nema novog PPO treninga, stvarnog VALIDATION/TEST ili mergea. CA nije fizički validiran.

**Sljedeći prijedlog TASK-041:** TRAIN no-op rast oba modela prema istim opaženim FEDS
promjenama, prije daljnjeg treninga. TASK-040 faza B (native resursi/akcije/PPO) ostaje
otvorena; TASK-039 imitation dijagnoza je odgođena. Nema aktivnog računanja.


### Objava TASK-040 faze A

Grana [codex/ca-simfire-paired](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-simfire-paired)
je commitana i pushana. [CI kodnog/rezultatskog commita042a5c73](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44846740515)
prolazi sva četiri posla (core3.11/3.13, numeric, knowledge). Verification čuva tačan
commit; kasnija dopuna objave ne mijenja numerički kod ili ishode. Nema novog PR-a,
mergea ili uploada velikog lokalnog paketa. Main i prethodna grana su sačuvani.


## TASK-038 završen — CA v2 BC/PPO (ADR-042, 2026-11-21)

Na `codex/ca-learning-pilot` iz3b7b56a2 završen je [kratki CA learning pilot](docs/research/CA_LEARNING_PILOT.md).
Plan6f2e4b61 prethodi treningu.32TRAIN požara ×3rostera daju96demonstracija/1.152stanja;
tri seeda17/29/43 uče60BC epoha pa svaki tačno4.096PPO koraka. Svi posjećuju96TRAIN kombinacija.

Svih6 modela ×16development požara ×3rostera =288putanja prolazi tehničke provjere.
BC prosjek3,08%, BC+PPO2,98%, referenca direct_flank7,46% spašene težinske štete.
PPO minus BC −0,105p.p., opisni interval[−2,08;+1,21]. Nijedan kandidat ne prolazi
registrovani kriterij nastavka. Modeli imaju2–5 bliskih susreta po seedu prema20 kod
heuristike, svi0gubitaka u uzorku; nema dokaza RL prednosti ili stvarne sigurnosti.

362pinovana testa, moderni347/3skip, core286/40skip, dodatni aktivni checkpoint testovi,
knowledge15/15/strict87 i CLI PASS. Numeric NPZ težine su lokalne s provjerenim hashovima;
stari checkpointovi nisu korišteni. Završni poslovi traju oko7,5min na nice19, max4procesa.
Naredni prijedlog TASK-039: TRAIN dijagnoza učiteljskih/modelskih putanja i kodiranja,
pa kratak unaprijed zadat nastavak ako je opravdan. Dugi trening, proceduralni test i
stvarni VALIDATION/TEST ostaju zatvoreni; nema aktivnog runa. CA nije fizički validiran.


### Objava TASK-038

Grana [codex/ca-learning-pilot](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-learning-pilot)
je commitana i pushana. [CI na kodnom/rezultatskom commitu1d4209be](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44840927699)
prolazi sva četiri posla. Verification čuva tačan testirani commit; kasnija dopuna
objave ne mijenja numerički kod. Paket modela ostaje lokalni; nema novog PR-a ili mergea.


## CA ugovor i pilot završeni — TASK-035 / ADR-040 (2026-11-21)

Korisnikov CA nastavak je izveden na `codex/ca-controlled-pilot`, iz `664d890d` završene
SimFire repair grane. [Izvještaj](docs/research/CA_CONTROLLED_PILOT.md) i zamrznuti plan čuvaju
razlog prelaska: naučeni SimFire modeli nisu nadmašili jaču heuristiku; nije proglašena
iscrpljenost SimFire-a. Plan commit `c8d8563c` prethodi kodu i rezultatima.

CA v2 daje isto native opažanje i current forcing svim politikama; heuristike rade samo
iz opažanja/maski. Svih16 development požara ×3 rostera ×5 politika =240 epizoda prolazi.
`direct_flank` čuva7,46% težinske štete prema0,24% randoma; opisna razlika7,23p.p.,
95% interval[0,44;16,49]. Ima20 bliskih susreta i0 gubitaka kroz48 epizoda. Nema RL modela
ili potvrđene sigurnosne prednosti. Prvi case replay15/15 je identičan.

352 pinovana testa bez skipa; moderni337/3 skip i core284/38 skip, CLI i knowledge PASS.
TASK-035 je završen. Naredni TASK-038 je v2 encoder/provenance i kratak preregistrovan
BC/PPO, uz jaku heuristiku i odvojene sigurnosne kriterije. TASK-037 SimFire je odgođen.
Train/test proceduralne liste su rezervisane, nisu generisane/skorirane; stvarni
VALIDATION i TEST 2024 ostaju zatvoreni. Stari checkpointovi i dugi trening nisu korišteni.
CA je vlastiti pojednostavljeni simulator, ne Cell2Fire ili fizička validacija.


### Objava CA grane

Grana [codex/ca-controlled-pilot](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-controlled-pilot)
je commitana i pushana. [CI na kodnom/rezultatskom commitu3ad3f72c](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44836958711)
prolazi sva četiri posla. Publication zapis je u CA verification JSON-u; kasnija dopuna
publikacijskih podataka ne mijenja numerički kod. Nema novog PR-a, mergea ili aktivnog runa.


## Objava i pregled (2026-11-20)

Grana [codex/simfire-observation-repair](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/simfire-observation-repair)
je pushana. [CI kodnog/rezultatskog commita1cabe778](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44817109635)
prolazi core3.11/core3.13, numeric i knowledge. Nema mergea ili novog PR-a po posljednjoj
korisnikovoj poruci; [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
prethodnog rada ostaje otvoren. [Publication receipt](reports/real-fire-data/feds-observation-repair-publication-v2.json)
čuva tačan testirani commit. Kasnija dopuna publikacijskih podataka ne mijenja numerički
kod. Veliki lokalni paket nije uploadovan.

## Najnovije — v2 popravak izveden (ADR-038)

[SimFire observation repair](docs/research/SIMFIRE_OBSERVATION_REPAIR.md) je sada prvi
ulaz. V2 vraća razliku fuel/nonfuel i native lokalnu geometriju; svi 98 legacy/no-op
kontrolni replayevi prolaze, sedam stvarnih v2 sekvenci takođe. Stari benchmark i
checkpointovi nisu tiho promijenjeni. Fine+gate ima bolji, ali nesiguran TRAIN prosjek
(123,72 charged ha; +22,68 prema starom pravilu). Nijedan naučeni kandidat ne prelazi prag.

Rad je na `codex/simfire-observation-repair`, iz `d3bb5b86`; prethodni PR #20 ostaje
za pregled. Push je odobren, novi PR nije potreban, nema mergea. Lokalni paket s
manifestom sadrži stare ulaze/ishode plus v2 opservacije i tehničke replay maske.
Nema aktivnog računanja. Sljedeće: TASK-035 CA ugovor/pilot ili eksplicitni SimFire
TASK-037 za fiziku/gate i novi trening. Detaljan redoslijed je u NEXT_SESSION.

## Korisnikov nastavak — popravak opažanja prije CA (2026-11-20)

Završeni rad je pushan i otvoren kao [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
prema `main`, za pregled kolega. PR ostaje otvoren. Korisnik je odobrio još jedan
SimFire pokušaj: TASK-036 sada ima prioritet pred CA pilotom TASK-035.
Nastavak ide iz ove grane u `codex/simfire-observation-repair`, u izdvojenom worktreeu;
novi PR nije potreban po posljednjoj korisnikovoj poruci. Precizni plan ide prije
novih mjerenja. VALIDATION/TEST i novi CA trening ostaju zatvoreni.

## Najnovije — TASK-034 završen (ADR-036)

[Završni SimFire audit](docs/research/SIMFIRE_OBSERVATION_AUDIT.md) je ulaz za nastavak:
98 input/observation provjera PASS, četiri nested metode bez prolaza praga, potvrđeni
pooling/fuel aliasing, startup race popravljen i native numerička osjetljivost izmjerena.
327/327 pinovanih testova prolazi. Native probe su dva namjerno odabrana slučaja;
nije dokazana fizička validacija niti iscrpljenost svih SimFire mogućnosti.

Nova grana `codex/simfire-observation-audit` iz `58feac72` je lokalna, bez novog push-a
ili mergea. Prethodna `codex/simfire-policy-iterations` je na originu. Nema aktivnog runa.
Preporučen je TASK-035: [CA ugovor i tehnički pilot](configs/drafts/ca-controlled-pilot-v1.json),
bez automatskog treninga; opcionalni TASK-036 opisuje SimFire v2. TEST i novo VALIDATION
korištenje ostaju zatvoreni. Brojevi ADR-028 ne vraćaju se u upotrebu. Detalji su u
NEXT_SESSION/BACKLOG; veliki artefakti su u lokalnom paketu s manifestom.

## Prethodni ciklus — SimFire B=1 završen (ADR-034)

Korisnikov SimFire nastavak TASK-028–030 je završen na lokalnoj grani
`codex/simfire-policy-iterations`. [Izvještaj](docs/research/SIMFIRE_B1_EXPLORATION.md)
čuva oba obračuna, provjerenu tabelu 98×33 i osam LOO metoda. Nijedna ne prelazi
unaprijed zadani prag. Charged ridge-10 daje +6,98 ha prema pravilu, ali −13,63 ha
bez najveće OOF razlike; nema potvrđene prednosti. Oracle jaz ostaje velik.
[Manifest lokalnog paketa](reports/real-fire-data/feds-b1-artifact-manifest-v1.json)
veže tačan weather, pune ishode, TRAIN ulaze i source snapshot. Nema aktivnog runa.
TASK-034 je zatim završen; njegov nalaz i predloženi TASK-035 su u najnovijoj sekciji iznad.
VALIDATION/TEST i CA faza 3 ostaju zatvoreni. Nema novog PPO treninga. Grana je naknadno pushana na origin po korisnikovom nalogu; PR i merge nisu urađeni.

## Gdje je projekat (jedan pasus)

Pitanje: može li RL agent s budžetom od B vatrogasnih linija smanjiti izgorjelu površinu
više od jednostavnih pravila, i pomaže li fine-tuning za zadani B. Glavni simulator je SimFire
pokrenut od stvarnih početnih stanja 118 američkih požara (98 TRAIN 2018/19, 20 VALIDATION
2023; TEST 2024 zatvoren). Raniji rezultati su poništeni (ADR-029, greška u vremenskim
podacima), greške su ispravljene, a ponovno pokretanje je dalo: **faza 1** gate PASS, zamrznut
WAF 0.10 / ROS 1.0 (ADR-031); **faza 2** nijedan od šest primarnih testova ne odbacuje, PPO
se ne razlikuje od nasumične linije ni od najbolje TRAIN heuristike, fine-tuning po budžetu
ne daje mjerljiv dobitak (ADR-032). **Pregled 2026-11-11** (literatura i dijagnoza, bez novih
treninga) kaže da je to očekivano i predlaže jeftinu TRAIN-only provjeru gornje granice
prije bilo kakvog novog treninga: [sažetak i plan](docs/research/review-2026-11-11/SUMMARY.md).

## Grane i pull requestovi

Faze 1 i 2 i pregled PR #19 su u `main`-u (`f96f744f`). Prethodna grana
`codex/simfire-policy-iterations` je na originu od 2026-11-19. Novi TASK-034 je lokalno
na `codex/simfire-observation-audit`, u istoimenom `.worktrees/` folderu. Nijedna nova
grana nije spojena u main; glavni klon i raniji artefakti su sačuvani.

Provjera prije rada: `git fetch origin` pa `gh pr list --state all --limit 5`. Lokalni `main`
na Harunovom računaru može zaostajati za `origin/main`; nove grane praviti iz `origin/main`.

## Šta pročitati, redom

1. [AGENTS](AGENTS.md) (pravila), [index](index.md), [projektni kontekst](knowledge/project-context.md).
2. [STATUS](docs/STATUS.md) i [NEXT_SESSION](docs/NEXT_SESSION.md): najnovije sekcije su na vrhu.
3. [Pregled 2026-11-11](docs/research/review-2026-11-11/SUMMARY.md): odgovori na pet pitanja,
   odluke koje čekaju, redoslijed TASK-028–033.
4. ADR-029 do ADR-034 s dopunama u [odlukama](docs/specs/DECISION_RECORDS.md).
5. [Šta politika smije raditi](docs/research/review-2026-11-11/INTERVENTIONS.md): tačan opis
   okruženja, akcija i heuristika (dokumentacija na nekoliko mjesta zaostaje za kodom).
6. Za pokretanje: [HANDOFF_STAGE_1_2](docs/HANDOFF_STAGE_1_2.md) §4–§6 samo kao referenca
   komandi (njegova dozvola za samostalno pokretanje je iskorištena) i [mapa koda](knowledge/code-map.md).

## Šta čeka odluku (Harun)

- Arhiviranje lokalnih rezultata faza 1 i 2 (vidi „Šta postoji samo lokalno“ ispod), npr. kao
  privatni GitHub release kakav je `synthetic-policy-v1`.
- Kako se računa šteta kad linija zauzme ćelije koje bi izgorjele (sada se računaju kao spašene).
- TASK-028–030 i TASK-034 su završeni; TASK-035 CA pilot je novi draft, TASK-036 SimFire v2 je opcionalan. Novi budžeti, nova VALIDATION upotreba i novi trening traže unaprijed zapisan nastavak.
- Korisnik je odabrao SimFire nastavak. CA observation i faza 3 ostaju odgođeni. Detalji: [NEXT_SESSION](docs/NEXT_SESSION.md), [BACKLOG](docs/BACKLOG.md).

## Pravila koja važe za svakog ko nastavlja

- Agent radi push i otvara PR samo uz Harunov nalog (za faze 1 i 2 dat je dopunom ADR-030, za
  pregled 2026-11-11 u razgovoru), uz nezavisnu reviziju. **Svaki merge radi Harun.**
- TEST 2024 se ne preuzima ni ne otvara. VALIDATION se koristi samo unaprijed registrovano.
- Ne mijenjati gate, kandidate, metrike, statistiku ni pravilo izbora nakon rezultata;
  nova pravila idu u novi ADR prije pokretanja.
- Bez plaćenog ili cloud computea. Dugi poslovi na Harunovom računaru: najviše 4 procesa,
  `nice -n 19`, i unaprijed reći koliko traje (trening ~95 min po seedu; pravilo je u AGENTS.md).
- Ne commitovati `.local/`, težine modela, sirove podatke, venv. Nikad `git clean -fdx`.
- `spread_aggregation` ostaje `"last_write"`; bez starih checkpointa i bez
  `--allow-legacy-checkpoints`.
- Simulatorski rezultat nije dokaz o stvarnom gašenju; gate PASS nije fizička validacija.

## Okruženje i podaci

**Novi računar.** Kod, manifest i ulazi se obnavljaju iz javnih izvora; ništa iz `.local/` nije u
gitu. Rezultati faza 1 i 2 se ne mogu obnoviti bez ponovnog pokretanja (vidi ispod).

1. SimFire okruženje (Python 3.9, pinovano; freeze fajl je za macOS ARM64):
   [SIMFIRE_ENVIRONMENT](docs/research/SIMFIRE_ENVIRONMENT.md), komande `uv venv` i
   `uv pip install -r requirements/simfire-macos-arm64-py39.freeze.txt`.
2. Ulazi: `scripts/build_feds_simfire_inputs.py --fetch-split train`, zatim
   `--fetch-split validation`; `scripts/fetch_gridmet_archives.py --year 2018 2019 2023`;
   `scripts/sample_gridmet_episode_weather.py`. Tačne komande su u SIMFIRE_ENVIRONMENT.
   `--fetch-split` ponovo piše `reports/real-fire-data/feds-simfire-input-{split}-coverage-v1.json`;
   ta izmjena se ne commituje.
3. Ponovno generisan vremenski fajl dobija **novi sha256** (sampler upisuje `created_utc`).
   Zamrznuti zapis faze 1 navodi `7a51aadd…`. Za VALIDATION okruženje i benchmark odbijaju
   fajl čiji se hash ne slaže sa zamrznutim zapisom; na TRAIN-u se hash samo bilježi u
   izvještaj. Za poređenje s fazama 1 i 2 treba kopija tog fajla od Haruna; novi hash traži
   novi ADR prije korištenja VALIDATION-a. Manifest epizoda je u gitu (sha256 `013be9a1…`).
4. Provjera: `$P -m unittest discover -s tests` (314 testova u ovom lokalnom pinovanom
   runtimeu; u čistom checkoutu bez `.local/` testovi lokalnih podataka se preskaču),
   `python3 scripts/validate_knowledge.py --strict`, `git diff --check`.

**Šta postoji samo lokalno, na Harunovom računaru** (lokacije za orijentaciju, nisu preduslov
za rad; za poređenje s fazama 1 i 2 treba kopija od Haruna, inače ~15 h ponovnog treninga i
benchmarka):

- Python: `.worktrees/overnight-steps-5-8/.local/simfire-venv/bin/python`.
- Faza 1, TRAIN gate za izabranu postavku: `waf-0.1-ros-1.json` (`ba7e91aa…`).
- Vremenski fajl `7a51aadd…`: `.local/backups/gridmet/feds-episode-weather-v1-7a51aadd.json`.
- Faza 1, puni gate izvještaji: `.worktrees/task-026-stage-1/.local/gate/adr030/`.
- Faza 2: `.worktrees/task-026-stage-2/.local/ppo/adr030/` (40 modela),
  `.local/bench/adr030-train.json` (`709050e6…`), `.local/bench/adr030-validation.json` (`e8068e6b…`).
- Stari, neispravni vremenski fajl `7b0aa405…` u `.worktrees/overnight-steps-5-8/.local/gridmet/`
  je dokaz greške: ne dirati. Ne dirati ni necommitovane fajlove u tom worktreeu.
- Zaostali worktreeji (`.claude/worktrees/task-021…024`, `.worktrees/task-027-feds-utc-dedup`)
  i stari procesi (vidi [WORK_LOG](docs/WORK_LOG.md)) uklanjaju se samo uz Harunovo „da“.

## Artifact za tim

Pregled za čitaoca koji ne zna projekat, s dijagramima i grafikonima:
https://claude.ai/artifact/EFi7EXKkvehgTt1GYtoi5Q. Privatan je; Harun ga dijeli kroz meni
Share. Prati stanje repozitorija; kad se razilaze, važi repozitorij. Ko ga ažurira prvo ga
pročita preko linka, pa objavi na isti link. Kopija HTML-a je u
[docs/team-overview](docs/team-overview/README.md), za otvaranje bez pristupa linku.

## Historija

Canada + CFSDS/Cell2Fire, Firehose i noćni SimFire koraci 5–8 su raniji pravci; njihovi
brojevi se ne citiraju kao nalazi (ADR-029). Trag je u
[experiment logu](docs/research/EXPERIMENT_LOG.md) i [odlukama](docs/specs/DECISION_RECORDS.md).

### Sintetički CA (ADR-028; brojevi poništeni ADR-029)

Grane `codex/synthetic-ca-training`, `codex/overnight-steps-5-8` (PR #4) i
`codex/fireline-simfire-benchmark` (PR #3) su spojene u `main` kao historija (ADR-029); kod je
od tada ispravljen (PR #11), a brojevi ispod se ne citiraju. Komande su zapis kako je rađeno.

```sh
git clone https://github.com/goralija/wildfire-rl-adaptation.git
cd wildfire-rl-adaptation
```

**Okruženje.** Sav sintetički rad koristi Python 3.9 venv iz
[`requirements/simfire-macos-arm64-py39.freeze.txt`](requirements/simfire-macos-arm64-py39.freeze.txt)
(numpy 1.26.4, torch 2.3.1, gymnasium 1.1.1, sb3/sb3-contrib 2.7.1). Postupak je u
[SIMFIRE_ENVIRONMENT](docs/research/SIMFIRE_ENVIRONMENT.md). Komande ispod pretpostavljaju
`P=".local/simfire-venv/bin/python"` i `PYTHONPATH=src PYTHONWARNINGS=ignore`.

**Šta treba za šta.**

| Posao | Treba stvarne podatke? | Treba težine? |
|---|---|---|
| Testovi, sintetički trening, BC, validacija na sjemenima | ne | ne (osim `--resume`) |
| Jednokratni test na 119 startova (od TASK-027 118), dijagnostika, viewer | da: `.local/feds-simfire-cases` i gridMET | da |

**Težine** (~27 MB svaka) nisu u gitu. Prilozi su draft GitHub releasea
`synthetic-policy-v1`, koji vide samo članovi s pristupom repou. Preuzmi ih u
`.local/synthetic/locked/` i provjeri hash prije učitavanja (zip sadrži pickle):

```sh
mkdir -p .local/synthetic/locked
gh release download synthetic-policy-v1 --repo goralija/wildfire-rl-adaptation --dir .local/synthetic/locked
for m in policy-v1 bc2 main1-best; do shasum -a 256 -c reports/synthetic/$m.sha256; done
```

**Stvarni ulazi.** `.local/feds-simfire-cases` (~46 MB) i gridMET vrijeme obnavljaju se
iz javnih izvora po [SIMFIRE_ENVIRONMENT](docs/research/SIMFIRE_ENVIRONMENT.md):
`build_feds_simfire_inputs.py --fetch-split train`, zatim `--fetch-split validation`
(freeze zapis je commitan), plus `sample_gridmet_episode_weather.py`. Test split 2024
se ne preuzima. Fajl s vremenom iz TASK-027 (sha256 `7a51aadd…`, prolaz FEDS `t` u lokalnom
sunčevom vremenu) je u `.local/gridmet/` worktreea `task-027-feds-utc-dedup`, s kopijom u
`.local/backups/gridmet/` glavnog klona; worktree koji pokreće fazu 1 kopira ga u svoj
`.local/gridmet/` i provjerava hash. Svako ponovno generisanje daje novi hash (`created_utc`),
koji se onda mora upisati u izvještaj i freeze zapis.

**Komande** (stvarno korištene; sve izlaze u ignorisani `.local/`):

```sh
$P -m unittest discover -s tests -p "test_synthetic*.py"
# PPO od nule (main-1, ~4.5h na 6 procesa)
$P scripts/train_synthetic_ppo.py --steps 1500000 --eval-every 100000 --eval-seeds 64 --out .local/synthetic/runs/main-1
# Plan B: imitacija direct_flank (bc-2), pa PPO fine-tune (ft-1 -> policy-v1)
$P scripts/bc_warm_start.py --init .local/synthetic/runs/main-1/final_model.zip --teacher direct_flank --rounds 40 --episodes-per-round 42 --epochs 8 --keep-rounds 3 --workers 7 --out .local/synthetic/runs/bc-2/bc_model.zip
$P scripts/train_synthetic_ppo.py --resume .local/synthetic/runs/bc-2/bc_model.zip --steps 600000 --eval-every 100000 --eval-seeds 64 --learning-rate 1e-4 --ent-coef 0.001 --clip-range 0.1 --start-stage B --out .local/synthetic/runs/ft-1
# Prihvatanje na sjemenima 0-255 (pravilo iz ADR-028)
$P scripts/evaluate_synthetic_policies.py --seeds 256 --first-seed 0 --workers 7 --subset-from-seed 64 --policies noop,random,direct_flank,protect_urban,downwind_indirect,ppo=.local/synthetic/locked/policy-v1.zip --out .local/synthetic/acceptance.json
# Jednokratni test zaključanih politika na stvarnim startovima
$P scripts/evaluate_real_cases.py --policy-locked --comparator-heuristic direct_flank --workers 7 --policies noop,random,direct_flank,protect_urban,downwind_indirect,ppo=.local/synthetic/locked/main1-best.zip,ppo=.local/synthetic/locked/bc2.zip,ppo=.local/synthetic/locked/policy-v1.zip --out .local/synthetic/real-cases.json
$P scripts/diagnose_synthetic_calibration_gap.py --all --policy-locked --out .local/synthetic/calibration-gap.json
# Viewer: http://127.0.0.1:8766, politika protiv no-op na jednom stvarnom startu
$P scripts/synthetic_case_viewer.py --port 8766
```

**Otvorena timska odluka.** policy-v1 je izjednačen s `direct_flank` (prihvatanje FAIL),
a jasno je bolji od no-op. Treba odlučiti da li se ide dalje (DAgger, duži fine-tune,
oracle osnova za plafon) ili se rad zaključuje sa sadašnjim rezultatom. Za novi pokušaj
predlažemo novu preregistraciju i prihvatanje na novim sjemenima, jer su sjemena 0–255
već korištena za izbor checkpointa (napomena o selekciji u ADR-028). Detalji su u [NEXT_SESSION](docs/NEXT_SESSION.md) i ADR-028.
