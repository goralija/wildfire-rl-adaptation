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

2026-10-28 — TASK-004 continuation authorized: build Firehose/Cell2Fire, attempt existing
checkpoint inference without training, and document dataset. Existing task worktree reused;
clean at start (e1de936). Docker daemon is available; choose isolated Linux container
instead of altering the modern .venv or installing system compiler libraries. A cached
managed Python 3.10 was made available by uv but is not needed for the selected Docker path.
No remote Git writes or long training authorized/required.
Plan: pinned dependency build -> binary no-action test -> legacy model load/predict ->
bounded rollouts and seed/replay checks -> dataset inventory/data card -> knowledge/handoff.
Verify: build exit 0, model action shape/mask, subprocess exits/timeout, paired seed replay,
existing tests, manifests with exact source/image/package versions. Treat any runtime patch
as an explicit compatibility decision, never a silent upstream change.

Runtime decision: checkpoint system_info.txt reports Python 3.8.12, SB3 1.5.0,
PyTorch 1.11.0+cu113 (GPU disabled), numpy 1.22.2, Gym 0.21.0. Use Python 3.8.20
container to match the Python minor version; PyTorch 1.13.1 has a verified Linux ARM64
wheel. This is compatible inference reproduction, not an exact original machine image.
SB3 contrib fork is pinned to 43b7fe6fcdda71c2c10de7af0d20f39e48ae5df3 (version 1.5.0).
Build only overrides compiler/include/link flags (remove x86-only -m64, enable OpenMP,
Eigen path), preserving original source and model files. Runtime network will be disabled.

TASK-004 runtime results: original C++ fork compiled without source edits in Linux ARM64;
both pretrained ZIPs loaded in SB3/contrib 1.5.0 and executed (0 training steps). Final
12-case batch passed with returncode 0, exact no-action/model seed replay, changed spread
for changed C++ seeds, identical input hash, B=8 enforcement/no-op continuation, and
unchanged model tensors. Four new probe helper tests were RED→GREEN.
Ruling: keep Firehose for next phase; runtime feasibility passed, full research gate remains
partial pending reset/cumulative-damage and termination reason adapter. Do not switch to
SimFire merely because the legacy stack needs isolation.
Confirmed wrapper issue: warmup CSV has 7 affected cells, reset state is blank; fixed PPO
upstream counter 206 vs history union 207. Explicit sync-reset diagnostic gives 207/207.
Confirmed state semantics: C++ outputGrid=1 merges burning and burnt; done may be weather
horizon, so no containment claims. Datacard inventories 141 files, 400 cells (307 fuel),
base weather plus 129 variants; current rows mode reads only base Weather.csv.
No raw dataset/model/image published, no remote pushes, no training or paid compute.
