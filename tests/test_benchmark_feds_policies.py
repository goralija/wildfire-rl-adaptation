import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from scripts.benchmark_feds_policies import main


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


if __name__ == "__main__":
    unittest.main()
