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
