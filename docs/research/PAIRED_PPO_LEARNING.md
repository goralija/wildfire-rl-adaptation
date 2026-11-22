---
type: Experiment Plan
title: Upareni PPO TRAIN learning pilot — TASK-043
---
# Upareni PPO learning pilot

## Plan prije koda i rezultata — 2026-11-22, ADR-051

Korisnik traži nastavak i opsežno testiranje, izričito dopušta duži lokalni trening
i završetak sesije dok on radi. Grana `codex/paired-ppo-learning` polazi iz
`720c914b`. [Zamrznuti plan](../../configs/frozen/paired-ppo-learning-v1.json) je kanonski.

**Činjenice:** TASK-040 B.1 daje zajednički encoder/PPO/charged reward ugovor i
tehnički PASS. Svih 61 kompatibilnih TRAIN požara već je korišteno u razvoju projekta.
**Pretpostavka:** isti PPO postupak može naučiti prenosivu kontrolu u ovom interfejsu.
**Provjerljivi cilj:** odvojiti pomak u učenju od razlike u razmjeru simulatora i od
blizine istim heuristikama. Nalaz ostaje eksploratorno razvojno poređenje.

Prvobitnih 16 hash-odabranih TASK-040 požara služi razvojnoj evaluaciji; drugih 45
uči model. Skupovi su disjunktni za nove težine, identični u oba backend-a. Ovo nije
nezavisan naučni holdout. Stvarni VALIDATION/TEST i budući FEDS ostaju zatvoreni.

Tri model seeda (17/29/43), po 2.048 koraka u svakom backend-u, isti v2/terrain536,
MLP64×64 i svi PPO parametri iz B.1. Isti seed određuje isti hash-raspored 512 epizoda
na 45 fitting slučajeva. Čuvaju se svi modeli na 0/512/2048 koraka; završni 2048 je
primaran, bez izbora najboljeg. Fizika, B=1, četiri odluke/48h i reward nisu promijenjeni.

Prije treninga: provjera ulaza svih 61, početnih opažaja/maski svih 16 i pune 33
native putanje na prva dva evaluacijska slučaja u oba backend-a. Finalni PPO zatim
ide native na svih 16 po seedu/backend-u i mora odgovarati staroj B=1 tabeli po
cijelim finalnim burned/line maskama i scoreu. Ostali checkpointovi i heuristike
mogu koristiti tačan lookup: do prve linije opažaj je no-op putanja; poslije nje
ostaju samo no-op potezi. Tabela ne daje buduće informacije politici ili treningu.

Primarno: prosjek procenta spašenih charged ćelija na istim slučajevima s pozitivnim
no-op rastom u oba backend-a. Sva tri model seeda prvo se prosječe unutar požara,
zatim opisni paired bootstrap po požaru, 10.000 uzoraka/seed0. Nema uvećavanja N
brojanjem model seedova kao novih požara. Prijaviti i sve seedove zasebno.

Uz to: charged/raw hektari, pooled procenat i nulti no-op slučajevi, pomak prema
vlastitom početnom modelu te razlika prema istim heuristikama. `advancing_front64`
je unaprijed fiksni referent; svi noop/random/downwind/front rezultati ostaju vidljivi.
Ključan je i CA−SF pomak u PPO-minus-heuristic razlici, ne samo veći CA procenat.
Nulti nazivnik ostaje undefined. Nema naknadnog odabira najbolje heuristike/modela.

Pozitivan opisni signal zahtijeva i final-minus-initial i final-minus-fixed-front
donju granicu opisnog intervala iznad nule u tom backend-u. To nije fizička validacija,
nezavisan dokaz RL prednosti ili automatska odluka o prelasku na CA.

Procjena je 45–75 minuta, najviše tri radnika i jedan koordinator, nice19 i jedna
numerička nit. Kod i testovi završavaju prije starta. Background proces ima logove,
status/greške, atomic receipts i sačuvane checkpointove. Završeni poslovi se mogu
usvojiti samo uz iste hashove; prekinut posao kreće od nule jer NPZ nije optimizer
resume. Nema tihog skraćivanja, produžavanja ili podešavanja po rezultatu.

## Status

Plan d586c1bc prethodi implementaciji13a234ba. Prošlo408pinned/0skip,393modern/4skip,
310core/48skip,15knowledge,CLI/strict92. Preflight102,47s:61input receipt,122guarded
no-op putanje,16initial v2/mask parity,132native full-tree putanje identične arhivi.
[Preflight dokaz](../../reports/real-fire-data/paired-ppo-preflight-v1.json),
[verifikacija](../../reports/real-fire-data/paired-ppo-verification-v1.json).

Trening je pokrenut u nezavisnoj background sesiji, koordinator PID37835,
nice19/3radnika/jedna nit. [Launch receipt](../../reports/real-fire-data/paired-ppo-launch-v1.json).
Rezultati još nisu kompletni. Lokalni status je kanonski za trenutno stanje. Native
resursi/mobilne jedinice ostaju otvoreni dio TASK-040 B; TASK-039 odgođen.


## Operativni nastavak

Iz task worktreea, pinovanim runtimeom, izabrati nov izlazni direktorij:

```sh
nice -n 19 .local/simfire-venv/bin/python scripts/run_paired_ppo_learning.py preflight --out .local/paired-ppo-v1
# Samo nakon preflight PASS; run ima najviše tri radnika i jedan koordinator.
nice -n 19 .local/simfire-venv/bin/python scripts/run_paired_ppo_learning.py run --out .local/paired-ppo-v1
```

Za background se isti `run` pokreće u nezavisnoj sesiji s preusmjerenim stdout/stderr.
`.local/paired-ppo-v1/status.json` prati cijeli run, `job-*/status.json` fazu i broj
koraka, `job-*/done.json` završetak s hashovima, `error.json`/`stop.json` grešku,
`coordinator.lock` PID aktivnog koordinatora. Ne pokretati drugi proces dok prethodni
postoji. Atomic completion se usvaja samo uz iste guardove i sve file hashove.

Poslije završetka: pročitati `analysis.json`, nezavisno prebrojati svih6×512epizoda,
288policy skorova i96native finalnih putanja; provjeriti cijele maske/score/returns,
checkpoint hashove i početne težine po seedu. Prijaviti0/512/2048 i sve seedove, iste
heuristike, oba razmjera i opisne intervale. Zatim figures, lokalni bundle/restore,
finalni testovi, STATUS/NEXT_SESSION/ADR/experiment log i push. Ne mijenjati numerički
source dok run radi; naknadni bug zahtijeva dokumentovan novi pokušaj.
