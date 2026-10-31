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
    "initial_scar_cell_ids_one_based": result.get("warmup_historical_scar_cell_ids_one_based"),
    "initial_front_cell_ids_one_based": result.get("warmup_active_front_cell_ids_one_based"),
    "reset_state_matches_grid": result.get("upstream_reset_state_matches_csv"),
    "cumulative_cells_after_replay": result.get("simulator_cumulative_affected_cells"),
    "terminal_reason": result.get("termination_reason"),
    "terminal_front_cell_ids_one_based": result.get("active_front_cell_ids_one_based"),
    "terminal_state_matches_grid_history": result.get("terminal_state_matches_grid_history"),
    "python_cumulative_affected_cells": result.get("python_cumulative_affected_cells"),
    "python_cumulative_matches_simulator": result.get("python_cumulative_matches_simulator"),
    "subprocess_returncode": result.get("subprocess_returncode"),
}
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
expected = {
    "return_code": 0,
    "success": True,
    "initial_state_import_log": "Imported historical state: scar=1 front=2",
    "initial_affected_cells": 3,
    "initial_active_cells": 2,
    "initial_scar_cell_ids_one_based": [1],
    "initial_front_cell_ids_one_based": [2, 3],
    "reset_state_matches_grid": True,
    "subprocess_returncode": 0,
    "terminal_state_matches_grid_history": True,
    "python_cumulative_affected_cells": 3,
    "python_cumulative_matches_simulator": True,
}
valid_reasons = {"weather_horizon", "front_extinguished", "grid_exhausted", "no_ignition"}
if (
    any(summary.get(key) != value for key, value in expected.items())
    or summary["terminal_reason"] not in valid_reasons
    or summary["cumulative_cells_after_replay"] < 3
):
    raise SystemExit("Historical initial state check failed: " + json.dumps(summary))
print(json.dumps(summary, indent=2))
