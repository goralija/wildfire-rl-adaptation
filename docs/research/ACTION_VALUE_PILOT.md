---
type: Experiment Plan
title: Završni B1 pokušaj učenja vrijednosti smjera
---
# TASK-047 — plan prije koda i ishoda, 2026-11-28

Korisnik želi pokušati pokazati učinak blizak ili bolji od pravila prije mergea.
Nova `codex/action-value-pilot` polazi iz male integracije `9fbd0380`; PR #22 se ne
mijenja. Arhiva i negativni nalazi prethodnih PPO pokušaja ostaju sačuvani.

**Činjenica:** sparse PPO i prethodni offline modeli nisu pokazali pouzdanu
prednost. Raniji CA BC/PPO bio je drugi, native-unit MDP. **Pretpostavka:** zajednički
model vrijednosti smjera može bolje iskoristiti svaku simuliranu odluku nego jedan
uzorkovani PPO potez. Ovo je novi mali contextual-bandit selektor, nije PPO niti
dokaz adaptacije budžetu. Oba simulatora ostaju nepromijenjena.

**Provjerljivi cilj:** jedan unaprijed fiksiran ridge model po backendu, alpha=10,
fit-only standardizacija, jednaka težina svakog požara. Svaki legalni smjer dobija
oznaku završnog charged dobitka prema vlastitom no-opu, podijeljenu tim no-opom.
Model dijeli težine između osam smjerova: iz postojećeg terrain536 ulaza uzima
lokalni zapis kandidata, njegovu gorivnu/terrain okolinu, te projekcije vjetra i
fronta u smjer kandidata. Nema ID-a požara, budućeg vremena ili no-op otiska u ulazu.
Prvi potez je legalni argmax samo ako je predviđeni dobitak pozitivan; inače trajni
no-op. Nakon prve odluke uvijek preostaju tri no-op koraka. Nema naknadnog čekanja
pa gradnje; taj uži prostor eksplicitno važi i za reference.

Koristi se isti raniji TRAIN 45/16 razvojni split. Nula u vlastitom no-opu nema
definisan postotak: takvi požari ostaju u apsolutnim rezultatima, a iz fitting loss-a
i primarnog procentnog poređenja ispadaju joint-zero slučajevi u oba backend-a.
SimFire first-step oznake se provjeravaju iz stare potpune B1 tabele; CA dobija
45×9 fresh fitting putanja, uz sve 16×9 razvojne putanje. Svaka traje pune 48h.
Početna opažanja i maske moraju biti jednaki između backenda. Širenje CA koristi
zamrznutu repliku0; nema biranja spread/model seeda.

Reference su no-op, front64, downwind, svih osam fiksnih početnih smjerova i tačno
očekivanje uniformne legalne početne linije. Svi vide isti početni terrain536 zapis
i masku. Front64 je rekonstruisan iz njegovih centroida, uz provjeru prema v2 pravilu.
Na istim joint-positive razvojnim požarima „blizu“ znači **≥90% najveće srednje
uštede među tim referencama i donja opisna 95% granica razlike ≥−2 procentna poena**.
„Bolje“ zahtijeva donju granicu >0. Paired fire bootstrap 10.000/seed0 u svakom
uzorku ponovo bira najjaču referencu; seedovi ili akcije nisu dodatni požari.
Oba backenda prikazati i pojedinačno i kroz learner/reference omjer. Zajednički
near uspjeh traži prolaz oba. Svi16 se prijavljuju i u ha/pooled obračunu.

Brojke su eksploratorne: istih16 je projekt već više puta gledao. Ovaj prag ne
mijenja ranije FAIL kriterije niti daje nezavisan dokaz neinferiornosti ili fizičke
validacije. Stvarni VALIDATION/TEST2024/futureFEDS ostaju zatvoreni.

**Granica:** jedan model i jedno očitavanje, bez novih hyperparametara ili izbora
najboljeg kandidata nakon rezultata. Ako ne prođe, zatvoriti s negativnim nalazom.
Testovi za maske/no-op, weighting, fit/eval odvajanje i statistiku prethode kodu.
Najviše tri radnika plus koordinator, nice19 i numerical threads1. Maksimalno30min;
ako posao potraje, sačuvati PID/progres i javiti ETA pa završiti chat.

[Zamrznuti dizajn](../../configs/frozen/action-value-pilot-v1.json).
