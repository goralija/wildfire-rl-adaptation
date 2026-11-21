---
type: Experiment Report
title: TASK-041 — SimFire/CA rast prema opaženom FEDS-u
sources:
  - resource: /configs/frozen/paired-observed-growth-v1.json
  - resource: /docs/research/CA_SIMFIRE_PAIRED.md
---
# Rast zamrznutih simulatora prema opaženom FEDS-u

Stanje2026-11-21: korisnik je odobrio nastavak predloženog TASK-041. Rad je na
`codex/ca-feds-growth-audit`, iz640a910e. [Plan](../../configs/frozen/paired-observed-growth-v1.json)
i ADR-045 prethode novom scoringu. Parametri, slučajevi i seedi se ne podešavaju.

**Pretpostavka:** velika razlika no-op rasta iz TASK-040 zaslužuje poređenje s istim
opaženim promjenama; manji rast i veći policy procenat sami ne znače bolji simulator.
FEDS je satelitski zapis uz nepoznate intervencije, ne potpuno opažen slobodni požar.

**Provjerljivi cilj:** isti16 TRAIN početaka, puna256mreža180m i48h; novi prostorni
rast izvan scar|front, apsolutna greška površine i no-growth slučajevi. Primarni CA0,
sva3seed-a zasebno i njihov sekundarni prosjek bez izbora najboljeg. Exact-time FEDS
na0/12/24/36/48h mora se poravnati s lokalno-solarnim UTC mapiranjem gridMET-a.

Ponavljaju se samo no-op putanje, najviše3radnika uz koordinaciju, nice19/jedna nit.
SF/CA0 cijele finalne maske moraju ponoviti arhivu; CA1/2 finalni brojevi moraju biti
isti. Future FEDS geometrije učitavaju se tek kad oba backend-a završe. Dvije postojeće
checksum-verifikovane godišnje TRAIN arhive, bez mrežnog preuzimanja i bez2023/2024.

Primarno: mean48h growth IoU na istim observed-positive potpunim slučajevima i mean
apsolutna greška novih ha na svim potpunim slučajevima. Sve16ulaznih stavki ostaju
vidljive; missing/invalid se ne pretvara u nulti rast. Puna vektorska pokrivenost mape,
ne-monotonost oboda i observed growth na nonfuel prijavljuju se zasebno. Sekundarno:
fully-covered subset, vremenska putanja i kumulativni opažajni envelope. Persistence i
postojeća downwind elipsa su reference. Nema naknadnog mijenjanja primarnog cilja.

Status: plan zamrznut prije koda/scoringa; nema rezultata ili tvrdnje fizičke validacije.
Native PPO faza B i TASK-039 ostaju otvoreni/odgođeni. Testovi, ponovljivost i naučne
granice bit će dopunjeni nakon izvršenja; TRAIN nalaz nije nezavisna finalna evaluacija.
