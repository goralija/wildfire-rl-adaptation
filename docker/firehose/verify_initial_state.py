"""Short isolated check for C++ historical scar/front import; performs no training."""

import contextlib
import json
import sys
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location("probe", "/opt/firehose_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

root = Path("/outputs/initial-state")
root.mkdir(parents=True, exist_ok=False)
case_out = root / "case"
sys.argv = [
    "probe",
    "--policy", "none",
    "--seed", "123",
    "--budget", "0",
    "--steps-before-sim", "0",
    "--steps-per-action", "1",
    "--max-steps", "200",
    "--initial-state-csv", "/opt/initial_state_fixture.csv",
    "--out", str(case_out),
]
with (root / "case.log").open("w") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
    code = probe.main()
result = json.loads((case_out / "result.json").read_text())
summary = {
    "return_code": code,
    "success": result.get("success"),
    "initial_state_import_log": result.get("initial_state_import_log"),
    "initial_affected_cells": result.get("warmup_affected_cells"),
    "initial_active_cells": result.get("warmup_active_cells"),
    "reset_state_matches_grid": result.get("upstream_reset_state_matches_csv"),
    "cumulative_cells_after_one_step": result.get("upstream_cumulative_cells"),
    "subprocess_returncode": result.get("subprocess_returncode"),
}
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
expected = {
    "return_code": 0,
    "success": True,
    "initial_state_import_log": "Imported historical state: scar=1 front=2",
    "initial_affected_cells": 3,
    "initial_active_cells": 2,
    "reset_state_matches_grid": True,
    "subprocess_returncode": 0,
}
if any(summary.get(key) != value for key, value in expected.items()):
    raise SystemExit("Historical initial state check failed: " + json.dumps(summary))
print(json.dumps(summary, indent=2))
