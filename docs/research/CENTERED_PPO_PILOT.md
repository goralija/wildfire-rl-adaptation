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

Plan je napisan prije implementacije. Trening još nije pokrenut.
