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

### Treniranje je tehnički dostupno; research gate nije prošao

Na korisnikov zahtjev dodan je pravi FEDS/SimFire Gymnasium env i MaskablePPO CLI,
odvojeni od starog sintetičkog env-a i Firehose checkpointa. Env uzorkuje samo TRAIN
epizode, koristi četiri 12h odluke kroz 48h, budžet `0,2,4` po defaultu, no-op plus osam
smjerova za kratku fireline akciju. Budžet ne prekida epizodu, no-op ostaje dostupan, a
kumulativna šteta se čuva i nakon fireline upisa. Reward koristi samo dodatne SimFire
burn ćelije; budući FEDS obodi ne ulaze u policy observation ili reward.
Na stvarnom Plateau TRAIN slučaju potvrđen je i budžet-1 potez: validan fireline je
postavljen, jedna jedinica potrošena, pa se sva četiri 12h koraka završe.

Za bounded tehnički PPO smoke (ne benchmark trening), koristi nov izlazni direktorij
pod ignorisanim `.local/`:

```sh
PYTHONPATH=src MPLCONFIGDIR=.local/mpl-cache XDG_CACHE_HOME=.local/cache SDL_VIDEODRIVER=dummy \
  .local/simfire-venv/bin/python scripts/train_feds_simfire.py \
  --steps 64 --out .local/feds-ppo-experiments/NEW-ID \
  --wind-adjustment-factor 0.01 --budgets 0,2,4 --seed 7
```

`--steps` mora biti višekratnik 64; 64 je bounded smoke, veće vrijednosti treniraju
duže. WAF je obavezno eksplicitan i trenutno nema kalibrisanog izbora. `.605` iz ranije
smoke komande sada je poznato loš cohort kandidat (157 map-edge kontakata u 396
case-timepointa); nemoj ga koristiti za glavni trening. `.01` izbjegao je rub, ali je
takođe pao po IoU i nije validan izbor. Ako treba provjeriti samo tehničku putanju,
koristi bounded smoke s novim `.local/` outputom i tretiraj ga kao exploratory.
Checkpoint i training receipt se ne commituju. Raniji 64-step smoke pri `.605` dokazuje
da CLI radi, ali nije preporučena postavka.

QA koda prolazi: SimFire Python 3.9 suite 65/65 PASS; glavni Python 3.12 suite 62 PASS
uz 9 optional-dependency skips; CLI smoke, svih 85 package checks, strict knowledge
validation za 69 Markdown fajlova i `git diff --check` prolaze.

Okruženje i testovi: [SimFire/FEDS env](../src/wildfire_rl/feds_simfire_env.py),
[trening CLI](../scripts/train_feds_simfire.py),
[env testovi](../tests/test_feds_simfire_env.py). Paketni `uv pip check` prolazi za 85
paketa. Originalni target Python runtime je bio zaglavljen; trenutni `bin/python` poziva
isti provjereni Python 3.9.25 preko susjednog `cfsds-train-qc` worktreea, dok target
venv i njegove biblioteke ostaju u ovom worktreeu. Originalni symlink je sačuvan kao
`.local/simfire-venv/bin/python.stalled-target-runtime`; ne uklanjati susjedni worktree
dok se lokalni Python runtime ne zamijeni samostalnom kopijom.

### Naučni status

TRAIN-only no-op screening je završen na svih 99 slučajeva za WAF
`0, 0.0025, 0.01, 0.025, 0.05, 0.10, 0.20, 0.605`, uz 5-min interni korak, seed=0,
48h horizont i 12h forcing segmente. Svaki run je završio 99/99; svaki kandidat je imao
396 scored case-timepointa. Budući FEDS obodi nisu ulazili u simulaciju/policy; korišteni
su samo nakon simulacije za ocjenu.

Dodatna osjetljivost WAF .01 / 1-min korak dala je mean IoU .4771, praktično isto kao
.4769 na 5-min koraku, uz nula rubnih kontakata; strict screen je i dalje FAIL. Koraci
3/10/15 min nisu pokretani jer ova provjera nije promijenila zaključak. Interni korak
ostaje neizabran.

**Gate: FAIL.** Persistence baseline je mean IoU .5343 i area error 2,351.7 ha; elipsa
.5308 i 2,346.6 ha. Najbolji IoU među WAF kandidatima je .4769 (.0025), a najmanja
greška površine 2,262.1 ha (.01). Nijedan kandidat ne nadmašuje obje reference po oba
kriterija uz nula rubnih kontakata. WAF/timebase nije zaključan; validation mape nisu
preuzete, 2024 TEST nije učitan. Potpuni sažetak i checksumi su u
[TRAIN reportu](../reports/real-fire-data/feds-simfire-train-noop-screen-v1.json).

Tehnički PPO CLI/env i kratki smoke ostaju dostupni, ali validirano benchmark treniranje
je blokirano. Sljedeći korak je pregledati greške i forcing/spatial assumptions, izabrati
revidiranu zajedničku kalibraciju na TRAIN-u i ponoviti no-op gate; tek nakon prolaza
smiju se preuzeti validation rasteri. Ne podešavati reference ili test slučajeve radi
prolaza. Vidi [environment record](research/SIMFIRE_ENVIRONMENT.md) i
[ADR-022](specs/DECISION_RECORDS.md).

## Za mjerodavno poređenje

1. Dijagnosticirati zašto simulirani burn ima niži mean IoU od persistence i elipse;
   kalibrisati zajedničke forcing/SimFire postavke samo na TRAIN kohorti.
2. Ponoviti isti no-op gate protiv nepromijenjenih baseline pravila. Ne preuzimati
   validation mape dok TRAIN kandidat ne prođe i parametri ne budu zamrznuti.
3. Prije policy-benefit poređenja precizirati operativnu gradnju linije, pa svim
   agentima dati iste scenarije, budžete, horizonte, observations i seedove.
4. TEST 2024 otvoriti tek za završni obračun poslije zaključavanja izbora.

Trenutni kod može izvršiti kratki tehnički PPO smoke. Gate blokira duži benchmark/policy
trening i tvrdnje o validaciji ili koristi politike.

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
