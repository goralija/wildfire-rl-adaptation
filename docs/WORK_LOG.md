# Work log

2026-10-28 — empty upstream repository cloned; local empty base commit created to permit
worktree isolation. Work occurs on `feature/project-bootstrap`. No original project files
existed. User opted out of questions; all unconfirmed project choices remain assumptions.

Pre-flight: simulator -> policies -> evaluation share GridFire contract; optional Gym adapter
wraps that same engine. Pilot metrics never stand in for Cell2Fire validation.

Task 2 complete: simulator tests first failed for absent implementation; 11 behavior tests
passed after implementation. Two invalid test fixtures were corrected because they put
priority cells on NONFUEL; production validation was retained.
Task 3 complete: evaluation tests first failed for absent module, then six tests passed.
Task 4: checkpoint audit and optional Gym tests failed first; train/save/load smoke ran
1,024 CPU steps. Added RED→GREEN warmup-terminal regression after finding a valid fire
could end before the agent's first action.
Ruling: initial horizon 80 truncated some pilot fires; raise config horizon to 240 and
rerun the baseline matrix before reporting. Otherwise delayed spread could bias comparisons.
Ruling: native worktree creation had no repository context (task cwd was an empty folder);
used a local Git worktree under the authorized workspace after creating an empty base commit.

Task 5 complete: independent read-only source review found no Critical/Important issues;
22 tests passed independently. Final: minor (deferred): JSON null config prints traceback
instead of a friendly validation error (TASK-010); valid configs unaffected.
Ruling: realism, legacy inference, adaptation gains and generalization remain outside
bootstrap verdict because they have not been run; risk of misreporting is addressed by
explicit labels throughout README, reports and protocol.
Verification: 300-episode pilot replay identical excluding runtime; 0 truncated at horizon
240. Clean no-dependency environment passes 18 core tests and smoke, 4 RL tests skip;
modern optional environment passes all 22 tests. Pilot figure rendered locally and checked.
Local branch/worktree retained. No push, merge, paid compute or messaging performed.

Final artifact check: Python CSV writer uses standard CRLF line endings; Git whitespace
check flagged them. Added a CSV text/eol=lf Git attribute so committed reports normalize
without changing data or source hashes. This affects only repository serialization.
