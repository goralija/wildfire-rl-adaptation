---
type: Research Protocol
title: SimFire benchmark — frozen comparison rules
status: frozen-for-evaluation-preparation
sources:
  - resource: /docs/research/PROTOCOL.md
  - resource: /docs/STATUS.md
  - resource: /data/manifests/simfire-fpa-fod-evaluation-membership-v1.json
  - resource: /src/wildfire_rl/simfire_gym_env.py
  - resource: /src/wildfire_rl/simfire_evaluation.py
---
# SimFire benchmark: fixed comparison rules

This document fixes how the policies will be compared after a base checkpoint and its
fine-tuned copy exist. It does not authorize or start training. The machine-readable
contract is [`evaluation-v1.json`](../../configs/simfire/evaluation-v1.json); its IDs,
hashes, settings, seeds and metrics are checked by the evaluation command.

## What the comparison can answer

The question is whether a PPO policy adapted on the 40 TRAIN incident environments ends
with less **simulated** burned area than its unchanged generic SimFire PPO starting point
on the same held-out incident conditions. No-op and a simple front-edge rule show how the
learned policies compare with transparent controls.

The result applies only to this SimFire version, the selected maps, daily weather proxy,
and simplified instant fireline actions. It cannot show that real historic fires would
have been smaller by the same number of hectares. Physical validation of the weather and
spread settings remains an open gate.

## Fixed incidents, environment and repeat runs

- Use the frozen membership file: 40 TRAIN incidents, 20 VALIDATION incidents, and 19
  final TEST incidents. Larch Creek stays excluded because it was used while debugging.
- Use the per-incident daily gridMET proxy as recorded; do not change its wind adjustment
  during policy selection. Use the proxy's stored default factor (0.3), not a per-policy
  override.
- Each episode has 32 fireline points, one decision per 30 simulated minutes, a 24-decision
  (12-hour) maximum, and a 15-update maximum lifetime for each burning cell.
- Repeat every incident with the same five environment seeds: 101, 211, 307, 401 and 503.
  For each incident/seed pair, all policies start from the same scenario and simulator
  seed. PPO inference is deterministic; seed variation comes from the environment.
- Keep the same observation, legal-action mask, action budget and simulator settings for
  every policy. No-op is always legal. Spending all points does not end the fire episode.

## Policies being compared

1. **No-op:** always wait and never place a line. This shows how much area SimFire burns
   without intervention.
2. **Front-edge heuristic:** when active fire exists and a legal cell is available, place
   one point in the legal cell closest by Manhattan distance to any currently burning
   cell. Break ties by the lowest row, then column. Otherwise wait. It uses only the
   current observation and action mask; it never reads future spread or a final perimeter.
3. **Base PPO:** a MaskablePPO checkpoint trained on generic SimFire functional scenarios,
   before it has seen any FPA-FOD cohort incident. The checkpoint must be saved and hashed.
4. **Fine-tuned PPO:** start from an exact copy of the base checkpoint and continue
   learning using only the 40 TRAIN incidents and SimFire rewards. Validation selects the
   saved checkpoint; the 19 TEST incidents are reserved for the final paired report.

The adapter, PPO architecture, and inference code are shared. This protocol does not
contain a base model or fine-tuned weights. Their training budgets, environment randomizer,
and checkpoint provenance must be recorded in a separate training manifest before anyone
starts training; no such run has happened yet.

## Measures and decision rule

The primary episode measure is the final cumulative area burned inside SimFire, in
simulated hectares, read from the adapter's cumulative burned cells. The primary paired
comparison is:

`base PPO burned area − fine-tuned PPO burned area`

A positive number means the fine-tuned policy left less area burned **in these
simulations**. Average the five matched seeds within each incident first, then give each
incident equal weight. Report the mean difference and a 95% percentile interval from
10,000 bootstrap samples of incidents (seed 20261102). This avoids treating repeated
seeds of one incident as 95 independent fires.

Also report per-incident values and the final cell count, fraction of burnable cells
burned, fireline points used, simulated minutes, and whether the episode ended naturally
or reached the time limit. Compare fine-tuned PPO with no-op and the heuristic as
secondary results. Keep the same incident/seed pairs in every comparison. Do not use FPA
reported final acres or MTBS perimeter as agent input, reward, checkpoint-selection
metric, or the headline outcome.

On VALIDATION, choose the fine-tuned checkpoint with the lowest equal-incident mean
simulated burned area over all 20 incidents and the five fixed seeds. If checkpoints tie,
choose the earliest saved checkpoint. Do not inspect TEST outcomes to choose model,
parameters, seeds, thresholds, or visual examples.

## Safe use of the runner

From the repository root, run the validation preflight first:

```sh
.local/simfire-venv/bin/python scripts/evaluate_simfire_benchmark.py --preflight-only
```

It verifies the contract and local VALIDATION inputs, initializes one observation, checks
that no-op is legal, and advances zero simulation steps. It does not load checkpoints or
train. The benchmark runner writes fresh CSV/JSON receipts under ignored `.local/` output.

Validation comparisons can run after checkpoint creation, without test access. TEST
inputs are blocked unless both `--open-test` and `--final-evaluation` are supplied, and the
runner then requires both frozen PPO checkpoints. Do not use those flags until training,
checkpoint choice, and physical-setting review are complete. Running a test evaluation
does not make its output a real-fire prediction.

## Remaining gate before training

The contract and inference runner are prepared, but this is not a scientific readiness
certificate. Before training, still document the generic base-model training recipe,
record the fine-tuning budget and stopping schedule, and review the 15-minute cell lifetime
and daily weather proxy as modeling assumptions. None of those checks may use final TEST
outcomes. Training remains unstarted until the user authorizes it.
