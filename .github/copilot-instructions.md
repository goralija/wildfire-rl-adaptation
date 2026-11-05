---
type: Agent Instructions
title: GitHub Copilot project entry point
---
# Project context

Read and follow [AGENTS.md](../AGENTS.md), then [index.md](../index.md),
[project context](../knowledge/project-context.md), [STATUS](../docs/STATUS.md)
and [NEXT_SESSION](../docs/NEXT_SESSION.md). Follow task-specific links before edits.
Current direction (2026-11-05, ADR-028): training uses a synthetic CA on procedurally
generated fires, with physically bounded units and a counterfactual no-op reward. The 119
real FEDS starts serve only as a one-time test of locked policies. policy-v1 (imitation of
direct_flank plus PPO) ties the best heuristic and clearly beats no-op; every outcome is
simulated. The earlier SimFire/FEDS gate failure and steps 7–8 (ADR-023–027) are historical.
The TRAIN-only SimFire/FEDS no-op gate was diagnosed and rerun (ADR-023/024) and still
fails. Steps 7–8 ran as exploratory work on a separately labelled free-burn stress
scenario (ADR-024–026). Every policy result is simulator-only, not calibrated or physically
validated. Validation was scored once per frozen record; keep 2024 TEST closed.
The synthetic pilot and legacy runtime verification
are not evidence of RL advantage or physical validation. Save decisions/evidence using
the shared AGENTS rules and [maintenance workflow](../knowledge/maintenance.md).
