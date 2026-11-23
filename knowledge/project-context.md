---
type: Project Context
title: Projektni kontekst i stanje istraživanja
description: Sažetak aktivnog SimFire/FEDS benchmarka, ADR-029 ispravki i otvorenih odluka.
status: stable
generated: {by: "process:claude-code", at: "2026-11-04T03:45:00Z"}
sources:
  - resource: /docs/STATUS.md
  - resource: /docs/NEXT_SESSION.md
  - resource: /docs/specs/DECISION_RECORDS.md
  - resource: /reports/real-fire-data/feds-simfire-train-noop-screen-v1.json
  - resource: /reports/real-fire-data/feds-simfire-policy-benchmark-v1.json
---
# Projektni kontekst

## TASK-045 završen — centriranje nije dovoljno (ADR-056, 2026-11-23)

[Izvještaj](../docs/research/CENTERED_PPO_PILOT.md), grana `codex/centered-ppo-pilot` iz `c2e53f4c`.
Plan0d8d3821 prije koda273cfb62; audit72fee0e1, vizualna dopunadf26661c.
Svih6×512koraka /768epizoda /12checkpointova završeno bez greške za20,05min,
21:43CET. Nema aktivnog treninga; raniji PID51639 i start/snapshot su historija.
Jedino je reward centriran; isti45TRAINfit/16development,3model seeda,globalclip,
MLP, B1,48h i vlastita fizika. Svi modeli i original512referenti sačuvani.

Na istih14joint-positive, original512→centered512: **SF6,75→3,16%**, **CA6,36→7,93%**.
Uparene razlike: SF−3,59pp[−8,75;−0,21], CA+1,57[−5,24;+7,80]. Prema tačno
uniformnoj liniji: SF−2,06[−6,43;+1,35], CA+1,73[−1,65;+5,02]. **Oba zamrznuta
kriterija nastavka su false.** CA sredina raste, ali opisni interval ne isključuje
pogoršanje. SF nalaz je negativan. TRAIN development nije nezavisan test ili
fizička validacija; stari TASK-043 nalazi ostaju nepromijenjeni.

Fiksni front11,29/3,35%, uniform5,23/6,20%, fit-only sektor6/7daje0,23/9,49%.
Novi savedha na svih16: SF138,24/CA84,04, pooled1,22/4,50%; SFzero-noop2ostaju
undefined. Politike su skoro uniformne i četiri od šest biraju jedan isti sektor
na16/16; sama promjena parametara nije dokaz naučene prilagodbe.

Nezavisni audit3.072step,192new+192original policy score,12+12model load,
96native putanja /480stanja,610reference stanja,32preflight i96firstrolloutstep PASS.
438pinned/0skip,423modern/4skip,328core/51skip i CLI PASS. Audit ne mijenja frozen
trening/fiziku. Detalji lokalnog paketa/restore i završna verifikacija u izvještaju.

**Sljedeći prijedlog TASK-046:** odvojeno zamrznuti mali pilot originalne nagrade
uz zasebni actor/critic clipping, isti512koraka i isti original512referenti. Nije
pokrenut; nema automatskog produžavanja ovih modela ili promjene više faktora.
Stvarni VALIDATION/TEST/futureFEDS/nativeunitparity/fizička validacija/merge ostaju
odvojeni. Za naredne odobrene duže poslove korisnik i dalje traži background start,
provjeren napredak, status/ETA i završetak chata dok računanje radi.


Završna provjera:15knowledge/strict94 PASS. Lokalni54.374.678Bpaket322člana plus
488/1035roditeljskih, svi hashovi provjereni. Puni restore iz kopiranog sourcea/ulaza/
12modela ponavlja192odluke/96native putanja/480stanja identičnim numeric nizovima,
uz iste postojeće biblioteke i bez novog treninga. Nema aktivnog računanja.

## TASK-044 završen — PPO signal/reference dijagnoza (ADR-054, 2026-11-23)

[Izvještaj](../docs/research/PPO_SIGNAL_DIAGNOSIS.md), `codex/ppo-signal-diagnosis` izc160fd0e.
Plan44658302 prije kodae1a28379. Nije rađen novi puni trening, nisu promijenjeni
TASK-043 reward/physics/checkpointovi ili oba neprošla learning kriterija.

Tačan uniformni first-line referent na istih14eval: **SF5,23%/CA6,20%**, naspram
starog finalPPO5,13/6,03%. Fiksni sektor biran samo po mean charged cells na45fit:
SF6(NW),CA7(N), na16development daje0,23/9,49%. Svi sektori/denominatori prikazani.
Između-požarna varijansa početnog troška je99,89/99,46%; nakon oduzimanja vlastitog
no-op13,91/27,15%, unutarpožarna varijansa/poredak poteza isti.

Svih6prvih16step rollouta ponavlja stare96training redova i početne težine.
U24disposable Adam probama globalno clipping smanjuje actor; zasebni clip daje
1,40–6,88×veći actor korak. Centriranje sa istim globalclipom daje1,74–4,45×u5/6
proba, ali **CA43pada na0,62×**. To je početni mehanizam, ne dokaz za cijeli trening
ili novu policy performance prednost. Actorparametri se jesu promijenili; Tanh
na početnim61opažaju nije zasićen.

Nezavisno405CA putanja/2.025maski i SFlinegeometrija, initialparity45,24gradient
reprodukcije i18parameterdelta provjera PASS.423pinned/0skip,408modern/4skip,
322core/49skip,15knowledge,CLI/strict93PASS. Lokalni49.496.735Bpaket488fajlova plus
manifest iugrađeni1035fajlova roditelj; svi hashovi potvrđeni. Restore novog koda/
ulaza/modela:9CA putanja svježe,32SF/CA rollout koraka,8fresh gradientmodes; ponovni
audit405pohranjenih putanja/24modes/18modela PASS uz iste numeričke nizove.

**Sljedeći prijedlog TASK-045:** preregistrovani512step centering-only pilot uz iste
globalclip/hiperparametre/45fit/16development/3seeda oba modela, poređenje sa sačuvanim
original512checkpointovima. Nije implementiran ili pokrenut. Nema aktivnog punog
treninga, stvarnog VALIDATION/TEST, futureFEDS-a, fizičke validacije ili mergea.

## TASK-043 završen — nijedan backend ne prolazi learning kriterij (ADR-052, 2026-11-22)

[Upareni PPO izvještaj](../docs/research/PAIRED_PPO_LEARNING.md), `codex/paired-ppo-learning`,
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

## TASK-040 B.1 završen — zajednički PPO/reward ugovor (ADR-050, 2026-11-22)

[Zajednički interfejs](../docs/research/COMMON_PPO_INTERFACE.md) na `codex/common-ppo-interface`,
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

## TASK-042 završen — svih 61 kompatibilnih TRAIN početaka (ADR-048, 2026-11-21)

[Prošireni audit](../docs/research/EXPANDED_OBSERVED_GROWTH.md) je završen na `codex/ca-expanded-growth-audit`, iz2de00136.
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

## TASK-041 završen — opaženi rast (ADR-046, 2026-11-21)

Na `codex/ca-feds-growth-audit`, iz640a910e, završen je [TRAIN audit](../docs/research/PAIRED_OBSERVED_GROWTH.md).
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

## TASK-040 faza A završena — upareni simulatori (ADR-044, 2026-11-21)

Na `codex/ca-simfire-paired`, iz `722d5f2d`, završen je [upareni pilot](../docs/research/CA_SIMFIRE_PAIRED.md).
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


## TASK-038 završen — CA v2 BC/PPO (ADR-042, 2026-11-21)

Na `codex/ca-learning-pilot` iz3b7b56a2 završen je [kratki CA learning pilot](../docs/research/CA_LEARNING_PILOT.md).
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


## CA ugovor i pilot završeni — TASK-035 / ADR-040 (2026-11-21)

Korisnikov CA nastavak je izveden na `codex/ca-controlled-pilot`, iz `664d890d` završene
SimFire repair grane. [Izvještaj](../docs/research/CA_CONTROLLED_PILOT.md) i zamrznuti plan čuvaju
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


## Najnovije — observation v2 (ADR-038, 2026-11-20)

Korisnikov dodatni SimFire pokušaj je izveden na `codex/simfire-observation-repair`.
[Izvještaj](../docs/research/SIMFIRE_OBSERVATION_REPAIR.md) bilježi ispravan kategorijski
fuel/nonfuel prikaz i lokalnu geometriju,98 identičnih no-op putanja i uparene rezultate.
Fine+gate daje 123,72 charged ha prema 101,04 starog pravila, uz interval koji uključuje 0.
Primarni naučeni model daje 71,18 ha prema 123,72 jače reference; niko ne prelazi prag.
Prethodni PR #20 ostaje otvoren; novi PR nije potreban. Nema mergea, novih holdout ili
PPO/CA treninga. CA draft TASK-035 i preostali SimFire put TASK-037 su jasno odvojeni.

## Nastavak 2026-11-20 — ADR-036

TASK-034 je završen na lokalnoj `codex/simfire-observation-audit`.
[Izvještaj](../docs/research/SIMFIRE_OBSERVATION_AUDIT.md) bilježi provjerene ulaze,
fuel/front aliasing, četiri nested metode bez prolaza i native numeričke osjetljivosti.
Startup race je ispravljen bez promjene dinamike. Postoji obrazložena preporuka za
TASK-035, kontrolisani CA ugovor/pilot; nije pokrenut. SimFire v2 ostaje smislen, ali
novi protokol, ne samo još jedan trening. Nema tvrdnje da su sve moguće greške isključene,
fizičke validacije, novih VALIDATION/TEST ili CA treninga.

## Nastavak 2026-11-19 — ADR-034

Korisnik je odabrao SimFire i odobrio dokumentovane TRAIN iteracije TASK-028–030 na
novoj grani. [SimFire B=1 izvještaj](../docs/research/SIMFIRE_B1_EXPLORATION.md) bilježi
završenu tabelu 98×33 i osam LOO metoda u oba obračuna. Nijedna ne dostiže prag za
nastavak: velik oracle jaz nije prenesen na izostavljene požare. Sljedeći prijedlog
je TASK-034, dijagnoza prostornog signala iz istog opažanja; nije pokrenut.
VALIDATION/TEST nisu ponovo korišteni, CA faza 3 nije pokrenuta, novi rad je lokalni.

## Dosadašnji SimFire pravac (historija)

Korisnik je odabrao **SimFire + FPA-FOD + FEDS-CONUS**, uz FLE/ICS-209 samo kao
ograničeni post-hoc kontekst. Split je po godini: train 2018/2019 (98 požara nakon deduplikacije), validation
2023 (20), test 2024 (zatvoren). Okvir obuhvata veće požare u deset zapadnih država i nije
reprezentativan za sve požare. FEDS/FPA veza ostaje provisionalna.

## Aktuelno — ADR-029, 2026-11-09: rezultati nevažeći, prvo ispravke

- **Greška.** gridMET uzorkovanje je svim požarima jedne godine davalo vrijeme prvog
  požara te godine (97/99 TRAIN, 19/20 VALIDATION). Ispravljeno u PR #3.
- **Posljedica.** SimFire gate, validacija, benchmark, studija budžeta i test CA politika
  na stvarnim požarima (ADR-022–028) nisu važeći zaključci; sekcije ispod su historija.
- **Druge potvrđene greške.** IoU uključuje početnu površinu; dijagonalne linije
  propuštaju vatru; PPO nije bolji od nasumične linije; u CA se napredak linije briše pri
  promjeni smjera, a ćelije linije se računaju kao spašene.
- **Ispravke.** TASK-021–027 su spojeni; odluke su u ADR-029 i ADR-030.
- **Faza 1 (ADR-031, 2026-11-09).** Gate po IoU rasta je prošao na 98 TRAIN požara; zamrznut
  je WAF 0.10 / ROS 1.0 (0.0958 prema 0.0258 za elipsu), VALIDATION ocijenjen jednom (0.0983
  prema 0.0278). Oba IoU su ispod 0.10 i simulator prerasta nerastuće požare, pa PASS nije
  fizička validacija.
- **Faza 2 (ADR-032, 2026-11-10).** Benchmark s 10 seedova na tom zapisu: nijedan od šest
  primarnih testova ne odbacuje nultu hipotezu; osnovni PPO se ne razlikuje od nasumične legalne
  linije ni od najbolje TRAIN heuristike, a fine-tuning po budžetu ne daje mjerljiv dobitak.
  Većina politika nauči jedan fiksan smjer. Simulatorski rezultat, ne dokaz o gašenju. Faza 3
  čeka korisnikovu odluku; redoslijed je u [NEXT_SESSION](../docs/NEXT_SESSION.md).

- **Pregled 2026-11-11.** Literatura i dijagnoza nakon faze 2, bez treninga: rezultat je
  očekivan; kratke epizode vjerovatno nisu uzrok; ključno je da li se najbolja linija može
  predvidjeti iz opservacije. Plan TASK-028–033 i odluke koje čekaju:
  [sažetak](../docs/research/review-2026-11-11/SUMMARY.md).

## Ranije — sintetički CA trening (ADR-028), 2026-11-05

- **Trening.** Agent se trenira samo na proceduralno generisanim sintetičkim požarima,
  u vlastitom CA simulatoru ([spec](../docs/research/SYNTHETIC_CA_ENV.md)):
  - vjerovatnoća paljenja zavisi od tipa goriva;
  - jedinice imaju fizičke brzine kretanja i gradnje linije;
  - nagrada je kontrafaktualna, protiv no-op rollouta;
  - jedinice se povlače po LCES pravilu i kažnjavaju se bliski susreti i gubici.
- **Uloga stvarnih slučajeva.** 119 FEDS startova služi samo kao jednokratni test
  zaključanih politika. Ishod je simuliran.
- **Rezultat.**
  - PPO od nule nije dostigao heuristiku.
  - `policy-v1` (imitacija direct_flank, pa PPO) je na sintetičkoj validaciji izjednačena
    s direct_flank (preregistrovani kriterij: FAIL) i jasno bolja od no-op.
  - Na stvarnim startovima čuva u prosjeku 12% no-op štete po slučaju više od no-op, uz
    upola manje bliskih susreta od direct_flank.
- **Granica.** Jaz kalibracije prema FEDS-u je velik (medijan IoU 0.27–0.30 na 48h).
  Detalji su u ADR-028 i [izvještajima](../reports/synthetic/index.md).
- **Odnos prema ranijem radu.** Koraci 5–8 ispod su historijski i ostaju na snazi kao
  dokaz da SimFire gate pada.

## Stanje koraka 5–8 — 2026-11-04

- **Kalibracija (korak 5) je FAIL.** Nakon dijagnoze i preregistrovane 3×3 mreže
  (ADR-023/024) nijedan zajednički SimFire parametar ne pobjeđuje persistence i elipsu
  istovremeno na TRAIN-u. Deficit dolazi iz požara koji u FEDS-u ne rastu, vjerovatno
  zaustavljenih ili ugašenih; slobodno-goreći no-op to ne može predstaviti. Zamrznuti
  gate zapis je `FAIL_exploratory` i gotovo ne širi vatru.
- **Validation (korak 6)** je skoriran jednom po zapisu
  ([izvještaj](../reports/real-fire-data/feds-simfire-validation-noop-v1.json)).
- **Koraci 7–8** rade na zasebnom, jasno označenom free-burn stress zapisu (ADR-024–027):
  jedinica budžeta je smjena ekipe od 20 ljudi = linija od ~1.26 km. Osnovni PPO pobjeđuje
  no-op, fine-tuning po budžetu nema mjerljive koristi, a downwind heuristika je jednako
  dobra ili bolja ([sažetak](../reports/real-fire-data/feds-simfire-policy-benchmark-v1.json)).

## Šta je potvrđeno, a šta nije

- Ulazi i no-op rezultati su reproducibilni na drugom računaru (isti hashovi, isti IoU).
- Benchmark je determinističan; politike dobijaju iste scenarije, budžete, opservacije i seed.
- Nije potvrđena fizička kalibracija SimFire-a, korist RL-a u stvarnom gašenju, niti
  korist prilagodbe budžetu. FEDS su satelitske procjene, gridMET je grubi proxy.
- Prioritetna područja (TASK-007), gradnja linije kroz vrijeme i TEST evaluacija nisu rađeni.

## Šta prvo raditi

Aktuelni redoslijed je u [NEXT_SESSION](../docs/NEXT_SESSION.md) i
[pregledu 2026-11-11](../docs/research/review-2026-11-11/SUMMARY.md); lista ispod je iz
2026-11-04 i historijska.

1. Timski odlučiti o growth-aware gateu ili modelu zaustavljanja prije tvrdnje o
   kalibraciji, i o tome da li stress scenarij ostaje radni simulator.
2. Ako se nastavlja korak 8: nova preregistracija s jačim signalom budžeta (više linija po
   odluci ili duži vijek aktivne ćelije) i više seedova.
3. TASK-007 i TASK-009 (poster); TEST 2024 tek na kraju, sa zaključanim politikama.

TASK-012 CFSDS izbor i Firehose TASK-004c su historijski, odvojeni pravci. Kasnija
odluka/ADR ima prednost nad starijim task opisima.

## Kako nastaviti

1. Pročitati [STATUS](../docs/STATUS.md), [NEXT_SESSION](../docs/NEXT_SESSION.md) i
   najnoviji unos u [odlukama](../docs/specs/DECISION_RECORDS.md).
2. Koristiti [HANDOFF](../HANDOFF.md) za novi klon i
   [mapu koda](code-map.md) za relevantne fajlove.
3. Nakon bitnog pomaka osvježiti izvore i navigaciju prema
   [pravilima održavanja](maintenance.md).

Ovaj sažetak je ulaz za ljude i agente; detaljni izvještaji/odluke su kanonski.
Ako su u sukobu, najnovija korisnička odluka i najnoviji ADR imaju prednost; ažurirati
sažetak i zabilježiti neslaganje.
