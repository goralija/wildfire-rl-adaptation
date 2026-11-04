#!/usr/bin/env bash
# Paired VALIDATION benchmark of every trained ADR-026 policy plus the ADR-025 heuristics.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.local/simfire-venv/bin/python}
PARAMS=${PARAMS:-configs/frozen/feds-simfire-stress-scenario-v1.json}
RUNS=${RUNS:-.local/ppo/adr024}
SEEDS=${SEEDS:-"11 12 13 14 15"}
WORKERS=${WORKERS:-7}
OUT=${OUT:?set OUT to a new report path}
export PYTHONPATH=src MPLCONFIGDIR=$PWD/.local/mpl-cache XDG_CACHE_HOME=$PWD/.local/cache
export SDL_VIDEODRIVER=dummy OMP_NUM_THREADS=1 PYTHONWARNINGS=ignore
args=()
for seed in $SEEDS; do
  for name in base ft-b1 ft-b2 ft-b4; do
    if [ -f "$RUNS/$name-s$seed/policy.zip" ]; then
      args+=(--policy "$name-s$seed=ppo:$RUNS/$name-s$seed/policy.zip")
    fi
  done
done
for heuristic in noop random_legal downwind advancing_front; do
  args+=(--policy "$heuristic=heuristic:$heuristic")
done
"$PY" scripts/benchmark_feds_policies.py --split validation --params "$PARAMS" \
  --workers "$WORKERS" "${args[@]}" --out "$OUT"
