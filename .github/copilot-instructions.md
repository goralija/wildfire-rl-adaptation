---
type: Agent Instructions
title: GitHub Copilot project entry point
---
# Project context

Najnovije: TASK-038/ADR-042 je završen kratki CA BC/PPO na `codex/ca-learning-pilot`;
pročitati [learning pilot](../docs/research/CA_LEARNING_PILOT.md) i najnoviji STATUS prije rada.

Aktivni nalog 2026-11-21 je TASK-035, završeni kontrolisani CA pilot (ADR-039–040), na
`codex/ca-controlled-pilot` iz SimFire repair grane. Pročitati [pilot](../docs/research/CA_CONTROLLED_PILOT.md)
i najnovije STATUS/NEXT_SESSION; stariji tekst o odgođenom CA je historija.

Read and follow [AGENTS.md](../AGENTS.md), then [index.md](../index.md),
[project context](../knowledge/project-context.md), [STATUS](../docs/STATUS.md)
and [NEXT_SESSION](../docs/NEXT_SESSION.md). Follow task-specific links before edits.
Current state (2026-11-09, ADR-029): the results of ADR-022 to ADR-028 are invalid
until rerun. The gridMET sampler gave every fire in a year the weather of that year's
first fire (fixed). PRs #3–#5 (SimFire/FEDS gate, steps 5–8, synthetic CA) are merged
into main as history; do not cite their numbers as findings. The fix tasks
TASK-021–024 and TASK-027 are merged (PR #15: 98 TRAIN, FEDS `t` read as the local-solar
overpass, regenerated gridMET file); decisions are in ADR-030 and its addenda. Stages 1 and 2
of the TASK-026 rerun may run without a further go-ahead (stage 2 only if stage 1 passes);
merges and stage 3 stay with the user (see docs/HANDOFF_STAGE_1_2.md). Stage 1 passed
(ADR-031: WAF 0.10 / ROS 1.0 frozen, VALIDATION scored once; a pre-set gate, not a physical
validation). Stage 2 is complete (ADR-032: none of the six primary tests rejects; base PPO is
not distinguishable from a random legal line or the best TRAIN heuristic; a simulator result). Stage 3
waits for the user's decision.
The SimFire TRAIN-only TASK-028–030 iterations are complete on codex/simfire-policy-iterations (ADR-034, 2026-11-19): 98x33 outcomes, eight LOO methods, no candidate meets the registered continuation threshold. TASK-034 has since been completed; see ADR-036 below. Follow STATUS, NEXT_SESSION and docs/research/SIMFIRE_B1_EXPLORATION.md. VALIDATION, TEST 2024 and CA stage 3 stay closed.
The synthetic pilot and legacy runtime verification
are not evidence of RL advantage or physical validation. Save decisions/evidence using
the shared AGENTS rules and [maintenance workflow](../knowledge/maintenance.md).

Latest 2026-11-20 (ADR-036): TASK-034 is complete on codex/simfire-observation-audit.
Read docs/research/SIMFIRE_OBSERVATION_AUDIT.md. A startup race is fixed, four nested
families do not meet the threshold, and numerical/observation limitations are explicit.
TASK-035 CA contract/pilot is a draft, not training approval; TEST and new VALIDATION stay closed.

Latest ADR-038 (2026-11-20): the authorized observation-v2 repair is complete on
codex/simfire-observation-repair. Read docs/research/SIMFIRE_OBSERVATION_REPAIR.md.
Information aliases are repaired; the fixed fine rule has an uncertain TRAIN gain,
while no learned candidate meets the threshold. Prior PR20 remains open; new PR optional.
TASK035 CA is a draft and TASK037 holds remaining SimFire work. No automatic holdout/training.
