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

## Rezultat — 2026-11-28, ADR-062

Plan `6edb724c` i numerički kod `e8ac6763` prethode novim ishodima. Sedam novih
testova i svih 18 action-value testova prolaze. Tehnički pilot Goldstone r1/r2
prošao je za 8,08 s; puni posao trajao je 138,93 s (2,32 min), tri nice19 radnika.
Prikupljene su sve 32 nove realizacije; oba zamrznuta roditeljska modela ostala
su byte-identična. Početna opažanja, maske i akcije CA modela ne mijenjaju se s
realizacijom. Svaki novi no-op svih pet stanja jednak je arhivi za svoju repliku.

| Provjera | Selektor saved% | Najjača referenca saved% | Selektor / referenca |
| --- | ---: | ---: | ---: |
| Zamrznuti CA, 14 požara × 3 širenja | 10,76 | 8,70 | 123,8% |
| CA leave-one-fire-out, 53 pozitivna od 61 | 14,15 | 11,09 | 127,6% |
| SimFire leave-one-fire-out, isti 53 | 2,21 | 7,30 | 30,3% |

Primarno su i dalje 14 požara, ne 42 nezavisna slučaja. Prvo se računa procenat
svake realizacije, zatim prosjek unutar požara. Svi 16 ostaju u apsolutnim rezultatima.
Najjača fiksna CA referenca poslije prosječenja širenja je smjer1; nije prosjek
najjačih različitih pravila pojedinačnih širenja.

| CA realizacija | Zamrznuti selektor | Najjača referenca |
| --- | ---: | ---: |
| 0, prethodno ocijenjena | 14,74% | 9,49% |
| 1, nova | 5,24% | 12,43% |
| 2, nova | 12,32% | 7,62% |

**Pozitivan prosjek opstaje, ali prednost nije stabilna kroz širenja.** Realizacija1
je znatno slabija od najbolje reference. Opisni raspon prema ponovo izabranoj
max-reference je na zajedničkom prosjeku [−4,58; +5,26] pp. CA LOO daje
[−2,56; +7,58] pp; SimFire LOO [−11,68; −1,28] pp. Zaključani near/better kriteriji
i dalje su false; granica −2 pp nije prilagođena rezultatu.

Pri izbacivanju bilo kojeg pojedinačnog požara iz ocjene bez refita, CA prosječna
prednost ostaje pozitivna: frozen [0,37; 3,21] pp, LOO [1,66; 4,22] pp.
To pokazuje da pozitivan prosjek ne zavisi samo od jednog slučaja; ne uklanja
razvojnu selekciju, nesigurnost ili negativan rezultat na širenju1.

LOO fituje 122 modela istog algoritma. Požar je isključen iz svog modela i
skaliranja, a referenca se bira samo iz fitting požara. Najbolji globalni
fiksni referent je ujedno fitting-only izbor: CA fixed1, SF front64.
53 zajednička pozitivna su za procente; svih 61 ostaje u ha/pooled mjerama.
Nezavisni read-only [auditor](../../scripts/audit_action_value_robustness.py)
provjerava 1098 roditeljskih i 288 novih mask-score ishoda, svih 48 zamrznutih
odluka, fitting isključenja i ponovno fitovanje 122 modela, te zasebnu statistiku.
[Kompaktan nalaz sa svim slučajevima](../../reports/real-fire-data/action-value-robustness-v1.json)
čuva hashove, sve replike i foldove; pune maske i težine ostaju lokalno.

Ovo podržava dalju CA istragu, uz preliminarnu učenu korist na B1 problemu.
Nema potvrđene prednosti, novog PPO rezultata, fizičke validacije ili budžetske
adaptacije. Šira provjera je završena bez pretrage modela. PR22 i main nisu mijenjani;
merge nije urađen. Dalji trening ili native control/budget faza traže zaseban plan.

**Završne provjere:** 344 pinned (0 skip), 329 modern (3 skip), 266 core (35 skip),
15 knowledge, synthetic CLI i strict checker svih85Markdown fajlova PASS.
Nove težine i maske nisu commitovane. Ponovljiva read-only provjera:

```sh
nice -n 19 .local/simfire-venv/bin/python scripts/audit_action_value_robustness.py \
  --out .local/action-value-robustness-v1 --receipt .local/robustness-audit-NEW.json
```

Legacy shutdown napomena: svih344 testova ispisalo je `OK` (397,58s), ali Python3.9
zatim nije završio proces. Lokalni macOS sample pokazuje glavni thread u
`Py_FinalizeEx / _PyImport_Cleanup / collect`; to ne utvrđuje uzrok ili krivicu
određene biblioteke. Vlastiti PID16659 zaustavljen je SIGTERM-om, exit143, nakon
sačuvanog loga/sample-a. To nije uredan exit0 legacy suitea. Modern/core suite,
CLI, knowledge i eksperimentalni runner/auditor završili su uredno. Nema aktivnog
treninga ili test procesa iz ove provjere. Nisu mijenjani globalni runtime ili
simulator da bi se prikrio zastoj; nalaz je operativno ograničenje ove sesije.
