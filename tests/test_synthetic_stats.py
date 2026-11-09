import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest("optional NumPy dependency is not installed: %s" % exc)

from wildfire_rl.synthetic_stats import (
    paired_bootstrap,
    real_case_groups,
    summarize_groups,
    summarize_policies,
)


def row(saved, ret=None, lost=0, calls=0, line=0, line_in_noop=0, noop_edge=False):
    ret = saved - lost - 0.1 * calls if ret is None else ret
    return {"saved_fraction": saved, "return": ret, "units_lost": lost, "close_calls": calls,
            "retreats": 0, "line_cells": line, "line_area_ha": 3.24 * line,
            "line_cells_in_noop_footprint": line_in_noop, "agent_new_cells": 10,
            "noop_new_cells": 12, "agent_urban_cells": 0.0, "noop_urban_cells": 0.0,
            "edge_contact": noop_edge, "noop_edge_contact": noop_edge}


class PairedBootstrapTest(unittest.TestCase):
    def test_identical_inputs_give_a_zero_interval(self):
        result = paired_bootstrap([0.1, 0.4, 0.2], [0.1, 0.4, 0.2], seed=1)
        self.assertEqual(result["mean"], 0.0)
        self.assertEqual(result["ci95"], [0.0, 0.0])
        self.assertEqual((result["wins"], result["losses"], result["ties"]), (0, 0, 3))

    def test_known_shift_and_interval_brackets_the_mean(self):
        rng = np.random.default_rng(3)
        b = rng.random(200)
        a = b + 0.05 + 0.01 * rng.standard_normal(200)
        result = paired_bootstrap(a, b, seed=2)
        self.assertAlmostEqual(result["mean"], float(np.mean(a - b)))
        lo, hi = result["ci95"]
        self.assertLess(lo, result["mean"])
        self.assertGreater(hi, result["mean"])
        self.assertGreater(lo, 0.04)
        self.assertEqual(result["n"], 200)
        self.assertEqual(result["wins"] + result["losses"] + result["ties"], 200)

    def test_same_seed_is_reproducible_and_empty_is_none(self):
        a, b = [0.3, 0.1, 0.5, 0.0], [0.2, 0.2, 0.1, 0.0]
        self.assertEqual(paired_bootstrap(a, b, seed=5), paired_bootstrap(a, b, seed=5))
        self.assertIsNone(paired_bootstrap([], [], seed=5))


class SummaryTest(unittest.TestCase):
    def _rows(self):
        return {
            "noop": [row(0.0, calls=1), row(0.0), row(0.0), row(0.0)],
            "random": [row(0.01), row(0.0), row(0.02), row(0.0)],
            "direct_flank": [row(0.2, calls=3, line=10, line_in_noop=2), row(0.1, calls=2),
                             row(0.0), row(0.3, calls=1)],
            "protect_urban": [row(0.05), row(0.05), row(0.0), row(0.1)],
            "ppo=x.zip": [row(0.2), row(0.1), row(0.0), row(0.25)],
        }

    def test_blocks_are_separate_and_best_heuristic_is_by_saved(self):
        summary = summarize_policies(self._rows())
        self.assertEqual(summary["best_heuristic"], "direct_flank")
        flank = summary["policies"]["direct_flank"]
        self.assertAlmostEqual(flank["suppression"]["mean_saved_fraction"], 0.15)
        self.assertEqual(flank["suppression"]["line_cells"], 10)
        self.assertEqual(flank["suppression"]["line_cells_in_noop_footprint"], 2)
        self.assertEqual(flank["safety"]["close_calls"], 6)
        self.assertEqual(flank["safety"]["episodes_with_close_call"], 3)
        self.assertAlmostEqual(flank["objective"]["mean_return"], 0.15 - 0.6 / 4)
        self.assertNotIn("close_calls", flank["suppression"])

    def test_every_policy_is_contrasted_with_noop_random_and_best_heuristic(self):
        summary = summarize_policies(self._rows())
        ppo = summary["policies"]["ppo=x.zip"]["contrasts"]
        self.assertEqual(set(ppo), {"vs_noop", "vs_random", "vs_best_heuristic"})
        self.assertEqual(ppo["vs_best_heuristic"]["reference"], "direct_flank")
        for metric in ("saved_fraction", "return", "close_calls"):
            self.assertIn("ci95", ppo["vs_noop"][metric])
        saved = ppo["vs_best_heuristic"]["saved_fraction"]
        self.assertAlmostEqual(saved["mean"], (0.0 + 0.0 + 0.0 - 0.05) / 4)
        # No self-contrast; the reference policies still get the other contrasts.
        self.assertNotIn("vs_noop", summary["policies"]["noop"]["contrasts"])
        self.assertNotIn("vs_best_heuristic", summary["policies"]["direct_flank"]["contrasts"])
        self.assertIn("vs_random", summary["policies"]["direct_flank"]["contrasts"])

    def test_contrasts_do_not_depend_on_policy_order(self):
        rows = self._rows()
        reordered = dict(reversed(list(rows.items())))
        a = summarize_policies(rows)["policies"]["ppo=x.zip"]["contrasts"]
        b = summarize_policies(reordered)["policies"]["ppo=x.zip"]["contrasts"]
        self.assertEqual(a, b)

    def test_override_and_groups_share_the_reference(self):
        rows = self._rows()
        groups = {"all": [0, 1, 2, 3], "tail": [2, 3]}
        result = summarize_groups(rows, groups, main="all")
        self.assertEqual(result["best_heuristic"], "direct_flank")
        self.assertEqual(result["groups"]["tail"]["best_heuristic"], "direct_flank")
        self.assertEqual(result["groups"]["tail"]["policies"]["noop"]["episodes"], 2)
        forced = summarize_policies(rows, best_heuristic="protect_urban")
        self.assertEqual(forced["best_heuristic"], "protect_urban")


class AcceptanceTest(unittest.TestCase):
    """ADR-030 section 5: saved fraction decides, safety is non-inferiority, return does not."""

    def _rows(self, ppo_saved, ppo_calls=0, ppo_lost=0, n=40):
        flank = [row(0.10 + 0.01 * (i % 5), calls=1 if i < 4 else 0) for i in range(n)]
        ppo = [row(ppo_saved + 0.01 * (i % 5), calls=1 if i < ppo_calls else 0,
                   lost=1 if i < ppo_lost else 0) for i in range(n)]
        return {"noop": [row(0.0)] * n, "random": [row(0.01)] * n,
                "direct_flank": flank, "ppo=x.zip": ppo}

    def _block(self, rows):
        return summarize_policies(rows)["acceptance"]["ppo=x.zip"]

    def test_better_saved_and_no_worse_safety_passes(self):
        block = self._block(self._rows(0.15, ppo_calls=4))
        self.assertEqual(block["comparator"], "direct_flank")
        self.assertEqual(block["rule"], "ADR-030 section 5")
        self.assertGreater(block["primary"]["ci95"][0], 0)
        self.assertTrue(block["primary_pass"])
        self.assertEqual(block["safety"]["close_calls"], {"policy": 4, "comparator": 4,
                                                          "non_inferior": True})
        self.assertTrue(block["safety_pass"])
        self.assertTrue(block["pass"])
        self.assertFalse(block["return"]["decides_acceptance"])

    def test_more_close_calls_or_losses_fail_safety(self):
        for calls, lost in ((5, 0), (0, 1)):
            block = self._block(self._rows(0.15, ppo_calls=calls, ppo_lost=lost))
            self.assertTrue(block["primary_pass"])
            self.assertFalse(block["safety_pass"])
            self.assertFalse(block["pass"])

    def test_tied_saved_fails_even_with_a_higher_return(self):
        rows = self._rows(0.10)
        rows["direct_flank"] = [dict(r, **{"return": r["return"] - 0.3}) for r in rows["direct_flank"]]
        block = self._block(rows)
        self.assertGreater(block["return"]["mean"], 0.2)
        self.assertLessEqual(block["primary"]["ci95"][0], 0)
        self.assertFalse(block["primary_pass"])
        self.assertFalse(block["pass"])

    def test_only_learned_policies_are_candidates(self):
        summary = summarize_policies(self._rows(0.15))
        self.assertEqual(set(summary["acceptance"]), {"ppo=x.zip"})
        heuristics_only = {k: v for k, v in self._rows(0.15).items() if k != "ppo=x.zip"}
        self.assertEqual(summarize_policies(heuristics_only)["acceptance"], {})


class RealCaseGroupTest(unittest.TestCase):
    def test_no_edge_group_uses_noop_edge_and_crop(self):
        results = [
            ("a", {"split": "train"}, {"noop": row(0.0)}),
            ("b", {"split": "train"}, {"noop": row(0.0, noop_edge=True)}),
            ("c", {"split": "validation", "initial_cells_outside_crop": 3}, {"noop": row(0.0)}),
            ("d", {"split": "validation"}, {"noop": row(0.0)}),
        ]
        groups = real_case_groups(results)
        self.assertEqual(groups["ex_train"], [0, 1])
        self.assertEqual(groups["ex_validation"], [2, 3])
        self.assertEqual(groups["all"], [0, 1, 2, 3])
        self.assertEqual(groups["all_in_crop"], [0, 1, 3])
        self.assertEqual(groups["no_edge_in_crop"], [0, 3])


if __name__ == "__main__":
    unittest.main()
