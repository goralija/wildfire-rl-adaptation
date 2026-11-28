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

## Pokretanje — 2026-11-28

Plan `eb96badb`, implementacija `1d600886`, deset numeričkih testova PASS prije
prvih novih ishoda. Tehnički pilot prva2fitting požara prošao24,40s: početna
opažanja/maske jednaki između backenda, CA no-op cijela putanja jednaka arhivi,
SimFire9početnih scoreova rekonstruisano iz punih maski; puna4odlučna horizonta.
Prvi pokušaj pokretanja zaustavljen je prije prikupljanja jer sandbox nije dozvolio
nice19; ponovljena ista komanda izvan sandboxa. Nema izmjene metode.

Prvi puni pokušaj v1 zaustavljen je prije fittinga: front64 rekonstrukcija pogrešno
je tražila pozitivan legacy burned kanal, koji ne uključuje aktivni front. Global
cumulative kanal ga uključuje. Prvo padajući11.test, zatim ispravka `dbcddb6d` i
61/61initial-only provjera referenci PASS. Kandidat, oznake i kriteriji ostaju isti;
v1zapisi nisu korišteni u konačnom v2runu. Pool gašenje greške je zapelo; ugašena su
samo tri vlastita idle radnika. `17ef653f` vraća ranije korišteni ProcessPoolExecutor
i eksplicitno zapisuje radničke greške. Oba commita prethode prvom fittingu/ocjeni.

Puna ponovljena komanda, novi output bez prepisivanja v1:

```sh
nice -n 19 .local/simfire-venv/bin/python scripts/run_action_value_pilot.py \
  --out .local/action-value-v2 --archive ../separate-clip-pilot
```

Lokalni `.local/action-value-v2/status.json`, `.local/launch-v2.json`, `guard.json` i
`fit-freeze.json` prenose stanje. Sirove maske i numeric NPZ modeli ostaju lokalno.
Guard veže plan, numerički kod i runtime; flock sprečava dva koordinatora,30min alarm
ograničava posao. Modeli se fituju jednom prije otvaranja razvojnih oznaka.
Aktivni koordinator PID12743 od10:20:50CET, `.local/run-v2.log`, procjena3–8min.

## Završeno — 2026-11-28, ADR-060

Puni v2 run završen je za 253,89 s (4,23 min). Nema aktivnog treninga. Dva
deterministička modela fitovana su na 39 joint-positive od 45 fitting požara;
šest zero slučajeva izostaje iz procentnog loss-a po planu. Modeli su zamrznuti
prije razvojne ocjene. Početna opažanja i maske jednaki su između backend-a na
svih 61 slučajeva. CA no-op svih pet stanja jednak je arhivi. Ukupno 1098
stored mask-score ishoda je provjereno; 16 izabranih SimFire putanja dodatno
prolazi fresh native replay. Svih 16 razvojnih požara ostaje u ha/pooled rezultatu,
a primarni procenti koriste istih 14 joint-positive slučajeva.

| Metoda | SimFire saved% | CA saved% |
| --- | ---: | ---: |
| Novi action-value selektor | 2,40 | **14,74** |
| Najjača od 12 zamrznutih referenci | 11,29 (front64) | 9,49 (fiksni smjer 7) |
| Tačno uniformna legalna linija | 5,23 | 6,20 |
| Selektor / najjača referenca | 21,3% | **155,4%** |

**Pozitivan CA razvojni signal:** +5,25 pp ili 55,4% veća srednja procentna ušteda
od najjače reference. CA bira šest različitih smjerova i dva puta no-op. Na 14
primarnih slučajeva prema fixed7 ima 6 boljih, 3 lošija i 5 istih ishoda.
Prosjek svih 16 u ha: 142,76 CA / 139,73 SimFire. Apsolutni ha između simulatora
nisu zajednički dokaz prednosti zbog različitog no-op širenja.

**Zaključani kriterij ipak nije prošao.** Opisni bootstrap raspon learner−maxreference
je CA [−10,42; +9,96] pp, SimFire [−26,78; −2,07] pp. Maksimum među referencama
ponovo se bira u svakom bootstrap uzorku. To nije interval prema samo fixed7
izabranom nakon ocjene. CA point-estimate nadmašuje referencu, ali donja granica
ne zadovoljava −2 pp. Near=false/better=false za oba backenda. Raniji PPO negativni
nalazi se ne mijenjaju. Ovo je povoljan prosjek na CA razvojnom uzorku, bez
potvrđene neinferiornosti ili RL prednosti.

[Kompaktan nalaz sa svim 32 per-case redovima](../../reports/real-fire-data/action-value-summary-v1.json)
čuva kriterije, referentne prosjeke, hashove i ograničenja. Zasebni read-only
[auditor](../../scripts/audit_action_value_pilot.py) potvrđuje 1098 mask-score ishoda,
fit-only refit oba modela, sve 32 razvojne odluke i zaseban bootstrap obračun.
337 pinned/0 skip, 322 modern/3 skip, 259 core/35 skip, 15 knowledge, CLI i strict
checker PASS. To su runtime provjere, ne fizička validacija. NPZ modeli i maske
ostaju u `.local`.

**Granica faze je primijenjena:** nema dodatnog kandidata ili novog treninga.
PR22 je ostao neizmijenjen; ovaj eksperiment je na `codex/action-value-pilot`.
Za review pokazati pozitivan CA prosjek zajedno s nesigurnošću i slabim SimFire
rezultatom. Šira provjera CA nalaza i native control/budget ugovor su novi planovi;
nisu automatski odobren novi holdout, merge ili dalja pretraga parametara.
