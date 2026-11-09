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
TASK-021–024 are merged; decisions are in ADR-030 and its addenda. Next are TASK-027 and a
regenerated gridMET file; the TASK-026 reruns run in stages, each with the user's go-ahead (order and acceptance in NEXT_SESSION.md). TEST 2024 stays closed.
The synthetic pilot and legacy runtime verification
are not evidence of RL advantage or physical validation. Save decisions/evidence using
the shared AGENTS rules and [maintenance workflow](../knowledge/maintenance.md).
