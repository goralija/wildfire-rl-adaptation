---
type: Experiment Plan
title: Odvojeni actor/critic clipping i završetak faze — TASK-046
---
# Posljednji optimizer test ove faze

## Plan prije implementacije i rezultata — ADR-057, 2026-11-23

Korisnik odobrava nastavak TASK-046 i traži jasan završetak faze, merge i napredak.
Grana `codex/separate-clip-pilot` polazi iz `b00e55e2`.
[Zamrznuti plan](../../configs/frozen/separate-clip-pilot-v1.json) prethodi implementaciji.

**Činjenice:** originalni PPO nije pokazao pouzdanu prednost; centriranje samo po
sebi nije prošlo unaprijed zadate kriterije. TASK-044 je na prvom updateu izmjerio
coupling globalnog gradient clippinga actora i critica. To nije dokaz da zasebno
ograničavanje daje bolju politiku nakon treninga.

**Hipoteza:** zaseban norm bound0,5 za actor i critic može popraviti izbor akcija
u istom512step budžetu. **Provjerljivi cilj:** promijeniti samo grupisanje gradient
clippinga i porediti svih šest novih modela s originalnim512 checkpointovima.

Isti45 TRAIN fitting /16 ranije istraženih razvojnih požara, seedovi17/29/43,
isti raspored128 punih epizoda, početne težine, MLP64×64, terrain536, B1 i4×12h.
Originalna charged-increment nagrada, isti combined PPO loss, isti jedan Adam,
learning rate, eps, dva PPO epoha i targetKL. Nema centriranja ili warm-starta.
Svaki actor/critic skup ima maxnorm0,5; skupovi moraju biti disjunktni i obuhvatiti
sve trainable parametre. Neočekivan ili dijeljeni trainable parametar zaustavlja rad.

Izvedeni opt-in MaskablePPO čuva statički upstream2.7.1 train kod, uz zamjenu samo
clip poziva. Nema globalnog monkeypatcha ili izmjene instalirane biblioteke.
Prvo testovi norm bounds/grupa i exact global-control updatea prema upstreamu;
zatim šest fresh16step rollouta identičnih TASK-044 raw snapshotu i nezavisni
separate-clip prvi Adam update. Ove disposable težine se ne ocjenjuju kao politike.
Raniji whole-physics preflight se pošteno ponovo koristi uz hashove istog koda.

Trening je6×512, checkpointovi0/512, svi modeli bez izbora najboljeg. Prvih16
actual training koraka mora biti potpuno isto kao raw TASK-044 buffer prije updatea.
Svaki stvarni minibatch ostavlja before/after norm receipt za obje grupe. Izlazni
modeli se native provjeravaju na svih16 po cijeloj burned/line maski i scoreu.

Primarno: separate512−original512 mean charged saved% na istih14 joint-positive;
tri seeda se prvo prosječe unutar požara, pa10k paired fire bootstrapseed0. Drugi
unaprijed zadati referent je tačno uniformna prva legalna linija. Donje95%granice
oba poređenja iznad0 daju samo opisni TRAIN continuation signal. Originalni front,
downwind, randomseed0, fit-only sektor, initial0 i centrirani512 ostaju vidljivi.
Svi seedovi, raw/charged ha, pooled i undefined zero-noop slučajevi ostaju u izvještaju.

## Kada završavamo fazu i pripremamo merge

1. **TASK-046 je posljednja optimizer ablation ove faze.** Završiti šest fiksnih
   treninga i audit. Nema automatskog dodatnog treninga, novih seedova ili nove
   optimizer izmjene poslije uvida u rezultate.
2. **TASK-047 je završetak ove faze:** jedan zajednički zaključak o cijelom nizu
   SimFire/CA popravaka i poređenja, pregled poznatih ograničenja i integracijski
   pregled prema aktuelnom `main`, svi testovi/CI i konkretan paket za review/merge.
   Na početku je `origin/main=f96f744f`, predak baze;77 commitova/220 fajlova čeka
   integraciju. To zahtijeva pregled cijelog niza, a ne samo posljednjeg reward testa.
3. Faza se zatvara i s negativnim nalazom. Uslov za integraciju je ispravan,
   reproduktivan kod i pošteno dokumentovani nalazi. Pozitivan RL rezultat nije
   uslov da spojimo istraživački rad; runtime PASS nije dokaz RL/fizičke prednosti.
4. Ako ima pozitivan signal, kandidat se zamrzava s ograničenjima. Ako ga nema,
   originalni baseline ostaje i ovu optimizer pretragu završavamo. U oba slučaja
   rezultat ne otvara automatski stvarni VALIDATION/TEST ili novi veći trening.
5. **Sljedeća faza, predloženi TASK-048:** unaprijed definisati CA kontrolni problem
   koji traži više od ove B1 prve linije, s eksplicitnim informacijama, akcijama,
   budžetima, sigurnošću i referentima; native unit parity prije novog učenja.
   To je zaseban dizajn, ne dodatna izmjena trenutnog benchmarka.

Konkretan integration/PR review dolazi poslije rezultata i TASK-047, prije stvarnog
mergea. Ova odluka završava ograničenu fazu istraživanja; ne tvrdi da smo provjerili
sve moguće greške simulatora ili fizički validirali CA.

## Izvršavanje i status

Plan je napisan prije koda i mjerenja. Trening još nije pokrenut.
Procjena20–30 minuta nakon testova/preflighta. Najviše3 radnika+koordinator,
nice19/jedna numerička nit. Korisnikova background preferenca ostaje: potvrditi
napredak, zapisati PID/status/ETA i završiti chat dok računanje radi. Checkpoint
je numeric inference-only NPZ; partial job nije Adam resume. Veliki podaci i težine
ostaju lokalni. Stvarni holdouti/futureFEDS/plaćeni compute ostaju zatvoreni.


### Implementacija i testna granica verzija

Plan208b95d5 prije koda53fa50e8.9novih testova prolazi u pinovanom runtimeu.
Prvi puni moderni suite je otkrio da je source-equivalence test pogrešno zahtijevao
identičnost i s novijim upstreamom2.9.2. Experiment runtime ostaje2.7.1; njegov
kanonski upstreamAST SHA9139494d442a0df0ccdb3e86db439264001787898c347cc6848d62ed23a75895
je zasebno zamrznut, a test poredi vraćeni clip izraz s tim fingerprintom. U2.7.1
se dodatno poredi stvarni upstreamAST. Moderni tensor/update testovi i dalje rade,
ali ne tvrde da je kopirani train generalna zamjena za2.9.2. Prazni Python3.12
ASTtype_params se normalizuju; semantička train struktura ostaje stroga. Nema
promjene loss/gradient pravila, mjernog plana ili frozen roditeljskih fajlova.
