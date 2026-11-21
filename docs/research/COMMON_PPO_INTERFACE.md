---
type: Experiment Plan
title: Zajednički PPO ugovor — TASK-040 B.1
---
# Zajednički PPO ugovor

## Plan prije implementacije i ishoda — 2026-11-22, ADR-049

Korisnikovo „hajde nastavi“ nastavlja predloženi TASK-040 B.1 iz ADR-048.
Rad je u `codex/common-ppo-interface`, iz `45d41fcf`; nema mergea ili dužeg treninga.
[Zamrznuti plan](../../configs/frozen/common-ppo-smoke-v1.json) određuje tehnički prihvat.

**Činjenica:** postojeći SimFire i CA bridge daju raw nagradu, a TASK-040 evaluacija
računa charged štetu. Stari native CA urban/unit PPO ima drugačiji MDP.
**Pretpostavka:** isti mali encoder i PPO mogu koristiti oba common-line backend-a.
**Provjerljivi cilj:** isti ulaz536, Discrete9, maske, B=1 i4×12h, te povrat jednak
negativnoj finalnoj charged šteti/100 umanjen za eksplicitne invalid kazne.

Novi opt-in wrapper koristi postojeći v2/terrain536 zapis i ne mijenja fiziku ili
historijski raw reward. Privatni no-op otisak vlastitog simulatora služi samo reward
knjigovodstvu, bez FEDS budućnosti ili njegove dostupnosti politici/maski. Prethodno
izgorjelo ostaje izgorjelo; union sprečava dvostruko brojanje. No-op ostaje legalan,
epizoda traje četiri odluke i poslije utrošenog budžeta.

Prvo testovi štete/nagrade/maski/budžeta, zatim native provjere na prva tri ranije
registrovana TASK-040 TRAIN slučaja: Goldstone, Weston Pass, Pine Lodge. Novi no-op
whole-mask mora odgovarati TASK-042 arhivi; i CA se provjerava u istom pinovanom
runtimeu kao SimFire. Početni opažaji/feature-i/maske moraju biti identični.

Tek zatim četiri kratka treninga: dva backend-a × seed17/29 ×64 koraka, isti MLP64×64,
PPO parametri i ciklični raspored16 epizoda (6/5/5). Nema izbora najboljeg modela ili
rangiranja. Numeric NPZ inference checkpoint mora sačuvati težine/logits/akcije i
cijele determinističke replay maske. Težine/raw ulazi ostaju lokalni.

Procjena izvršavanja5–15min, nice19, jedna numerička nit, sekvencijalno. Tehnički
PASS ne dokazuje učenje, fizičku validaciju ili prednost CA/SimFire-a. Native mobilni
resursi ostaju otvoreni dio TASK-040 B. Veći trening traži novi unaprijed zapisan plan.
