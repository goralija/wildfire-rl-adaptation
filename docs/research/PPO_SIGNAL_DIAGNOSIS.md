---
type: Experiment Plan
title: PPO signal i reference — TASK-044
---
# PPO signal i reference

## Plan prije mjerenja — ADR-053, 2026-11-23

Korisnik nastavlja predloženi TASK-044. Nova grana `codex/ppo-signal-diagnosis`
polazi iz `c160fd0e`. [Zamrznuti plan](../../configs/frozen/ppo-signal-diagnosis-v1.json)
prethodi implementaciji i novim brojkama; TASK-043 nalazi ostaju nepromijenjeni.

**Činjenica:** stari pilot nije prošao learning kriterij. Soft distribucije su skoro
uniformne, a greedy izbor često isti. Fixed random seed0 daje sektor7 na svih16.
Pinovani MaskablePPO2.7.1 računa MSE value loss i globalno ograničava normu svih
policy parametara, uključujući actor/critic; Adam policy default eps je1e-5.
To je provjereno u instaliranom izvornom kodu, ne pretpostavljeno iz naziva algoritma.
**Hipoteza:** veličina reward/value signala i zajedničko ograničavanje gradijenata
mogu otežavati actor update. Ovo još nije nalaz ili dokaz uzroka cijelog treninga.
**Provjerljivi cilj:** izmjeriti reference, promjenu parametara i početni gradient
mehanizam pod istim scenarijima, bez novog punog treninga ili mijenjanja starih skorova.

1. Tačan uniformni izbor među legalnim linijama na prvoj odluci. Svi9traženi sektori
   (uključujući no-op) na45fitting požara: SF iz arhive, CA novi native replay. Isti
   front/nonfuel mask i budžet. Jedan fiksni sektor bira se samo po mean charged saved
   ćelijama na45fitting, s najmanjim ID-em pri izjednačenju. Tek zatim ocjena na16.
   Prijaviti i sve sektore, sve nazive/denominatore, mean%/ha/pooled i zero-noop.
2. Svih18postojećih numeric checkpointova na početnim opažajima svih61: actor/critic
   pomaci parametara, entropy/greedy/KL, Tanh saturation i feature rasponi. Fit/eval odvojeni.
3. Ponoviti prvi rollout16koraka/4epizode za svaki od3seeda i oba backend-a, bez
   `train` poziva. Mora odgovarati prvih16originalnih training redova i početnim
   težinama. Tada na istom minibatchu4jednokratne, odbačene Adam probe: originalna/
   centrirana nagrada × zajedničko/odvojeno actor-critic ograničavanje. Nove težine
   se ne čuvaju kao politike i ne mjere na požarima.

Centriranje dodaje vremenski poravnat no-op prirast/100 nagradi. Uz gamma=lambda1
i puni4step horizont ukupni pomak je isti no-op damage/100 za svaki potez tog požara,
pa ne mijenja poredak konačnih charged troškova. Ovo se prvo testira i računa na
istim putanjama; production reward/physics/maske/checkpointovi ostaju isti.

Unit test mora potvrditi ručni PPO loss/gradijent/Adam prvi korak prema instaliranoj
implementaciji. Probe mjere aktivne naspram prisilnih odluka, skalu returna/advantagea,
norme prije/poslije clippinga, Adam eps i stvarni pomak actor/critic parametara.
Originalni optimizer momentum nije sačuvan; nalaz važi za početni korak, ne cijeli trening.

Procjena native dijela5–15min, najviše3radnika+koordinator,nice19/jedna nit. Nema
novog punog treninga, tuninga, stvarnog VALIDATION/TEST, budućeg FEDS-a ili mergea.
Ni povoljnija jednokratna proba nije dokaz da bi novi puni trening učio bolje.

## Status

Plan je zamrznut prije implementacije. Dijagnostički poslovi još nisu pokrenuti.
