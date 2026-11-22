---
type: Handoff
title: Naredni korak — nakon zajedničkog PPO ugovora (2026-11-22)
---
# Naredni korak

## TASK-043 trening pokrenut u pozadini — ADR-051, 2026-11-22

Korisnik je odobrio duži lokalni upareni PPO pilot. [Plan i handoff](research/PAIRED_PPO_LEARNING.md),
`codex/paired-ppo-learning` iz720c914b; plan d586c1bc prije koda13a234ba.45TRAIN fitting
i16ranije istraženih development evaluation,3model seeda×2backend-a×2048koraka.
Isti B.1 encoder/MLP/reward/akcije/budžet/horizont, svi0/512/2048checkpointovi, bez
best-selection. Stvarni VALIDATION/TEST i merge zatvoreni. Ovo još nema learning rezultat.

**Prije starta prošlo:**408pinned/0skip,393modern/4skip,310core/48skip,15knowledge,
CLI/strict92. Ulazi/receipt-i svih61,122guarded no-op putanje, početni v2/maske
svih16isti i132native putanje (puni33×prva2slučaja×2backend-a) po cijelim finalnim
burned/line maskama i scoreu odgovaraju starim arhivama. Preflight102,47s.

Grana je pushana; [CI na0cb67456](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/45066883345)
prolazi sva4posla. Sva3radnika su potvrđeno prešla64koraka bez grešaka; korisniku
preporučen povratak za oko75min. Ovo je snapshot, živi lokalni status ima prednost.

**Aktivno:** koordinator PID37835 u nezavisnoj sesiji, nice19, najviše3radnika i
jedna numerička nit po procesu. Lokalni izlaz `.local/paired-ppo-v1`, procjena45–75min.
Prije nastavka pročitati `status.json`, `job-*/status.json`, `coordinator.lock`,
`error.json`/`stop.json`, te `analysis.json` ako postoji. Ne pokretati dupli posao.
PID je historija starta, ne dokaz da je još aktivan: provjeriti proces i heartbeat.

Po završetku nezavisno provjeriti6poslova/3072epizode, sve18checkpointova,288policy
skorova i96native finalnih putanja, početne težine po seedu, matematiku procenta/
hektara i paired bootstrap po požaru. Sve seedove/0-512-2048stupnjeve prijaviti;
PPO-minus-istoj-front-heuristici i CA-minus-SF relativni gap obavezni. Zatim figure,
local bundle/restore, finalni testovi, ADR/experiment log i objava. NPZ nije optimizer
resume; nepotpun posao traži dokumentovan novi pokušaj, završeni samo uz iste hashove.

## TASK-040 B.1 završen — zajednički PPO/reward ugovor (ADR-050, 2026-11-22)

[Zajednički interfejs](research/COMMON_PPO_INTERFACE.md) na `codex/common-ppo-interface`,
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

[Prošireni audit](research/EXPANDED_OBSERVED_GROWTH.md) je završen na `codex/ca-expanded-growth-audit`, iz2de00136.
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

### Predloženi nastavak TASK-040 B.1: mali tehnički ugovor

1. Zamrznuti zajednički PPO interfejs u oba backend-a: isti v2 input/encoder,9sector/no-op
   akcija, B=1,48h i isti slučajevi/raspoloživa informacija. Bez future FEDS/no-op otiska u opažanju.
2. Prije ponašajne promjene testirati isti obračun štete/nagrade, maske, prior i budžet.
   Postojeći raw reward i charged evaluacija nisu tiho izjednačeni ovim auditom.
3. Tek nakon ugovora predložiti kratak tehnički train/replay smoke, s istom arhitekturom,
   seedovima i budžetom koraka. Tehnički PASS nije RL prednost; veći trening traži novi plan.
4. Raniji CA urban/unit PPO i mobilne jedinice ostaju zaseban MDP. B.1 ga ne preimenuje
   u uporediv native resursni benchmark; taj dio faze B ostaje otvoren.

B.1 nije pokrenut. Nema novog dugog treninga ili stvarnog VALIDATION/TEST. Širi frozen61
no-op audit je završen; novo širenje istog kompatibilnog spiska nije naredni zadatak.

## TASK-041 završen — opaženi rast (ADR-046, 2026-11-21)

Na `codex/ca-feds-growth-audit`, iz640a910e, završen je [TRAIN audit](research/PAIRED_OBSERVED_GROWTH.md).
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

### Predloženi TASK-042: redoslijed i prihvat

1. Prije novog skora preregistrovati svih61eligible ID-jeva iz TASK-040 ulaznog QC-a,
   iste fizičke parametre, tri postojeća CA spread seeda i SF no-op. Bez izbora po rezultatu.
2. Isti exact-time/whole-vector loader; predikcije zaključati prije opažanja. Izvještaj
   mora zadržati svaki slučaj, missing/coverage razloge i posebno nerast/slab rast.
3. Ne tiho širiti ili pomjerati samo Martinovu mapu prema targetu. Veća domena je novi
   protokol; existing map rezultat ostaje jasno cenzurisan. Ne podešavati WAF/ROS po ovih16.
4. Ponoviti zajedničke metrike/denominatore i case-level intervale; tek po širem nalazu
   predložiti kalibraciju ili TASK-040 fazu B za native resurse/akcije/PPO ugovor.

TASK-042 još nije pokrenut. TEST/VALIDATION i dugi trening ostaju zatvoreni. Stariji
TASK-041 prijedlozi ispod su historija i zamijenjeni završenim ADR-046.

## TASK-040 faza A završena — upareni simulatori (ADR-044, 2026-11-21)

Na `codex/ca-simfire-paired`, iz `722d5f2d`, završen je [upareni pilot](research/CA_SIMFIRE_PAIRED.md).
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


### Redoslijed predloženog nastavka

1. Prije novog skora zapisati TASK-041 plan: isti16 TRAIN, isto48h poravnanje FEDS
   opažanja, bez promjene modela, s odvojenim observed/no-growth i missing-data slučajevima.
2. Uporediti rast i prostorni otisak prema opažanju: new-area IoU bez početne štete,
   apsolutna/relativna površina i nerast; sačuvati oba simulatora i sve3 CA spread replike.
3. Prvo provjeriti vremensko poravnanje, gorivost početnog fronta i opažajnu pokrivenost;
   neslaganje nije automatski greška simulatora ili dokaz da je FEDS potpuna istina.
4. Tek po tom nalazu predložiti kalibraciju na TRAIN-u ili TASK-040 fazu B. Bez otvaranja
   VALIDATION/TEST, vraćanja poništenih ADR-022–028 nalaza ili automatskog dugog PPO treninga.

Ovaj redoslijed je prijedlog; TASK-041 još nije pokrenut i parametri nisu podešavani.

## TASK-038 završen — CA v2 BC/PPO (ADR-042, 2026-11-21)

Na `codex/ca-learning-pilot` iz3b7b56a2 završen je [kratki CA learning pilot](research/CA_LEARNING_PILOT.md).
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

Redoslijed: provjeriti sačuvane manifeste i rezultate, pročitati ADR-042, potom TASK-039
plan prije novih poteza/treninga. Ne ponavljati završeni pilot bez razloga i ne otvarati
testne liste. Stari tekst TASK-038 kao prijedloga ili rada u toku je historija.


### Objava TASK-038

Grana [codex/ca-learning-pilot](https://github.com/goralija/wildfire-rl-adaptation/tree/codex/ca-learning-pilot)
je commitana i pushana. [CI na kodnom/rezultatskom commitu1d4209be](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/44840927699)
prolazi sva četiri posla. Verification čuva tačan testirani commit; kasnija dopuna
objave ne mijenja numerički kod. Paket modela ostaje lokalni; nema novog PR-a ili mergea.


## CA ugovor i pilot završeni — TASK-035 / ADR-040 (2026-11-21)

Korisnikov CA nastavak je izveden na `codex/ca-controlled-pilot`, iz `664d890d` završene
SimFire repair grane. [Izvještaj](research/CA_CONTROLLED_PILOT.md) i zamrznuti plan čuvaju
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

Redoslijed nastavka: pročitati CA izvještaj/ADR-040, provjeriti manifeste i sačuvane
ishode, zatim napisati TASK-038 plan prije novih modela ili metrike. Ne ponavljati
završeni pilot bez razloga. Nijedan dugi posao trenutno ne radi.


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
prethodnog rada ostaje otvoren. [Publication receipt](../reports/real-fire-data/feds-observation-repair-publication-v2.json)
čuva tačan testirani commit. Kasnija dopuna publikacijskih podataka ne mijenja numerički
kod. Veliki lokalni paket nije uploadovan.

## Nakon v2 popravka — redoslijed (ADR-038, 2026-11-20)

1. Pročitati [završni v2 izvještaj](research/SIMFIRE_OBSERVATION_REPAIR.md) i rezultate.
   FazaA TASK-036 je završena. Ne ponavljati 98 replayeva ili 16 fit kombinacija ako
   sačuvani manifesti i hashovi prolaze. V2 i jača fine+gate heuristika su referenca
   za svaki naredni SimFire pokušaj; ne vraćati se na slabiji comparator bez objašnjenja.
2. Kolege mogu pregledati [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
   prethodnog rada i izvedenu `codex/simfire-observation-repair` granu. Novi PR nije
   potreban po korisniku; ništa nije mergeano. Pratiti CI objavljene grane.
3. Predloženi naredni glavni korak je TASK-035: CA ugovor informacija i tehnički pilot
   iz postojećeg drafta. Ne vraćati stare poništene checkpointove ili automatski trenirati;
   prvo definisati opaženo vrijeme, verzije, slučajeve, budžete i jake heuristike.
4. Ako se dalje bira SimFire, TASK-037: max/korak kroz novi TRAIN gate i novu tabelu;
   zatim custom v2 encoder/checkpoint i unaprijed zadati BC/PPO protokol. Povratak na
   B=2/B=4 ne može koristiti B=1 tabelu poslije prve linije.
5. TEST 2024 i nova VALIDATION upotreba ostaju zatvoreni. Raw env nagrada nije promijenjena
   u charged; taj trening ugovor mora biti eksplicitan prije novog PPO-a.

Popravak informacija je potvrđen. Njegov policy dobitak je preliminaran, nijedan
naučeni kandidat ne prolazi, a svih mogućih algoritama/SimFire grešaka nije dokazano odsustvo.

## Korisnikov nastavak — popravak opažanja prije CA (2026-11-20)

Završeni rad je pushan i otvoren kao [PR #20](https://github.com/goralija/wildfire-rl-adaptation/pull/20)
prema `main`, za pregled kolega. PR ostaje otvoren. Korisnik je odobrio još jedan
SimFire pokušaj: TASK-036 sada ima prioritet pred CA pilotom TASK-035.
Nastavak ide iz ove grane u `codex/simfire-observation-repair`, u izdvojenom worktreeu;
novi PR nije potreban po posljednjoj korisnikovoj poruci. Precizni plan ide prije
novih mjerenja. VALIDATION/TEST i novi CA trening ostaju zatvoreni.

## 2026-11-20 — završen TASK-034 (ADR-036)

Ulaz je [završni pregled](research/SIMFIRE_OBSERVATION_AUDIT.md): četiri nested porodice
bez prolaza praga, svi input/observation checkovi, potvrđeni startup fix i mala native
sensitivity studija. Nema aktivnog runa; ne ponavljati eksperimente bez provjere artefakata.

1. Predloženi glavni nastavak: **TASK-035 — CA ugovor informacija i tehnički pilot**,
   [pripremljen draft](../configs/drafts/ca-controlled-pilot-v1.json). Prvo zapisati šta
   CA opaža (sada koristi weather.at(decision)), verziju opservacije i checkpointa,
   razdvojene proceduralne slučajeve, jedinice i budžete. Ne učitavati stare poništene politike.
2. Potom no-op i jake heuristike uz isti scenario, informacije i common random numbers;
   kratki BC/PPO tek po novom protokolu i unaprijed zadanom kriteriju. Sada nije pokrenuto.
3. Opcionalni **TASK-036 — SimFire v2**: kategorijski fuel/nonfuel, reljef/finija opservacija,
   max/korak kroz novi TRAIN growth gate, pa nova tabela i komparatori. To je preostali
   smisleni pravac, ne dokaz da je svaka SimFire mogućnost iscrpljena.
4. TEST 2024 ostaje zatvoren; nema novog VALIDATION odobrenja. Stari CA ADR-028 nalazi
   ostaju poništeni. Novi rad je na lokalnoj grani `codex/simfire-observation-audit`;
   prethodna grana je na originu, ova nije pushana/mergeana. Lokalni paket treba sačuvati.

Preporuka CA pilota je obrazloženi projektni izbor, ne fizička validacija CA ili dokaz
RL prednosti. Precizni CA protokol još nije prihvaćen niti izvršen.

## 2026-11-19 — završen odobreni SimFire ciklus (ADR-034)

TASK-028–030 su završeni na lokalnoj grani `codex/simfire-policy-iterations`.
[Izvještaj i komande](research/SIMFIRE_B1_EXPLORATION.md) su ulaz za nastavak.
Puna tabela 98 požara i svih osam LOO metoda su provjereni; nijedna metoda nije
prešla prag iz ADR-033. Po tom stop-uslovu nisu pokretani novi PPO, holdout ili
CA eksperimenti. PR #19 je već u `main`-u; nova grana je pushana na origin
po korisnikovom nalogu 2026-11-19, bez PR-a ili mergea.

1. Pročitati ADR-034, izvještaj i [manifest lokalnog paketa](../reports/real-fire-data/feds-b1-artifact-manifest-v1.json).
   Ne ponavljati 93-minutnu enumeraciju ako su sačuvani artefakti i hashovi ispravni.
2. Predloženi TASK-034: zapisati mali TRAIN-only protokol za prostorni signal u istom
   opažanju i stabilnost izbora kroz požare. Ne birati nove metode ili pragove na
   postojećim OOF rezultatima pa ih predstavljati kao nezavisnu potvrdu.
3. Zvanični obračun linije, novi observation kanali, B=2/B=4 i novo VALIDATION korištenje
   ostaju otvorene odluke. TEST 2024 ostaje zatvoren; CA nije aktivni pravac.
4. Push grane je urađen; PR i merge nisu. Sačuvati lokalni paket iz `.local/b1/artifacts/`;
   veliki artefakti nisu uploadovani. Njihovo remote arhiviranje ostaje zaseban nalog.

Starije sekcije ispod su historija; njihovo čekanje odobrenja TASK-028–030 je razriješeno.

## Najnovije — 2026-11-12: pregled završen; prvo provjera gornje granice na TRAIN-u

Faze 1 i 2 su gotove, a [pregled 2026-11-11](research/review-2026-11-11/SUMMARY.md) je
odgovorio na pet pitanja nakon ADR-032. Polazna tačka za novu osobu ili agenta je
[HANDOFF](../HANDOFF.md).

1. **Harun:** merge PR #19 (pregled i HANDOFF). Faze 1 i 2 su već u `main`-u (PR #17, #18).
2. **Harun odlučuje:**
   - kako se računa šteta kad linija zauzme ćelije koje bi izgorjele (sada „spašene“);
   - da li se pokreću TASK-029 i TASK-030 (samo TRAIN, eksploratorno, bez ADR-a);
   - ranije otvoreno: glavni simulator za poster, CA observation, faza 3.
3. **Sljedeći posao uz „da“** ([BACKLOG](BACKLOG.md)):
   - TASK-028: pomoćna funkcija za ocjenu s naplatom linije (test prije koda);
   - TASK-029: iscrpna B=1 tablica (33 niza po požaru), pilot na 20 TRAIN požara mora dati
     iste ishode kao TRAIN benchmark, pa svih 98 (ukupno ~1,5 h na 4 procesa);
   - TASK-030: offline ocjena pravila, selektora i tabelarnog RL-a uz LOO po požaru; nastaviti
     samo ako je dobitak izvan podešavanja ≥30 ha i ≥25% jaza.
4. Planer, B=2/B=4, novo korištenje VALIDATION-a i novi trening traže ADR prije pokretanja.

## 2026-11-10: faze 1 i 2 su gotove; čekaju se korisnikove odluke

Faza 2 je izvedena po ADR-030 §4 na zamrznutom zapisu: nijedan od šest primarnih testova ne
odbacuje nultu hipotezu, a osnovni PPO se ne razlikuje od nasumične legalne linije ni od
najbolje TRAIN heuristike (intervali su široki). Brojevi su u [ADR-032](specs/DECISION_RECORDS.md) i
[STATUS](STATUS.md).

1. **Korisnik:** pregled i merge PR-a faze 1 (`f/task-026-stage-1`), zatim PR-a faze 2
   (`f/task-026-stage-2`, otvoren prema grani faze 1).
2. **Korisnik odlučuje prije faze 3:** koji je simulator glavni za poster, i da li sintetički
   CA smije posmatrati forcing tekućeg koraka (`src/wildfire_rl/synthetic_env.py`;
   HANDOFF_STAGE_1_2, §8).
3. **Pitanja koja je faza 2 otvorila** (nisu odlučena, ne mijenjaju ADR-030 §4):
   - Većina politika nauči jedan fiksan smjer. Da li vrijedi duži trening ili drugačiji
     observation, ili se nalaz prijavljuje kakav jeste.
   - Nasumična legalna linija je jedna realizacija (isti seed u svakom scenariju). Prosjek
     preko više nasumičnih seedova bio bi pošteniji komparator, ali to je nova odluka.
   - `downwind` je na VALIDATION-u bolji od `advancing_front`, koji je izabran na TRAIN-u s
     razlikom od 6.7 ha.
4. Zaostali worktreeji se uklanjaju samo uz korisnikovo „da“.

## 2026-11-09: faza 1 PASS (ADR-031)

Gate na TRAIN-u je prošao po ADR-030 §3: zamrznut je WAF 0.10 / ROS 1.0
(`configs/frozen/feds-simfire-growth-gate-freeze-v1.json`, sha256 `7639e3a9…`), a VALIDATION
je ocijenjen jednom. Brojevi i granice su u [ADR-031](specs/DECISION_RECORDS.md) i
[STATUS](STATUS.md).

1. **Korisnik:** pregled i merge PR-a faze 1 (grana `f/task-026-stage-1`).
2. **Faza 2 (autonomno):** grana `f/task-026-stage-2`, izvedena iz grane faze 1.
   Trening po ADR-026 sa 10 seedova, TRAIN benchmark za izbor heuristike, jedan VALIDATION
   benchmark, analiza po ADR-030 §4 i broj epizoda u kojima linija spali više od no-op-a.
   Komande su u [HANDOFF_STAGE_1_2](HANDOFF_STAGE_1_2.md), §6. Rezultat ide u novi ADR i EXP-020.
3. **Faza 3 ne kreće** bez korisnikove odluke o glavnom simulatoru i o observationu u
   sintetičkom CA (HANDOFF_STAGE_1_2, §8).

Zamrznuti zapis je free-burning scenarij koji prolazi unaprijed zadano pravilo, ne kalibrisan
model: na nerastućim požarima znatno prerasta opaženo. To ograničenje važi i za fazu 2.

## 2026-11-09: rezultati ADR-022–028 su nevažeći, prvo ispravke (ADR-029)

Revizija PR-ova #3–#5 našla je grešku u gridMET uzorkovanju: 97/99 TRAIN i 19/20
VALIDATION požara dobili su vrijeme drugog požara. Greška je ispravljena (PR #3), PR-ovi
#3–#5 su spojeni u `main` kao historija, a **brojevi iz ADR-022–028 se ne citiraju** dok
se ne ponove. Detalji i potpun spisak grešaka: [ADR-029](specs/DECISION_RECORDS.md).

**Redoslijed.** Ispravke TASK-021–024 su urađene, nezavisno revidirane, popravljene i
spojene 2026-11-09 (PR-ovi #8, #9, #12, #11); pravila koja su pritom precizirana su u
dopunama ADR-030.
1. **TASK-021 — CI: urađeno (PR #8).** Posao `numeric` pokreće sve testove osim
   SimFire/sb3/lokalnih podataka; preskočeni testovi moraju tačno odgovarati
   `tests/ci_expected_skips.txt`.
2. **TASK-022 — metrike i gate: urađeno (PR #9).** IoU samo rasta, downwind elipsa od vodeće
   ivice fronta, `growth_gate` po ADR-030 §3 (rastući požari, IoU po požaru zbirno kroz
   četiri tačke).
3. **TASK-023 — SimFire okruženje: urađeno (PR #12).** Linije bez dijagonalnih rupa, budžet po
   dužini, linija ne "štedi" kad čeka i drži do efektivnih 980 ft/min, agent vidi gridMET
   dan strogo prije sljedećeg segmenta (novi pre-start zapis), statistika ADR-030 §4,
   checkpointi vezani za postavke, ista zaštita VALIDATION-a i fiksni korak od 5 min u
   no-op putanji, lokalni RNG.
4. **TASK-024 — sintetički CA: urađeno (PR #11).** Napredak vezan za ćeliju, ćelije linije
   u no-op otisku se plaćaju i u nagradi, prihvat po ADR-030 §5, test na stvarnim
   slučajevima je opisni s unaprijed zadanom heuristikom.
5. **TASK-025 — odluke: urađeno u [ADR-030](specs/DECISION_RECORDS.md).** Agent vidi
   vrijeme prethodnog segmenta; umanjenje linije se skalira s korakom, a korak je fiksno
   5 minuta; gate se mjeri IoU-om rasta na požarima koji rastu (≥1.10× površine za 48h)
   prema downwind elipsi, bez dodira s rubom; benchmark ima 10 seedova i glavna poređenja
   PPO prema nasumičnoj liniji i najboljoj TRAIN heuristici (tačni test, Holm); u CA je
   glavni ishod spašena površina, a sigurnost uslov neinferiornosti; sugar-pine ostaje,
   columbus ispada (98 TRAIN).
6. **TASK-026 — ponovno pokretanje u tri faze, svaka uz izričit nalog (ADR-030 §7).**
   Faza 1 bez treninga (manifest bez duplikata, nove gridMET vrijednosti s hashom, gate,
   zamrzavanje, jedna VALIDATION ocjena) tek kad su TASK-021–024 spojeni i FEDS vremenska
   zona provjerena. Faza 2: SimFire benchmark i studija budžeta. Faza 3: ponovni trening CA
   politika, tek nakon odluke koji je simulator glavni za poster.
7. **TASK-027 — spojeno (PR #15, 2026-11-09), nakon nezavisne revizije.**
   Columbus je isključen pravilom u generatoru manifesta (98 TRAIN, 20 VALIDATION). FEDS `t`
   je oznaka VIIRS prolaza u lokalnom sunčevom vremenu, ne UTC; korisnik je izabrao preračun
   01:30/13:30 lokalno → UTC po dužini ([dopuna ADR-030](specs/DECISION_RECORDS.md),
   [dokazi](research/SIMFIRE_ENVIRONMENT.md)). Novi gridMET fajl: sha256
   `7a51aadd46b894d9cd80835d7953107271b3182c776d7bb464d7abae826afac1`, manifest
   `013be9a1…`. RNG reset je riješen u TASK-023.

**Faze 1 i 2, autonomno (dopuna ADR-030 o autonomiji); faza 1 je izvedena, vidi vrh.** Agent smije sam
pokrenuti gate, zamrzavanje i jednu VALIDATION ocjenu, a fazu 2 samo ako gate prođe; merge
i faza 3 ostaju korisnikovi. Prompt s komandama, uslovima zaustavljanja i izvještajem:
[HANDOFF_STAGE_1_2](HANDOFF_STAGE_1_2.md). Fajl s vremenom (`7a51aadd…`) je u
`.local/backups/gridmet/` glavnog klona; kopira se u `.local/gridmet/` worktreea i provjerava hash.

Paralelni PR-ovi (TASK-021–024) ne mijenjaju zajedničke fajlove znanja (STATUS,
NEXT_SESSION, BACKLOG, log, agent ulazi); promjene opisuju u PR-u, a znanje se ažurira pri
merge-u.


## Najnovije — 2026-11-05: sintetički CA (ADR-028), grana `codex/synthetic-ca-training`

**Stanje.** policy-v1 je zaključan (hash u `reports/synthetic/policy-v1.sha256`; težine su prilog draft releasea
`synthetic-policy-v1`, lokalno u ignorisanom `.local/synthetic/locked/`; preuzimanje u
[HANDOFF](../HANDOFF.md)). Jednokratni test na stvarnim slučajevima je
izveden. Svaki novi checkpoint koji ide na stvarne slučajeve prvo se zaključava i
prijavljuje kao nova verzija, jer višestruki pokušaji na istih 119 slučajeva unose selekciju.

**Odluke za tim:**
- Da li je izjednačenje s heuristikom dovoljno za poster ili tražimo agenta koji je
  pobjeđuje. Kandidati za to: DAgger, duži fine-tuning, više sjemena, više jedinica i
  oracle baseline.
- Da li heuristike treba povezati s doktrinarnim izvorima (vidi "Porijeklo heuristika" u
  spec dokumentu).

**Tehnički nastavak:**
1. DAgger umjesto čiste imitacije, pa PPO s value pre-trainingom.
2. Ablacija doslovne "growth trend" nagrade, za objašnjenje u radu.
3. Vizualizacija epizoda je urađena: `scripts/synthetic_case_viewer.py` (lokalni viewer,
   politika naspram no-op na jednom stvarnom startu, s FEDS obodima).

**Komande** (iz roota worktreea, `PY=.local/simfire-venv/bin/python`, `PYTHONPATH=src`):
`scripts/evaluate_synthetic_policies.py`, `scripts/train_synthetic_ppo.py`,
`scripts/bc_warm_start.py`, `scripts/evaluate_real_cases.py --policy-locked`,
`scripts/diagnose_synthetic_calibration_gap.py --all --policy-locked`,
`scripts/synthetic_case_viewer.py`. Tačne argumente stvarnih runova daje [HANDOFF](../HANDOFF.md).


## Trenutno stanje — 2026-11-04

Grana `codex/overnight-steps-5-8` je izvedena iz `codex/fireline-simfire-benchmark`
(PR #3) i sadrži korake 5–8. Ništa nije spojeno u `main`. Lokalni ulazi, venv, modeli i
puni izvještaji su u ignorisanom `.local/` na Harunovom računaru; obnova je opisana u
[environment recordu](research/SIMFIRE_ENVIRONMENT.md).

1. **Gate (korak 5) je FAIL.** Dijagnoza i preregistrovana mreža su u ADR-023/024.
   Zamrznuti gate zapis gotovo ne širi vatru. Strogo pravilo je strukturno naklonjeno
   persistence referenci jer su mnogi FEDS požari stvarno zaustavljeni.
2. **Validation (korak 6)** je skoriran jednom po zapisu. Stress zapis (WAF .01 / ROS 1.0)
   prolazi strogo pravilo na 20 VALIDATION slučajeva, iako je pao na TRAIN-u.
3. **Intervencije i benchmark (korak 7, ADR-025)** postoje i testirani su.
4. **Prilagodba budžetu (korak 8, ADR-026/027)**: osnovni PPO pobjeđuje no-op, fine-tuning
   po budžetu ne daje mjerljivu korist, a downwind heuristika je jednako dobra ili bolja.
   Sve je simulatorski i eksploratorno.

## TASK-019 hipoteze — šta je provjereno (pozitivno i negativno)

| Hipoteza | Provjera | Rezultat |
|---|---|---|
| Nepotpune/izmijenjene FEDS arhive | MD5 svih 6 slojeva nakon prekinutog sekvencijalnog preuzimanja (exit 144 = namjerno ugašen i zamijenjen paralelnim) | sve OK, nema `.partial` |
| Vremensko poravnanje 0–48h | svih 119 epizoda: start maske = prvi FEDS timestamp, četiri razmaka od tačno 12h; runner provjerava start | OK |
| Konvencija vjetra | gridMET `th` je odakle puše; kod rotira +180° u SimFire smjer kuda; jedinični test; `vs` m/s → ft/min × WAF | OK; smjer nije uzrok (dijagnoza: deficit nije u smjeru nego u tome koji požar raste) |
| Isti grid za SimFire, persistence, elipsu | isti 256×256/180 m raster, isti `all_touched`, ista inicijalna maska u sve tri metode | OK |
| Nulti vjetar (sanity) | WAF 0 na 99 TRAIN (ADR-022): IoU .4768, i dalje raste u ~63% timepointa | rast bez vjetra postoji (Rothermel + nagib); potvrđuje pretjeran rast na statičnim požarima |
| Ulazi drugačiji od Belminovih | 99/99 LANDFIRE/maski + 9 gridMET identični hashovi; WAF .01 reproduciran tačno | nije uzrok |
| Prag paljenja / vijek ćelije | ROS × WAF mreža (ADR-023) | smanjuje lažni rast, ali do persistence se dolazi tek gašenjem skoro svega; FAIL |
| Trening samo na TRAIN | env odbija ne-TRAIN bez eksplicitnog `split`; trening skripta fiksira `split="train"` | OK |

Neprovjereno: vremenska zona FEDS `t` (pretpostavka UTC; TASK-027 je kasnije pokazao da nije UTC), finija vlaga goriva od `fm100`,
model zaustavljanja/gašenja. **Svi rezultati koraka 7–8 su "gate FAIL, nije mjerodavno"**
u smislu kalibracije; validation je preuzet i skoriran po korisnikovom odobrenju za
eksploratorni nastavak (ADR-024).

**Ako TASK-019 popravka učini da gate prođe:** prvo ponoviti gate na TRAIN-u, tek onda
validation, a eksploratorne rezultate koraka 6–8 označiti kao zastarjele (ADR-024 dopuna).

## Odluke za tim (ne donositi ih bez korisnika)

- Prihvatiti li stress scenarij kao radni simulator za predaju ili tražiti growth-aware
  gate, npr. ocjenu samo na požarima koji u FEDS-u rastu ili jednostavan model
  zaustavljanja/gašenja, prije bilo kakve tvrdnje o kalibraciji.
- Spojiti li ovu granu u PR #3 ili je držati kao zaseban draft PR.
- Šta od TASK-007 (prioritetna područja) i TASK-020 (gradnja linije kroz vrijeme, više
  linija po odluci) ulazi u obim prije postera.

## Najkorisniji tehnički nastavak

1. **Jači signal budžeta:** dozvoliti više jedinica po 12h odluci ili duži aktivni vijek
   ćelije, da veći budžet ima gdje djelovati. To je nova preregistracija (novi ADR), a ne
   izmjena ADR-026.
2. **Više seedova i koraka** ako tim želi uže intervale. Trenutni trošak je oko 8 odluka/s
   na 7 procesa.
3. **TASK-007:** težina prioritetnih ćelija u nagradi i ablacija ukupne naspram
   prioritetne štete.
4. **TASK-009:** grafikon `reports/real-fire-data/feds-simfire-policy-benchmark-v1.png` i
   ADR-027 tabela su polazište za poster. TEST 2024 otvoriti tek za završni obračun s
   unaprijed zaključanim politikama.

## Komande

Sve iz roota worktreea, uz `PYTHONPATH=src`, `SDL_VIDEODRIVER=dummy`, `OMP_NUM_THREADS=1`
i `MPLCONFIGDIR=.local/mpl-cache`:

```sh
scripts/run_budget_adaptation_experiment.sh            # trening po ADR-026 (SEEDS, BASE_STEPS, FT_STEPS)
OUT=.local/bench/NEW.json scripts/run_budget_adaptation_benchmark.sh
.local/simfire-venv/bin/python scripts/analyze_budget_adaptation.py .local/bench/NEW.json
.local/simfire-venv/bin/python scripts/plot_budget_benchmark.py .local/bench/NEW.json --out .local/bench/NEW.png
```

## Provjere prije predaje

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src .local/simfire-venv/bin/python -m unittest discover -s tests
PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW-ID
python3 scripts/validate_knowledge.py --strict
UV_CACHE_DIR=.local/uv-cache uv pip check --python .local/simfire-venv/bin/python
git diff --check
```

Ne otvarati TEST 2024. Ne pokretati plaćeni compute, push u tuđu granu ili merge bez
korisnikovog naloga. CFSDS/Cell2Fire rezultati ostaju historijski i odvojeni.
