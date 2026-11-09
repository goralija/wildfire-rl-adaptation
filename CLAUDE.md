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
into main as history; do not cite their numbers as findings. Work next on the fix
tasks TASK-021–024 as separate PRs; the TASK-025 decisions are in ADR-030, and the
reruns in TASK-026 run in stages, each with the user's go-ahead (order and acceptance in NEXT_SESSION.md). TEST 2024 stays closed.
Keep decisions and evidence in the
repository, following [maintenance](knowledge/maintenance.md). This file is a routing
shim; shared rules live in AGENTS.md.
