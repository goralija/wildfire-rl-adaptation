"""Characterize the current C++ rule for a historical scar on an NF cell."""

import contextlib
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("probe", "/opt/firehose_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

root = Path("/outputs/nonfuel-initial-scar")
fixture = Path("/opt/nonfuel_initial_scar_fixture.csv")
sys.argv = [
    "probe",
    "--policy", "none",
    "--seed", "123",
    "--budget", "0",
    "--steps-before-sim", "0",
    "--steps-per-action", "1",
    "--max-steps", "1",
    "--initial-state-csv", str(fixture),
    "--out", str(root),
]

with (Path("/outputs") / "nonfuel-initial-scar-probe.log").open("w") as log:
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        probe_exit_code = probe.main()

result = json.loads((root / "result.json").read_text())
stderr = (root / "simulator-stderr.txt").read_text()
expected_error = "InitialState.csv marks a non-fuel/harvested cell as burned"
summary = {
    "schema": "firehose-nonfuel-initial-scar-compatibility/v1",
    "fixture": "burnt cell 4 is NF in Sub20x20; burning cell 1 is burnable",
    "probe_exit_code": probe_exit_code,
    "probe_adapter_error": result.get("error"),
    "simulator_returncode": result.get("subprocess_returncode"),
    "simulator_rejection": expected_error if expected_error in stderr else None,
    "expected_current_rejection_confirmed": expected_error in stderr,
    "training": False,
}
(Path("/outputs") / "nonfuel-initial-scar-summary.json").write_text(
    json.dumps(summary, indent=2) + "\n"
)
if not summary["expected_current_rejection_confirmed"]:
    raise SystemExit("The current non-fuel scar rejection was not reproduced")
print(json.dumps(summary, indent=2))
