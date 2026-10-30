import copy
import json
from pathlib import Path
import tempfile
import unittest

from wildfire_rl.evaluation import evaluate, summarize, write_run


CONFIG = dict(schema_version=1, label='test', backend='synthetic-v1',
              scenario=dict(rows=3, cols=3, ignition=[4], priority=[0],
                            spread_probability=1, burn_duration=2,
                            warmup_steps=0, horizon=10),
              budgets=[0, 1], seeds=[20, 21], policies=['none', 'min_l2'])


class EvaluationTests(unittest.TestCase):
    def test_paired_matrix_and_hand_calculated_damage(self):
        rows = evaluate(CONFIG)
        self.assertEqual(len(rows), 8)
        for row in rows:
            self.assertEqual(row['burned_cells'], 1 if row['budget'] == 1 and
                             row['policy'] == 'min_l2' else 9)
            self.assertFalse(row['truncated'])
            self.assertLessEqual(row['interventions'], row['budget'])

    def test_replay_metrics_are_identical(self):
        a = evaluate(CONFIG)
        b = evaluate(CONFIG)
        for rows in (a, b):
            for row in rows:
                row.pop('runtime_seconds')
        self.assertEqual(a, b)

    def test_summary_uses_paired_differences_and_zero_budget_control(self):
        summary = summarize(evaluate(CONFIG))
        adapted = next(r for r in summary if r['budget'] == 1 and r['policy'] == 'min_l2')
        self.assertAlmostEqual(adapted['saved_fraction_mean'], 8 / 9)
        self.assertAlmostEqual(adapted['saved_fraction_ci95_low'], 8 / 9)
        for row in summary:
            if row['budget'] == 0:
                self.assertEqual(row['saved_fraction_mean'], 0)

    def test_unpaired_or_duplicate_rows_are_rejected(self):
        rows = evaluate(CONFIG)
        for bad in (rows[1:], rows + [rows[0]], [r for r in rows if r['policy'] != 'none']):
            with self.assertRaises(ValueError):
                summarize(bad)

    def test_bad_configs_fail_before_running(self):
        for key, value in (('budgets', [-1]), ('seeds', [1, 1]), ('seeds', []),
                           ('policies', ['none', 'unknown']), ('policies', ['min_l2']),
                           ('backend', 'cell2fire'), ('schema_version', 2)):
            cfg = copy.deepcopy(CONFIG)
            cfg[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                evaluate(cfg)

    def test_run_contains_provenance_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'run'
            write_run(CONFIG, out)
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual(manifest['config'], CONFIG)
            self.assertEqual(len(manifest['source_sha256']), 64)
            self.assertEqual(len(manifest['config_sha256']), 64)
            self.assertTrue((out / 'episodes.csv').exists())
            self.assertTrue((out / 'summary.csv').exists())
            self.assertTrue((out / 'budget_damage.svg').exists())
            before = (out / 'manifest.json').read_bytes()
            with self.assertRaises(FileExistsError):
                write_run(CONFIG, out)
            self.assertEqual((out / 'manifest.json').read_bytes(), before)
