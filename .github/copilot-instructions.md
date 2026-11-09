---
type: Agent Instructions
title: GitHub Copilot project entry point
---
# Project context

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
validation). Stage 2 is reported in its own PR and ADR. TEST 2024 stays closed.
The synthetic pilot and legacy runtime verification
are not evidence of RL advantage or physical validation. Save decisions/evidence using
the shared AGENTS rules and [maintenance workflow](../knowledge/maintenance.md).
