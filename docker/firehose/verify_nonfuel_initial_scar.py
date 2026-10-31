"""Verify explicit NF historical-scar import and reject ambiguous states."""

import contextlib
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("probe", "/opt/firehose_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

root = Path("/outputs/nonfuel-initial-scar")
fixture_root = Path("/opt")
root.mkdir(parents=True, exist_ok=True)


def run_probe(case_name, fixture_name):
    case_root = root / case_name
    sys.argv = [
        "probe",
        "--policy", "none",
        "--seed", "123",
        "--budget", "0",
        "--steps-before-sim", "0",
        "--steps-per-action", "8",
        "--max-steps", "200",
        "--initial-state-csv", str(fixture_root / fixture_name),
        "--out", str(case_root),
    ]
    with (root / (case_name + ".probe.log")).open("w") as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            exit_code = probe.main()
    result = json.loads((case_root / "result.json").read_text())
    stderr_path = case_root / "simulator-stderr.txt"
    stderr = stderr_path.read_text() if stderr_path.exists() else ""
    return {"probe_exit_code": exit_code, "result": result, "stderr": stderr}


accepted_run = run_probe(
    "accepted-explicit-scar", "nonfuel_initial_scar_fixture.csv"
)
accepted = accepted_run["result"]
nonfuel_ids = set(accepted.get("upstream_nonfuel_cell_ids_one_based", []))
transitions = accepted.get("transitions") or []
terminal = accepted.get("terminal_state") or {}
nonfuel_active_transitions = [
    transition.get("nonfuel_active_front_cell_ids_one_based", [])
    for transition in transitions
]
accepted_ok = bool(
    accepted.get("initial_state_import_log") ==
    "Imported historical state: scar=1 front=1"
    and accepted.get("upstream_reset_state_matches_csv") is True
    and accepted.get("warmup_ever_affected_cell_ids_one_based") == [1, 4]
    and accepted.get("warmup_historical_scar_cell_ids_one_based") == [4]
    and accepted.get("warmup_active_front_cell_ids_one_based") == [1]
    and accepted.get("warmup_nonfuel_scar_cell_ids_one_based") == [4]
    and accepted.get("warmup_nonfuel_active_cell_ids_one_based") == []
    and 4 in nonfuel_ids
    and accepted.get("success") is True
    and accepted.get("terminal_state_matches_grid_history") is True
    and accepted.get("python_cumulative_matches_simulator") is True
    and 4 in set(terminal.get("ever_affected_ncells", []))
    and not set(terminal.get("active_front_ncells", [])) & nonfuel_ids
    and all(not active_ids for active_ids in nonfuel_active_transitions)
    and accepted.get("error") is None
)

invalid_cases = [
    (
        "reject-implicit-burnt",
        "nonfuel_initial_scar_reject_burnt_fixture.csv",
        "requires explicit scar_nf state for an NF scar",
    ),
    (
        "reject-nonfuel-active-front",
        "nonfuel_initial_scar_reject_active_fixture.csv",
        "cannot mark a non-fuel cell as burning",
    ),
    (
        "reject-scar-on-fuel",
        "nonfuel_initial_scar_reject_mismatch_fixture.csv",
        "scar_nf state requires an NF fuel cell",
    ),
]
rejections = []
for case_name, fixture_name, expected_error in invalid_cases:
    run = run_probe(case_name, fixture_name)
    rejections.append({
        "fixture": fixture_name,
        "probe_exit_code": run["probe_exit_code"],
        "expected_rejection": expected_error,
        "rejection_confirmed": expected_error in run["stderr"],
        "simulator_returncode": run["result"].get("subprocess_returncode"),
        "secondary_probe_error": run["result"].get("error"),
    })

summary = {
    "schema": "firehose-nonfuel-initial-scar-compatibility/v2",
    "contract": {
        "explicit_state": "scar_nf",
        "accepted_only_when_fuel_class_is": "NF",
        "cumulative_damage_cell_ids_one_based": accepted.get(
            "warmup_ever_affected_cell_ids_one_based"
        ),
        "damage_semantics": "pre-existing scar is included in ever_affected; measure new simulated damage relative to the same initial state",
        "active_front_cell_ids_one_based": accepted.get(
            "warmup_active_front_cell_ids_one_based"
        ),
        "nonfuel_scar_cell_ids_one_based": accepted.get(
            "warmup_nonfuel_scar_cell_ids_one_based"
        ),
        "nonfuel_active_front_cell_ids_one_based": accepted.get(
            "warmup_nonfuel_active_cell_ids_one_based"
        ),
        "terminal_ever_affected_cell_ids_one_based": terminal.get("ever_affected_ncells"),
        "terminal_active_front_cell_ids_one_based": terminal.get("active_front_ncells"),
        "nonfuel_active_front_cells_over_all_transitions": nonfuel_active_transitions,
    },
    "accepted_fixture": {
        "file": "nonfuel_initial_scar_fixture.csv",
        "probe_exit_code": accepted_run["probe_exit_code"],
        "initial_state_import_log": accepted.get("initial_state_import_log"),
        "reset_grid_matches_import": accepted.get("upstream_reset_state_matches_csv"),
        "completed_no_action_episode": accepted.get("success"),
        "terminal_state_matches_grid_history": accepted.get("terminal_state_matches_grid_history"),
        "python_cumulative_matches_simulator": accepted.get("python_cumulative_matches_simulator"),
        "probe_error": accepted.get("error"),
        "contract_confirmed": accepted_ok,
    },
    "rejected_fixtures": rejections,
    "training": False,
    "physical_or_historical_fire_behavior_validation": False,
    "bounded_probe_exit_code_note": "The nested generic probe is capped at 200 decisions; the accepted fixture normally returns 0 after its synthetic-map no-action episode reaches a named terminal state. This is an importer/state contract check, not physical validation.",
    "status": "PASS_EXPLICIT_NF_SCAR_IMPORT_CONTRACT" if (
        accepted_ok and all(case["rejection_confirmed"] for case in rejections)
    ) else "FAIL_NF_SCAR_IMPORT_CONTRACT",
}
(root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
if summary["status"] != "PASS_EXPLICIT_NF_SCAR_IMPORT_CONTRACT":
    raise SystemExit(summary["status"])
print(json.dumps(summary, indent=2))
