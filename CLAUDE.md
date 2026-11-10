---
type: Agent Instructions
title: Claude project entry point
---
# Project context

Follow [AGENTS.md](AGENTS.md). Read [index.md](index.md) and
[knowledge/project-context.md](knowledge/project-context.md), then the current
[STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md) and task-specific links.
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
waits for the user's decision. TEST 2024 stays closed.
Keep decisions and evidence in the
repository, following [maintenance](knowledge/maintenance.md). This file is a routing
shim; shared rules live in AGENTS.md.
