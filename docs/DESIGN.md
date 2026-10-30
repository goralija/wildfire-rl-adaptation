---
type: Design
title: Bootstrap design — 2026-10-28
status: draft
---
# Bootstrap design — 2026-10-28

Intent: an MPVI research project about adapting a pretrained wildfire intervention policy
across budgets, with a priority-protection evaluation. Stakeholders: student team and professor.
The user requests a useful start from an empty repository and durable project memory.

## Approaches considered
1. Immediately port Firehose: closest to the proposed pretrained model, but legacy Gym,
   custom SB3 fork, C++ dependencies and a hardcoded simulator seed must be investigated.
2. Immediately switch to SimFire/SimHarness: relevant alternative, but a different observation
   and action contract means pretrained Firehose weights cannot be assumed reusable.
3. Build a small experiment harness while auditing Firehose (selected by agent): quickly
   checks budgets, statistics and reproducibility without pretending to reproduce physics.

Decision: option 3 now; Firehose/Cell2Fire is a provisional main backend, not a confirmed
working integration. SimFire is the fallback after a bounded feasibility gate.

Deliverables: local repository with research knowledge, source provenance, rubric coverage,
repeatable pilot, tests, optional modern RL smoke path, decisions, handoff and backlog.
The pilot is intentionally synthetic and is not the final research result.

Constraints: no questions per user request; no publication of correspondence or email addresses;
no global dependencies, cloud charges, long training, remote branch changes or operational
firefighting claims. Core runs without third-party packages. Unknown deadline/compute are open.

Success: a fresh session can find state, execute tests and reproduce the pilot from README;
metrics cannot improve merely by exhausting budget or erasing evidence of past burning;
next simulator decision has explicit checks and a stopping rule.
