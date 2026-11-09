"""The SimFire no-op gate path refuses VALIDATION without a freeze and non-5-minute steps."""

import contextlib
import io
import unittest

try:
    import numpy  # noqa: F401
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from scripts import evaluate_feds_train_noop as evaluator
from scripts import run_feds_noop_episode as runner


class NoopGateGuardTests(unittest.TestCase):
    def test_runner_refuses_validation_without_a_freeze_record(self):
        with self.assertRaisesRegex(ValueError, "freeze record"):
            runner.run_episode("any-case", 0.01, split="validation")

    def test_runner_refuses_test_split(self):
        with self.assertRaisesRegex(ValueError, "TEST"):
            runner.run_episode("any-case", 0.01, split="test")

    def test_runner_refuses_a_step_other_than_five_minutes(self):
        with self.assertRaisesRegex(ValueError, "5 minutes"):
            runner.run_episode("any-case", 0.01, internal_update_minutes=1)

    def test_evaluator_refuses_validation_without_an_allowlisted_record(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            evaluator.main(["--wind-adjustment-factor", "0.01", "--split", "validation"])
        self.assertIn("freeze record", stderr.getvalue())

    def test_evaluator_only_offers_the_five_minute_step(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            evaluator.main(["--wind-adjustment-factor", "0.01", "--internal-update-minutes", "1"])
