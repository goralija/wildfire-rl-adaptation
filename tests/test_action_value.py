import unittest
try:
    import numpy as np
except ImportError:
    np = None


@unittest.skipIf(np is None, 'NumPy optional')
class ActionValueTests(unittest.TestCase):
    def setUp(self):
        from wildfire_rl import action_value
        self.m = action_value

    def test_split_rejects_leakage_and_duplicates(self):
        for a, b in [(['a'], ['a']), (['a', 'a'], ['b']), ([], ['b'])]:
            with self.assertRaises(ValueError): self.m.validate_split(a, b)
        self.m.validate_split(['a', 'b'], ['c'])

    def test_shared_features_follow_candidate_and_keep_input_unchanged(self):
        obs = np.zeros(536)
        obs[162 + 37 * 3 + 23] = .75
        before = obs.copy(); x = self.m.action_features(obs)
        self.assertEqual(x.shape[0], 8)
        self.assertEqual(np.flatnonzero(x[:, 23]).tolist(), [3])
        np.testing.assert_array_equal(obs, before)
        with self.assertRaises(ValueError): self.m.action_features(np.zeros(535))

    def test_each_fire_has_equal_weight_with_unequal_legal_actions(self):
        mask = np.zeros((2, 9), bool); mask[:, 0] = True
        mask[0, 1] = True; mask[1, 1:] = True
        w = self.m.fitting_weights(mask)
        np.testing.assert_allclose(w.sum(axis=1), [1., 1.])
        self.assertEqual(w[0, 0], 1.); self.assertEqual(w[1, 0], .125)
        mask[0] = False
        with self.assertRaises(ValueError): self.m.fitting_weights(mask)

    def test_fit_only_scaler_and_learned_direction(self):
        x = np.zeros((4, 8, 2)); x[:, :, 0] = np.arange(8); x[2:, :, 0] = -np.arange(1, 9)
        masks = np.ones((4, 9), bool)
        model = self.m.fit_ridge(x, x[:, :, 0] / 10, masks, alpha=10.)
        self.assertEqual(self.m.select_action(model, x[0], masks[0]), 8)
        self.assertEqual(self.m.select_action(model, x[2], masks[2]), 0)
        scaler = model['mean'].copy()
        self.m.select_action(model, x[0] * 10000, masks[0])
        np.testing.assert_array_equal(scaler, model['mean'])

    def test_illegal_high_value_is_ignored_and_noop_stays_available(self):
        model = dict(mean=np.zeros(1), scale=np.ones(1), coef=np.array([0., 1.]))
        x = np.arange(8).reshape(8, 1); mask = np.ones(9, bool); mask[8] = False
        self.assertEqual(self.m.select_action(model, x, mask), 7)
        self.assertEqual(self.m.select_action(model, -x, mask), 0)
        mask[0] = False
        with self.assertRaises(ValueError): self.m.select_action(model, x, mask)

    def test_joint_zero_is_not_a_percent_and_all_fires_stay_in_ha(self):
        r = self.m.compare(np.array([20., 0.]), np.array([100., 0.]),
                           np.array([[10., 0.], [15., 0.]]), np.array([True, False]))
        self.assertEqual(r['n'], 1); self.assertEqual(r['mean_saved_percent'], 20.)
        self.assertAlmostEqual(r['mean_saved_ha_all'], 32.4); self.assertTrue(r['better'])
        with self.assertRaises(ValueError):
            self.m.compare(np.ones(2), np.zeros(2), np.ones((2, 2)), np.ones(2, bool))

    def test_near_uses_ratio_and_uncertainty(self):
        refs = np.full((2, 4), 10.)
        r = self.m.compare(np.full(4, 9.), np.full(4, 100.), refs, np.ones(4, bool))
        self.assertTrue(r['near']); self.assertFalse(r['better'])
        self.assertEqual(r['delta_best_ci95_pp'], [-1., -1.])
        r = self.m.compare(np.array([0., 20., 20., 0.]), np.full(4, 100.), refs, np.ones(4, bool))
        self.assertEqual(r['ratio_to_best'], 1.); self.assertFalse(r['near'])

    def test_bootstrap_reselects_strongest_reference_per_draw(self):
        r = self.m.compare(np.array([7., 7.]), np.full(2, 100.),
                           np.array([[10., 0.], [0., 10.]]), np.ones(2, bool))
        np.testing.assert_allclose(r['delta_best_ci95_pp'], [-3., 2.])
        self.assertFalse(r['better'])

    def test_nonfinite_or_impossible_damage_is_rejected(self):
        with self.assertRaises(ValueError):
            self.m.compare(np.ones(2), np.zeros(2), np.ones((2, 2)), np.ones(2, bool))
        with self.assertRaises(ValueError): self.m.action_features(np.full(536, np.nan))

    def test_encoded_reference_geometry(self):
        obs = np.zeros(536); obs[1:3] = [0., 1.]
        obs[4:6] = [1., 1.]; obs[160:162] = [1., 0.]
        refs = self.m.reference_actions(obs, np.ones(9, bool))
        self.assertEqual(refs['downwind'], 7); self.assertEqual(refs['advancing_front64'], 1)

    def test_front_reference_when_legacy_burned_is_empty(self):
        obs = np.zeros(536); obs[1:3] = [0., 1.]
        obs[5] = .01; obs[160:162] = [-.01, .01]
        refs = self.m.reference_actions(obs, np.ones(9, bool))
        self.assertEqual(refs['advancing_front64'], 4)
