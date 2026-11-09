---
type: Agent Instructions
title: Gemini project entry point
---
# Project context

Follow [AGENTS.md](AGENTS.md). Read [index.md](index.md) and
[knowledge/project-context.md](knowledge/project-context.md), then the current
[STATUS](docs/STATUS.md), [NEXT_SESSION](docs/NEXT_SESSION.md) and task-specific links.
The TRAIN-only SimFire/FEDS no-op gate has finished and failed. Diagnose shared
inputs/parameters and rerun the same gate on TRAIN before using validation maps; keep
2024 TEST closed. The bounded PPO path is a technical smoke only. See NEXT_SESSION.md
and the latest ADR for the current state.
Preserve the shared rules and knowledge maintenance workflow in AGENTS.md;
this file only routes the agent to the repository context.
