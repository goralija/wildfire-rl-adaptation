---
type: Agent Instructions
title: Gemini project entry point
---
# Project context

Follow [AGENTS.md](AGENTS.md). Read [index.md](index.md) and
[knowledge/project-context.md](knowledge/project-context.md), then the current
[STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md) and task-specific links.
Current state (2026-11-09, ADR-029): the results of ADR-022 to ADR-028 are invalid
until rerun. The gridMET sampler gave every fire in a year the weather of that year's
first fire (fixed). PRs #3–#5 (SimFire/FEDS gate, steps 5–8, synthetic CA) are merged
into main as history; do not cite their numbers as findings. The fix tasks
TASK-021–024 are merged; decisions are in ADR-030 and its addenda. Next are TASK-027 and a
regenerated gridMET file; the TASK-026 reruns run in stages, each with the user's go-ahead (order and acceptance in NEXT_SESSION.md). TEST 2024 stays closed.
See NEXT_SESSION.md
and the latest ADR for the current state.
Preserve the shared rules and knowledge maintenance workflow in AGENTS.md;
this file only routes the agent to the repository context.
