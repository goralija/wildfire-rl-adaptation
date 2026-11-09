import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.benchmark_feds_policies as benchmark
from scripts.benchmark_feds_policies import main
from wildfire_rl.feds_simfire_setup import POLICY_SETTING_KEYS, SimFireParams, policy_settings


ROOT = Path(__file__).resolve().parents[1]
STRESS_RECORD = ROOT / "configs/frozen/feds-simfire-stress-scenario-v1.json"


class BenchmarkSplitGuardTests(unittest.TestCase):
    def _refused(self, *arguments):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "bench.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                main(["--params", str(STRESS_RECORD), "--out", str(out), *arguments])
            self.assertFalse(out.exists())
        self.assertEqual(raised.exception.code, 2)
        return stderr.getvalue()

    def test_validation_refuses_a_record_outside_the_allowlist(self):
        # The stress record is committed and says selected_on_split=train, which was
        # all the old check asked for; it is not allowlisted (ADR-029).
        self.assertIn("allowlist", self._refused("--split", "validation"))

    def test_test_split_is_never_accepted(self):
        self.assertIn("invalid choice", self._refused("--split", "test"))


def _benchmark_settings(**overrides):
    """The settings a default --split train benchmark with the stress record expects."""
    frozen = json.loads(STRESS_RECORD.read_text(encoding="utf-8"))["frozen_params"]
    settings = policy_settings(SimFireParams(**frozen), weather_observation="previous",
                               line_placement="front_edge", observation_max_budget=4)
    settings.update(overrides)
    return settings


class CheckpointReceiptTests(unittest.TestCase):
    """A PPO checkpoint is evaluated only under the settings its training receipt states."""

    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.directory = Path(self._directory.name)
        self.checkpoint = self.directory / "run" / "policy.zip"
        self.checkpoint.parent.mkdir()
        self.checkpoint.write_bytes(b"not a real checkpoint; never loaded")
        self.out = self.directory / "bench.json"

    def tearDown(self):
        self._directory.cleanup()

    def _receipt(self, fields):
        content = {"schema_version": "test", "checkpoint_sha256":
                   hashlib.sha256(self.checkpoint.read_bytes()).hexdigest(), **fields}
        (self.checkpoint.parent / "training_manifest.json").write_text(json.dumps(content),
                                                                       encoding="utf-8")

    def _run(self, *extra):
        stderr = io.StringIO()
        arguments = ["--params", str(STRESS_RECORD), "--out", str(self.out), "--scenario-limit", "1",
                     "--policy", "ppo=ppo:%s" % self.checkpoint, *extra]
        with mock.patch.object(benchmark, "_run_job", return_value=[]) as run_job, \
                contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            try:
                code = main(arguments)
            except SystemExit as exit_:
                code = exit_.code
        return code, stderr.getvalue(), run_job.called

    def test_settings_name_every_required_field(self):
        settings = _benchmark_settings()
        self.assertEqual(set(settings), set(POLICY_SETTING_KEYS))
        for key in ("weather_observation", "weather_observation_rule", "sim_params",
                    "fireline_attenuation", "line_banking_floor"):
            self.assertIn(key, settings)
        self.assertEqual(settings["line_banking_floor"], "zero")
        pinned = policy_settings(SimFireParams(wind_adjustment_factor=0.01,
                                               fireline_attenuation="per_update"),
                                 weather_observation="previous", line_placement="front_edge",
                                 observation_max_budget=4)
        self.assertNotEqual(pinned["line_banking_floor"], "zero")

    def test_matching_receipt_is_accepted_and_recorded(self):
        self._receipt(_benchmark_settings())
        code, stderr, ran = self._run()
        self.assertEqual(code, 0, stderr)
        self.assertTrue(ran)
        report = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(report["checkpoint_receipts"]["ppo"]["status"], "verified")
        self.assertEqual(report["legacy_checkpoints"], [])

    def test_missing_receipt_is_refused_without_the_legacy_flag(self):
        code, stderr, ran = self._run()
        self.assertEqual(code, 2)
        self.assertIn("receipt", stderr)
        self.assertIn("--allow-legacy-checkpoints", stderr)
        self.assertFalse(ran)
        self.assertFalse(self.out.exists())

    def test_legacy_flag_admits_a_missing_receipt_and_labels_the_report(self):
        code, stderr, _ran = self._run("--allow-legacy-checkpoints")
        self.assertEqual(code, 0, stderr)
        report = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(report["legacy_checkpoints"], ["ppo"])
        self.assertEqual(report["checkpoint_receipts"]["ppo"]["status"], "legacy")
        self.assertTrue(report["allow_legacy_checkpoints"])
        self.assertIn("LEGACY", report["label"])

    def test_receipt_without_the_new_fields_is_legacy(self):
        old = _benchmark_settings()
        del old["line_banking_floor"], old["weather_observation_rule"]
        self._receipt(old)
        code, stderr, _ran = self._run()
        self.assertEqual(code, 2)
        self.assertIn("line_banking_floor", stderr)
        code, stderr, _ran = self._run("--allow-legacy-checkpoints")
        self.assertEqual(code, 0, stderr)
        report = json.loads(self.out.read_text(encoding="utf-8"))
        self.assertEqual(report["checkpoint_receipts"]["ppo"]["status"], "legacy")
        self.assertEqual(sorted(report["checkpoint_receipts"]["ppo"]["missing_fields"]),
                         ["line_banking_floor", "weather_observation_rule"])

    def test_mismatched_settings_are_refused_even_with_the_legacy_flag(self):
        params = json.loads(STRESS_RECORD.read_text(encoding="utf-8"))["frozen_params"]
        mismatches = {
            "weather_observation": dict(weather_observation="upcoming_perfect_forecast"),
            "sim_params": dict(sim_params=SimFireParams(**dict(params, wind_adjustment_factor=0.2)).as_dict()),
            "fireline_attenuation": dict(fireline_attenuation="per_update"),
            "line_banking_floor": dict(line_banking_floor="none_pinned_simfire"),
        }
        for field, override in mismatches.items():
            with self.subTest(field=field):
                self._receipt(_benchmark_settings(**override))
                for extra in ((), ("--allow-legacy-checkpoints",)):
                    code, stderr, ran = self._run(*extra)
                    self.assertEqual(code, 2)
                    self.assertIn(field, stderr)
                    self.assertFalse(ran)

    def test_receipt_for_another_checkpoint_is_refused(self):
        self._receipt(_benchmark_settings())
        self.checkpoint.write_bytes(b"a different file")
        for extra in ((), ("--allow-legacy-checkpoints",)):
            code, stderr, _ran = self._run(*extra)
            self.assertEqual(code, 2)
            self.assertIn("checkpoint_sha256", stderr)


class TrainingReceiptTests(unittest.TestCase):
    def test_both_training_scripts_write_the_policy_settings_into_their_receipt(self):
        # The scripts train PPO and are not run here; check that the receipt dictionary
        # spreads policy_settings(...), so it carries every POLICY_SETTING_KEYS field.
        import ast

        root = Path(__file__).resolve().parents[1]
        for script in ("train_feds_budget_adaptation.py", "train_feds_simfire.py"):
            tree = ast.parse((root / "scripts" / script).read_text(encoding="utf-8"))
            spreads = [
                node for node in ast.walk(tree) if isinstance(node, ast.Dict)
                and any(key is None and isinstance(value, ast.Call)
                        and getattr(value.func, "id", None) == "policy_settings"
                        for key, value in zip(node.keys, node.values))
                and any(isinstance(key, ast.Constant) and key.value == "checkpoint_sha256"
                        for key in node.keys)
            ]
            with self.subTest(script=script):
                self.assertEqual(len(spreads), 1)


if __name__ == "__main__":
    unittest.main()
