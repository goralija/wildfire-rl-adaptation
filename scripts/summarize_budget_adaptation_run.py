#!/usr/bin/env python3
"""Write the committed run record of a budget-adaptation benchmark (ADR-030 section 4).

Collates what the ignored local files hold: the training receipts, the TRAIN and
VALIDATION benchmark reports, the pre-VALIDATION lock and the analysis report. Nothing is
simulated or tested again here. The record refuses inputs that disagree with each other
(freeze record, checkpoint hashes, the best TRAIN heuristic, the TRAIN report hash).

The ``behaviour`` block is descriptive and was added after the result was seen: it shows
how many different action sequences each PPO policy uses, which the contrasts cannot.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/real-fire-data"
DEFAULT_RUNS = ROOT / ".local/ppo/adr030"
DEFAULT_TRAIN = ROOT / ".local/bench/adr030-train.json"
DEFAULT_VALIDATION = ROOT / ".local/bench/adr030-validation.json"
DEFAULT_LOCK = REPORTS / "feds-simfire-budget-validation-lock-adr030-v1.json"
DEFAULT_ANALYSIS = REPORTS / "feds-simfire-budget-benchmark-adr030-v1.json"
DEFAULT_OUT = REPORTS / "feds-simfire-budget-run-record-adr030-v1.json"
PPO_NAME = re.compile(r"(base|ft-b\d+)-s(\d+)")
RECEIPT_FIELDS = ("phase", "budgets", "seed", "requested_steps", "actual_steps",
                  "wall_clock_minutes", "checkpoint_sha256", "init_checkpoint_sha256",
                  "params_file_sha256", "split", "validation_or_test_cases_loaded")


class RunRecordError(ValueError):
    """The inputs of the run record disagree with each other."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _relative(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def family(policy: str) -> str:
    match = PPO_NAME.fullmatch(policy)
    return match.group(1) if match else policy


def benchmark_block(report: dict, *, split: str, freeze_sha256: str, checkpoints: dict) -> dict:
    """Check one benchmark report and reduce it to counts and family means."""
    if report.get("split") != split or report.get("test_cases_loaded") is not False:
        raise RunRecordError("Expected a %s report that loaded no TEST case." % split)
    if report.get("params_file_sha256") != freeze_sha256:
        raise RunRecordError("The %s report was run with another freeze record." % split)
    if report["errors"] or report.get("legacy_checkpoints"):
        raise RunRecordError("The %s report has errors or legacy checkpoints." % split)
    used = {name: item["checkpoint_sha256"] for name, item in report["checkpoint_receipts"].items()}
    if used != checkpoints:
        raise RunRecordError("The %s report used other checkpoints than the lock lists." % split)
    rows = report["episodes"]
    added = {(row["policy"], row["budget"], row["scenario_id"]): row["added_burned_ha"]
             for row in rows}
    scenarios = sorted({row["scenario_id"] for row in rows})
    budgets = sorted({row["budget"] for row in rows})
    policies = sorted({row["policy"] for row in rows})
    if len(rows) != len(scenarios) * len(budgets) * len(policies):
        raise RunRecordError("The %s report is not a full scenario x budget x policy grid." % split)
    members = defaultdict(list)
    for policy in policies:
        members[family(policy)].append(policy)
    mean_delta = {
        name: {str(budget): statistics.fmean(
            added[(policy, budget, scenario)] - added[("noop", budget, scenario)]
            for policy in names for scenario in scenarios) for budget in budgets}
        for name, names in sorted(members.items()) if name != "noop"}
    return {
        "created_utc": report["created_utc"],
        "scenario_count": len(scenarios),
        "policies": len(policies),
        "budgets": budgets,
        "episodes": len(rows),
        "errors": 0,
        "runtime_minutes": report["runtime_minutes"],
        "budget0_all_policies_equal_noop": all(
            added[(policy, 0, scenario)] == added[("noop", 0, scenario)]
            for policy in policies for scenario in scenarios) if 0 in budgets else None,
        "noop_mean_added_ha": statistics.fmean(added[("noop", budgets[0], s)] for s in scenarios),
        "family_mean_delta_ha_vs_noop": mean_delta,
    }


def behaviour_block(report: dict) -> dict:
    """How many different action sequences each PPO policy uses (descriptive, post hoc)."""
    by_policy = defaultdict(dict)
    for row in report["episodes"]:
        if PPO_NAME.fullmatch(row["policy"]) and row["budget"] > 0:
            by_policy[row["policy"]][(row["scenario_id"], row["budget"])] = tuple(row["actions"])
    groups = defaultdict(list)
    for policy in sorted(by_policy):
        groups[tuple(sorted(by_policy[policy].items()))].append(policy)
    base = {}
    for policy in sorted(by_policy):
        if family(policy) != "base":
            continue
        first = Counter(actions[0] for actions in by_policy[policy].values())
        action, count = first.most_common(1)[0]
        base[policy] = {
            "distinct_action_sequences": len(set(by_policy[policy].values())),
            "most_common_first_action": action,
            "share_of_episodes_with_that_first_action": count / len(by_policy[policy]),
        }
    return {
        "ppo_policies": len(by_policy),
        "distinct_ppo_behaviours": len(groups),
        "identical_behaviour_groups": sorted(names for names in groups.values() if len(names) > 1),
        "distinct_base_behaviours": len({key for key, names in groups.items()
                                         if any(family(name) == "base" for name in names)}),
        "base_policies": base,
    }


def training_block(runs_dir: Path, checkpoints: dict, *, freeze_sha256: str) -> dict:
    runs = []
    for name in sorted(checkpoints):
        receipt = json.loads((runs_dir / name / "training_manifest.json").read_text(encoding="utf-8"))
        if receipt["checkpoint_sha256"] != checkpoints[name]:
            raise RunRecordError("The receipt of %s names another checkpoint." % name)
        if receipt["params_file_sha256"] != freeze_sha256 or receipt["split"] != "train" \
                or receipt["validation_or_test_cases_loaded"] is not False:
            raise RunRecordError("%s was not trained on TRAIN with the freeze record." % name)
        runs.append({"run": name, **{field: receipt[field] for field in RECEIPT_FIELDS}})
    return {
        "models": len(runs),
        "total_decisions": sum(run["actual_steps"] for run in runs),
        "total_wall_clock_minutes": sum(run["wall_clock_minutes"] for run in runs),
        "runs": runs,
    }


def build_record(*, runs_dir: Path, train_path: Path, validation_path: Path, lock_path: Path,
                 analysis_path: Path, code_commits: dict) -> dict:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    train = json.loads(train_path.read_text(encoding="utf-8"))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    freeze_sha256, checkpoints = lock["freeze_record_sha256"], lock["checkpoint_sha256"]
    train_sha256 = sha256_file(train_path)
    selection = analysis["best_heuristic_selection"]
    if not (lock["train_benchmark"]["sha256"] == train_sha256 == selection["source_report_sha256"]):
        raise RunRecordError("The lock, the analysis and the TRAIN report name different TRAIN hashes.")
    if lock["best_heuristic_selection"]["best_heuristic"] != selection["best_heuristic"]:
        raise RunRecordError("The analysis used another best heuristic than the lock.")
    if analysis["source_split"] != "validation" or lock["created_utc"] >= validation["created_utc"]:
        raise RunRecordError("The lock must predate the analysed VALIDATION report.")
    blocks = {}
    for split, report, path in (("train", train, train_path), ("validation", validation, validation_path)):
        blocks[split] = {"local_full_report": _relative(path),
                         **benchmark_block(report, split=split, freeze_sha256=freeze_sha256,
                                           checkpoints=checkpoints),
                         "local_full_report_sha256": sha256_file(path),
                         "behaviour_descriptive_post_hoc": behaviour_block(report)}
    return {
        "schema_version": "feds-simfire-budget-run-record/1.0",
        "decision": "ADR-030 section 4, stage 2 of TASK-026; result in ADR-032",
        "label": "SIMULATOR BENCHMARK; NOT PHYSICAL VALIDATION OF SUPPRESSION",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "code_commits": code_commits,
        "freeze_record_sha256": freeze_sha256,
        "sim_params": validation["sim_params"],
        "policy_settings": validation["policy_settings"],
        "lock": {"file": _relative(lock_path), "sha256": sha256_file(lock_path),
                 "created_utc": lock["created_utc"],
                 "best_heuristic": selection["best_heuristic"]},
        "analysis": {"file": _relative(analysis_path), "sha256": sha256_file(analysis_path)},
        "training": training_block(runs_dir, checkpoints, freeze_sha256=freeze_sha256),
        "benchmarks": blocks,
        "test_cases_loaded": False,
        "validation_use": "VALIDATION was benchmarked once, after the policies and the best "
                          "TRAIN heuristic were locked; it selected nothing.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--train-report", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--validation-report", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--code-commit", action="append", default=[], metavar="STEP=COMMIT",
                        help="repository commit a step was run from; repeat per step")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    if not args.code_commit or any("=" not in item for item in args.code_commit):
        parser.error("give --code-commit STEP=COMMIT for every step")
    try:
        record = build_record(runs_dir=args.runs, train_path=args.train_report,
                              validation_path=args.validation_report, lock_path=args.lock,
                              analysis_path=args.analysis,
                              code_commits=dict(item.split("=", 1) for item in args.code_commit))
    except RunRecordError as exc:
        parser.error(str(exc))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.out),
                      "models": record["training"]["models"],
                      "validation_episodes": record["benchmarks"]["validation"]["episodes"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
