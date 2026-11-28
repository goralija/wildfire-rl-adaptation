import unittest

try:
    import numpy as np
except ImportError:
    np = None


@unittest.skipIf(np is None, 'NumPy optional')
class RobustnessTests(unittest.TestCase):
    def setUp(self):
        from wildfire_rl import action_value_robustness
        self.m = action_value_robustness

    def test_physical_replicates_are_averaged_within_fire_after_percentages(self):
        saved = np.array([[10., 0.], [10., 0.]])
        noop = np.array([[100., 100.], [10., 100.]])
        r = self.m.summarize(saved, noop, np.zeros((2, 2, 1)), np.ones(2, bool))
        self.assertEqual(r['n'], 2)
        self.assertAlmostEqual(r['mean_saved_percent'], 27.5)
        self.assertAlmostEqual(r['pooled_saved_percent_all'], 20/310*100)
        self.assertAlmostEqual(r['mean_saved_ha_all'], 16.2)

    def test_duplicating_same_spread_does_not_narrow_fire_uncertainty(self):
        saved = np.array([[1., 5., 20.]])
        noop = np.full((1, 3), 100.)
        refs = np.full((1, 3, 2), 5.)
        a = self.m.summarize(saved, noop, refs, np.ones(3, bool))
        b = self.m.summarize(np.repeat(saved, 3, 0), np.repeat(noop, 3, 0),
                             np.repeat(refs, 3, 0), np.ones(3, bool))
        self.assertEqual(a['delta_best_ci95_pp'], b['delta_best_ci95_pp'])
        self.assertEqual(b['n'], 3)

    def test_joint_zero_in_one_spread_is_excluded_only_from_percentages(self):
        r = self.m.summarize(np.array([[5., 0.], [5., 1.]]), np.array([[10., 0.], [10., 10.]]),
                             np.zeros((2, 2, 1)), np.ones(2, bool))
        self.assertEqual(r['n'], 1)
        self.assertEqual(r['primary_mask'], [True, False])
        self.assertAlmostEqual(r['mean_saved_ha_all'], 2.75*3.24)

    def test_bad_denominators_or_shapes_are_rejected(self):
        with self.assertRaises(ValueError):
            self.m.summarize(np.ones((1, 2)), np.zeros((1, 2)), np.zeros((1, 2, 1)), np.ones(2, bool))
        with self.assertRaises(ValueError):
            self.m.summarize(np.ones((1, 2)), np.ones((2, 2)), np.zeros((1, 2, 1)), np.ones(2, bool))

    def test_held_out_fire_cannot_change_fitted_weights_or_selected_reference(self):
        rng = np.random.default_rng(2)
        x = rng.normal(size=(4, 8, 2)); y = rng.normal(size=(4, 8))
        masks = np.ones((4, 9), bool); eligible = np.ones(4, bool)
        refs = np.array([[0., 1.], [0., 2.], [0., 2.], [100., -100.]])
        a, ids, baseline = self.m.fit_fold(x, y, masks, eligible, ['a', 'b', 'c', 'd'], 'd', refs)
        x[3] *= 1e6; y[3] *= -1e6; refs[3] *= -1e6
        b, ids2, baseline2 = self.m.fit_fold(x, y, masks, eligible, ['a', 'b', 'c', 'd'], 'd', refs)
        self.assertEqual(ids, ['a', 'b', 'c']); self.assertEqual(ids2, ids)
        self.assertEqual(baseline, 1); self.assertEqual(baseline2, baseline)
        for key in a: np.testing.assert_array_equal(a[key], b[key])

    def test_ineligible_training_fire_is_not_fitted(self):
        x = np.zeros((4, 8, 2)); masks = np.ones((4, 9), bool)
        _, ids, _ = self.m.fit_fold(x, np.zeros((4, 8)), masks, np.array([True, False, True, True]),
                                   ['a', 'b', 'c', 'd'], 'd', np.zeros((4, 2)))
        self.assertEqual(ids, ['a', 'c'])

    def test_sensitivity_reselects_reference_after_each_fire_deletion(self):
        r = self.m.summarize(np.array([[10., 10., 10.]]), np.full((1, 3), 100.),
                             np.array([[[25., 0.], [0., 25.], [0., 0.]]]), np.ones(3, bool))
        self.assertAlmostEqual(r['delete_one_effect_delta_range_pp'][0], -2.5)
        self.assertAlmostEqual(r['delete_one_effect_delta_range_pp'][1], -2.5)
