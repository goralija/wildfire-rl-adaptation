#!/usr/bin/env bash
# Step-8 budget-adaptation experiment on the ADR-024 free-burn stress scenario.
# For each training seed: base PPO at budget 2, then equal-length fine-tunes at
# budgets 1, 4 and the matched control at 2. Outputs stay in ignored .local/.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.local/simfire-venv/bin/python}
PARAMS=${PARAMS:-configs/frozen/feds-simfire-stress-scenario-v1.json}
OUT=${OUT:-.local/ppo/adr024}
BASE_STEPS=${BASE_STEPS:-8064}
FT_STEPS=${FT_STEPS:-3024}
SEEDS=${SEEDS:-"11 12 13"}
export PYTHONPATH=src MPLCONFIGDIR=$PWD/.local/mpl-cache XDG_CACHE_HOME=$PWD/.local/cache
export SDL_VIDEODRIVER=dummy OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore
mkdir -p "$OUT"
for seed in $SEEDS; do
  if [ ! -f "$OUT/base-s$seed/policy.zip" ]; then
    "$PY" scripts/train_feds_budget_adaptation.py --phase base --params "$PARAMS" \
      --budgets 2 --steps "$BASE_STEPS" --seed "$seed" --out "$OUT/base-s$seed"
  fi
done
for seed in $SEEDS; do
  for budget in 1 2 4; do
    if [ ! -f "$OUT/ft-b$budget-s$seed/policy.zip" ]; then
      "$PY" scripts/train_feds_budget_adaptation.py --phase finetune --init "$OUT/base-s$seed/policy.zip" \
        --params "$PARAMS" --budgets "$budget" --steps "$FT_STEPS" --seed "$((seed * 10 + budget))" \
        --out "$OUT/ft-b$budget-s$seed"
    fi
  done
done
echo EXPERIMENT_DONE
