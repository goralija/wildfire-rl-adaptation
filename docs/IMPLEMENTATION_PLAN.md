# Project bootstrap implementation plan

**Date:** 2026-10-28. **Goal:** recoverable research foundation plus tested pilot.
**Spec:** `specs/VISION.md`, `specs/BUSINESS_RULES.md` and `research/PROTOCOL.md`.
**Architecture:** dependency-free synthetic grid engine, policies and paired evaluation;
optional Gymnasium/MaskablePPO interface; Firehose stays an external, pinned dependency.
**Stack:** Python >=3.11 (reference 3.13), unittest, JSON/CSV/SVG, optional SB3.

User explicitly requests autonomous progress without questions. Design choices here are
agent assumptions, not additional agreements. Native execution in this session.
No remote writes, global installs, expensive training or upstream source modification.

## Review focus
Budget exhaustion must continue the fire; previously ignited cells stay damaged;
policy RNG must not change spread RNG; paired comparisons require identical scenarios;
horizon truncation must not silently count as containment.

## Task 1 — knowledge and research contract
- [x] Save source provenance, rubric weights, professor requirements and simulator audit.
- [x] Write scoped specs, decisions, protocol, backlog and resume instructions.
- [x] Verify links, weights sum to 100, assumptions and planned work are explicit.

## Task 2 — deterministic pilot engine and baselines
Files: `src/wildfire_rl/{simulator,policies}.py`, `tests/test_simulator.py`.
Interface: `Scenario`, `GridFire.reset(seed)`, `step(action)`, `action_masks()`, `metrics()`;
`choose_action(env, policy, rng)` returns cell index or `env.noop`.
- [x] First write and run failing tests for budget, no-op, masks, cumulative damage,
  deterministic spread, synchronous transitions and termination/truncation.
- [x] Implement smallest synthetic simulator and random, min_l2, max_l2, priority baselines.
- [x] Run `PYTHONPATH=src python3 -m unittest discover -s tests -v` → green.

## Task 3 — paired experiment and evidence
Files: `evaluation.py`, `cli.py`, configs, `tests/test_evaluation.py`.
Interface: `evaluate(config)` → episode dicts; `summarize(rows)` → paired differences
against no-action with bootstrap intervals; CLI writes run manifest, CSV, SVG.
- [x] First write/run failing tests for same-seed replay, zero-budget equality,
  incompatible pairs, invalid config and no overwrites.
- [x] Implement manifests with config/source hashes and environment metadata.
- [x] Run pilot matrix twice and compare deterministic metrics (runtime may differ).

## Task 4 — optional RL smoke and upstream compatibility audit
Files: `gym_env.py`, `train.py`, optional tests, `checkpoint_audit.py`.
- [x] First test Gym API, valid no-op after budget exhaustion and training save/load.
- [x] Implement optional adapter and bounded CPU smoke training; keep pilot results separate.
- [x] Inspect checkpoint ZIP metadata without deserializing pickle/PyTorch objects.
- [x] Record exactly what was tested and what remains unverified.

## Task 5 — verification and handoff
- [x] Full tests, clean install, reproduce pilot, inspect SVG and review branch.
- [x] Update `docs/STATUS.md`, `docs/NEXT_SESSION.md`, experiment log and checklist.
- [x] Commit locally, create Git bundle backup and leave clear publication instructions.

## Execution notes
Plan implemented in this session. Main Firehose integration/fine-tuning is deliberately
outside bootstrap completion and remains TASK-004 onward in BACKLOG. The checkpoint
audit is a package module rather than a scripts/ wrapper. A fresh reviewer checks code;
reports and final handoff are verified separately by the implementer. Local commits and
bundle preserve the result. User requested no questions, so keep the feature branch
without merge/push; preserve its worktree and all ignored local context.
