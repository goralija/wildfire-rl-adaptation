---
type: Experiment Plan
title: Centrirana nagrada — TASK-045
---
# Centrirana nagrada: kontrolisani PPO pilot

## Plan prije implementacije i rezultata — ADR-055, 2026-11-23

Korisnik nastavlja predloženi TASK-045 i izričito dopušta pozadinski trening uz
završetak sesije i procjenu povratka; to važi i za naredne zadatke. Grana
`codex/centered-ppo-pilot` polazi iz `c2e53f4c`.
[Zamrznuti plan](../../configs/frozen/centered-ppo-pilot-v1.json) prethodi kodu i mjerenjima.

**Činjenica:** TASK-044 je izmjerio početni case-scale/global-clipping mehanizam,
bez dokaza da nova nagrada daje bolju politiku. Centriranje je poboljšalo5/6prvih
koraka, uz CA43kontraprimjer. **Hipoteza:** no-op centriranje može poboljšati učenje
u istom step budžetu. **Provjerljivi cilj:** promijeniti samo reward, a zatim porediti
svih šest novih512step modela sa svih šest sačuvanih originalnih512modela.

Isti45TRAIN fitting/16ranije istraženih development evaluation,3model seeda17/29/43,
isti TASK043hash raspored128epizoda po modelu. Isti v2/terrain536,MLP64×64,PPO parametri,
globalclip,B1,9akcija i4×12h. Nova politika kreće iz istih početnih težina, bez warm-starta.
Sačuvati0/512, bez izbora najboljeg. CAspread0fiksiran; model seedovi nisu novi požari.

Opt-in reward v2 je `(noop_increment − charged_increment)/100 − .01*invalid`.
Vlastiti5state no-op služi samo nagradi. Poslije pune4odluke povrat je charged saved
cells/100 umanjen za invalid kazne; pri gamma=lambda1 poredak poteza se ne mijenja.
Obs/maske/physics i stari reward/checkpointovi se ne mijenjaju. No-op uvijek legalan,
budget0ne završava epizodu, prethodna šteta ostaje u kumulativnoj maski.

Prvo unit testovi reward/shape/binary/prior/budget/masks i numeric save/reload. Zatim
32paired native putanje (4fiksna slučaja×2backend-a×4sekvence), po dvije kopije
raw/centered: svi opažaji,maske,budžeti,akcije i svaka burned/line maska identični,
reward offset matematički tačan. Sve61reference i stari512receipts provjereni.
Prvih16novih training koraka mora imati iste obs/actions/masks/values/logprobs kao
TASK-044prvi rollout; nagrada/returns porede se s centered tensor probom uz float32toleranciju.

Završni novi512modeli se ocjenjuju na svih16i native provjeravaju po cijeloj finalnoj
burned/line maski i charged scoreu prema staroj B1tabeli. Primarno je centered-minus-
original512 na istih14joint-positive, uz model-seed prosjek unutar požara pa opisni
10kpaired bootstrapseed0. Druga granica nastavka je centered-minus-tačnom-uniformnom
referentu. Obje donje95%granice iznad0 daju samo opisni continuation signal; ne fizičku
validaciju ili pobjedu nad svim heuristikama. Front/fitting-onlysector/seed0random,
owninitial0,ha/pooled/zero-noop i svi model seedovi ostaju vidljivi.

Nema promjene clippinga/arhitekture/optimizera ili više koraka. Stvarni VALIDATION/TEST,
futureFEDS, plaćeni compute i merge zatvoreni. Predviđeno15–25min, najviše3radnika+
koordinator,nice19/jedna nit. Poslije potvrđenog starta korisnik dobija vrijeme povratka.
NPZ je inference-only: završeni poslovi se usvajaju uz guard/hash, nepotpuni zahtijevaju
dokumentovan novi pokušaj. Stari TASK-043/044rezultati ostaju historijski nepromijenjeni.

## Status

Plan je zasebno commitovan kao `0d8d3821`, prije implementacije. Opt-in adapter i
runner su implementirani; stari numerički source ostaje nepromijenjen. Trening je pokrenut nakon preflighta; vidi start i nastavak ispod. Jedanaest novih testova obuhvata reward invariance, reference,
statistiku, PPO/NPZ, prekid prije updatea i odbijanje partial/duplicate poslova.
Novi moduli imaju zaseban reward contract, a prva16step provjera čuva tačne ulaze
i lokalnu float32toleranciju `atol=2e-5,rtol=1e-6` samo za izvedene reward tenzore.

Kod: [adapter/statistika](../../src/wildfire_rl/centered_control.py),
[runner](../../scripts/run_centered_ppo_pilot.py), [contract testovi](../../tests/test_centered_control.py),
[RL/stop testovi](../../tests/test_centered_control_rl.py).

Pozadinski posao koristi atomic exclusive coordinator lock, odvojene PID/status/
error/stop/done zapise i numeričke checkpointove0/512. Globalni stop se zapisuje prije
čekanja poola; nedovršen job se ne usvaja kao optimizer resume. Završeni job ima
hash svakog fajla prije usvajanja. Fajlovi s težinama i mapama ostaju u `.local`.


## Preflight i pozadinski start — 2026-11-23

**Provjereno:**434 pinned /0skip,419 modern /4skip,324 core /51skip,15 knowledge,
CLI i strict94.11 novih testova uključuje namjerni pogrešan prvi rollout i prekid
prije prvog optimizer updatea, globalni stop, partial job i dupli koordinator.
[Verifikacija](../../reports/real-fire-data/centered-ppo-verification-v1.json).
Kod `273cfb62` je pushan i [sva četiri CI posla](https://github.com/goralija/wildfire-rl-adaptation/actions/runs/45258731879)
prolaze, prije novog training nalaza.

[Native preflight](../../reports/real-fire-data/centered-ppo-preflight-v1.json):
32 para (64 epizode), četiri fiksna požara×dva simulatora×četiri sekvence,39,90s.
Jednaki svi opažaji i finalni opažaj, maske, akcije, budžeti, fizički score i svaka
kumulativna maska požara/linije. Per-step offset i finalna saved-return jednakost
prolaze;122 referentne putanje i originalni512checkpoint receipts provjereni.
Ovo je tehničko očuvanje ugovora, ne rezultat novog učenja.

[Launch zapis](../../reports/real-fire-data/centered-ppo-launch-v1.json):21:23 CET,
koordinator PID51639, PPID1, nice19, tri radnika, jedna nit. Worktree
`.worktrees/centered-ppo-pilot`, izlaz `.local/centered-ppo-v1`, stdout
`.local/centered-training.log`. Ne pokretati istu komandu dok postoji živ koordinator.

Pri nastavku prvo pregledati lokalni root i job status, lock/PID, first-rollout,
stop/error i done receipts. Ako je kompletno, nezavisno provjeriti šest modela,
3072 trening koraka /768 epizoda, svih96 native final putanja, isti original512,
prve16 korake i bootstrap po požaru. Zatim objaviti sve rezultate i ograničenja,
provesti prenosiv lokalni bundle/restore i zapisati ADR-056. Ako je nedovršeno,
prvo utvrditi razlog; nema optimizer nastavka iz inference-only NPZ checkpointa.

**Snapshot pri predaji:** tri SimFire radnika već napreduju; prvi16 parity PASS
za sva tri (obs/actions/masks/values/logprobs tačno; najveći izmjereni reward-derived
float32 error1,26e-6). CA17/29/43 su u redu čekanja. PPID1/nice19 provjereni iz `ps`,
bez stop/error zapisa. Ovo je snapshot starta; lokalni status ima prednost.
Korisniku procijenjen povratak za oko30min, bez držanja chata otvorenim.
