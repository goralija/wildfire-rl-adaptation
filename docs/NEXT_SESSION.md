---
type: Handoff
title: SimFire/FEDS TRAIN-only PPO path and calibration status
---
# Naredni korak

## Trenutno stanje — 2026-11-03

Aktivan worktree je `.worktrees/fireline-simfire-benchmark` na grani
`codex/fireline-simfire-benchmark`, izvedenoj iz `main`. Glavni checkout i raniji
`cfsds-train-qc` worktree su sačuvani.

TRAIN input setup je završen: 99 train slučajeva, svi sa checksum-verifikovanim
LANDFIRE gorivom/terenom i FEDS početnom scar/front maskom. Tačan front postoji za
119/119 train/validation startova; episode manifest i gridMET forcing pokrivaju 99 train
i 20 validation slučajeva. Validation mape nisu preuzete, a 2024 TEST nije preuzet ni
učitan.

### Treniranje je tehnički dostupno

Na korisnikov zahtjev dodan je pravi FEDS/SimFire Gymnasium env i MaskablePPO CLI,
odvojeni od starog sintetičkog env-a i Firehose checkpointa. Env uzorkuje samo TRAIN
epizode, koristi četiri 12h odluke kroz 48h, budžet `0,2,4` po defaultu, no-op plus osam
smjerova za kratku fireline akciju. Budžet ne prekida epizodu, no-op ostaje dostupan, a
kumulativna šteta se čuva i nakon fireline upisa. Reward koristi samo dodatne SimFire
burn ćelije; budući FEDS obodi ne ulaze u policy observation ili reward.
Na stvarnom Plateau TRAIN slučaju potvrđen je i budžet-1 potez: validan fireline je
postavljen, jedna jedinica potrošena, pa se sva četiri 12h koraka završe.

Pokreni novi, kratak trening direktorij pod ignorisanim `.local/`:

```sh
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache SDL_VIDEODRIVER=dummy \
  .local/simfire-venv/bin/python scripts/train_feds_simfire.py \
  --steps 64 --out .local/feds-ppo-experiments/NEW-ID \
  --wind-adjustment-factor 0.605 --budgets 0,2,4 --seed 7
```

`--steps` mora biti višekratnik 64; 64 je bounded smoke, veće vrijednosti treniraju
duže. `0.605` je samo eksplicitan, provisional primjer za reprodukciju Plateau smokea,
ne zaključena postavka. Izlazni direktorij mora biti nov. Checkpoint i training receipt
se ne commituju. Jedan stvarni 64-step smoke već je završio: sačuvan/ponovo učitan model
i završni TRAIN rollout su u `.local/feds-ppo-smoke-waf-0.605-64steps/`.

QA je završena: SimFire Python 3.9 suite 63/63 PASS; glavni Python 3.12 suite 60 PASS uz
9 očekivanih optional-dependency skips; knowledge validator 69/69 Markdown PASS; CLI
smoke, svih 85 package checks i `git diff --check` prolaze.

Okruženje i testovi: [SimFire/FEDS env](../src/wildfire_rl/feds_simfire_env.py),
[trening CLI](../scripts/train_feds_simfire.py),
[env testovi](../tests/test_feds_simfire_env.py). Paketni `uv pip check` prolazi za 85
paketa. Originalni target Python runtime je bio zaglavljen; trenutni `bin/python` poziva
isti provjereni Python 3.9.25 preko susjednog `cfsds-train-qc` worktreea, dok target
venv i njegove biblioteke ostaju u ovom worktreeu. Originalni symlink je sačuvan kao
`.local/simfire-venv/bin/python.stalled-target-runtime`; ne uklanjati susjedni worktree
dok se lokalni Python runtime ne zamijeni samostalnom kopijom.

### Naučni status

Jedan Plateau TRAIN no-op recheck pri WAF .605 ponovio je 19 kumulativnih ćelija
(61.56 ha), IoU .64 prema 71.28 ha observed, bez dodira ruba u 4/4 vremenske tačke.
WAF oko .615–.625 brzo prerasta mapu. To je jedan požar, ne izbor WAF-a ni cohort gate.
Nijedan WAF/timebase nije izabran.

TRAIN-only no-op kohorta i poređenje sa persistence/elipsnom referencom još su otvoreni.
Zato je omogućena tehnička PPO putanja, ali PPO smoke nije benchmark, fizička validacija
ili dokaz prednosti. Za sve train/validation/test granice i ograničenja vidi
[environment record](research/SIMFIRE_ENVIRONMENT.md) i
[ADR-021](specs/DECISION_RECORDS.md). Test 2024 ostaje zatvoren.

## Za mjerodavno poređenje

1. Na TRAIN-u izmjeriti zajedničke WAF/timebase kandidate, no-op, persistence i
   unaprijed definisanu elipsu uz iste 48h vremenske tačke i map-edge metrike.
2. Zamrznuti zajedničke postavke prije preuzimanja validation mapa; validation koristiti
   samo za provjeru već fiksiranih postavki.
3. Prije policy-benefit poređenja precizirati operativnu gradnju linije, pa svim
   agentima dati iste scenarije, budžete, horizonte, observations i seedove.
4. TEST 2024 otvoriti tek za završni obračun poslije zaključavanja izbora.

Ove naučne provjere ne blokiraju lokalni tehnički PPO trening; blokiraju samo tvrdnje o
validaciji i koristi politike.

## Provjere prije predaje

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m wildfire_rl.cli --config configs/smoke.json --out runs/NEW-ID
python3 scripts/validate_knowledge.py --strict
UV_CACHE_DIR=.local/uv-cache uv pip check --python .local/simfire-venv/bin/python
git diff --check
```

Ne preuzimati validation rastere ni TEST podatke tokom PPO smokea. Ne pokretati plaćeni
compute, dugi trening, push ili merge bez odgovarajućeg naloga/upute. CFSDS/Cell2Fire
rezultati ostaju historijski i odvojeni od SimFire/FEDS.
