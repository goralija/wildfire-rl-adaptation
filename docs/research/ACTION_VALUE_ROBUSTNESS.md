---
type: Experiment Plan
title: Šira provjera action-value nalaza
---
# TASK-049 — stabilnost postojećeg CA nalaza

## Plan prije novih ishoda — 2026-11-28, ADR-061

Korisnik traži širu provjeru poslije ADR-060. **Činjenica:** na razvojnih 14
joint-positive požara CA selektor daje 14,74%, najjača referenca 9,49%, ali
zamrznuti kriteriji zbog nesigurnosti ne prolaze. SimFire selektor ostaje slab.
**Pretpostavka:** povoljan CA prosjek može biti osjetljiv na fizičku repliku ili
izabrani razvojni split. Cilj je izmjeriti tu osjetljivost, bez novog kandidata.

1. **Primarno: isti zamrznuti CA model, tri širenja.** Na istih 16 razvojnih
   požara, CA replika 0 iz roditeljskog runa plus fresh replike 1 i 2. Prikuplja se
   no-op i svih osam legalnih početnih linija uz nepromijenjen simulator, B1/48h i
   tri preostala no-op koraka. Model i sva pravila biraju iz istog početnog
   terrain536 opažanja i maske; njihove odluke moraju biti jednake kroz replike.
   Postotak se računa unutar požara/replike, zatim prosjek replika unutar požara,
   pa prosjek požara. Požari bez pozitivnog no-op rasta u bilo kojoj od tri CA
   replike ili u SimFire-u izostaju samo iz primarnog procentnog poređenja.
   Svi ostaju u ha/pooled podacima; nula nema izmišljeni procentni dobitak.
   Ista dva opisna kriterija kao ADR-059: near ≥90% najjače od 12 referenci i
   donja bootstrap granica ≥−2pp; better donja granica >0. Bootstrap 10.000/seed0
   klasterira požare, ne replike, i ponovo maksimizira referencu u svakom uzorku.
2. **Sekundarno: svih 61 TRAIN požar, LOO.** Isti action-value algoritam,
   alpha10 i feature zapis; svaki požar se ocjenjuje modelom koji nije dobio ni
   njegovo opažanje za skaliranje ni njegove oznake za fitting. Fitting koristi
   pozitivne ostale požare u oba backend-a. Bez pretrage hyperparametara. Oba
   simulatora ocjenjuju isti joint-positive skup. Uz ranijih 12 pravila dodaje se
   pravilo odabrano samo na fitting požarima svakog folda. Čuvaju se svi foldovi,
   hashovi njihovih modela, njihove fitting liste i odluke.
   Prikazati procentne, ha/pooled i learner/reference omjere, te raspon efekta
   kad se iz rezultata izbaci svaki pojedinačni požar bez ponovnog fittinga.

LOO je nova razvojna analiza istog fiksnog algoritma; preklapajući fitting skupovi
nisu nezavisni eksperimenti, a bootstrap fiksnih OOF predikcija ne obuhvata svu
nesigurnost ponovnog učenja. Svih 61 su ranije istraživani TRAIN slučajevi.
Replike istog požara ne povećavaju broj nezavisnih požara. Nema potvrđujućeg
holdouta, PPO napretka, fizičke validacije ili dokaza adaptacije budžetu.

[Zamrznuti dizajn](../../configs/frozen/action-value-robustness-v1.json) veže roditeljski
plan, ishode i modele hashovima. Postojeći kriteriji i nalazi se ne prepisuju.
Testovi za odvajanje foldova, jednak ponder požara, nulte nazivnike i statistiku
prethode kodu. Max tri nice19 radnika plus koordinator, numerical threads1 i
limit30min. Procjena novih rollouta nekoliko minuta; dugi posao ide odvojeno uz ETA.
TEST2024, novi realni VALIDATION i future FEDS ostaju zatvoreni. Bez mergea.
