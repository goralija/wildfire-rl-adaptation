import copy
from datetime import datetime, timedelta
import unittest

try:
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest(str(exc))

from wildfire_rl.observed_growth_audit import (
    growth_metrics, summarize_endpoint, validate_time_alignment,
    rasterize_observation, observed_envelope,
)


def time_fixture():
    from wildfire_rl.gridmet_weather import feds_overpass_utc
    times = [(datetime(2018, 8, 3, 12) + timedelta(hours=12*k)).isoformat() for k in range(5)]
    case = {'scenario_id': 'fixture', 'split': 'train', 'event': {'year': 2018},
            'evaluation_reference': {'initial_state_time': times[0],
                                     'observed_state_times_0_to_48h': times}}
    moments = [feds_overpass_utc(t, -112.5) for t in times]
    weather = {'split': 'train', 'initial_state_time': times[0],
               'weather_sample_location': {'longitude': -112.5},
               'segments': [{'start_utc': a.isoformat(), 'end_utc': b.isoformat()}
                            for a, b in zip(moments, moments[1:])]}
    return case, weather


class ObservedGrowthTest(unittest.TestCase):
    def test_new_growth_excludes_large_prior_and_preserves_false_growth(self):
        initial = np.ones((8, 8), bool); initial[-1] = False
        target = initial.copy(); target[-1, :2] = True
        pred = initial.copy(); pred[-1, 1:4] = True
        r = growth_metrics(initial, pred, target)
        self.assertEqual((r['predicted_growth_cells'], r['observed_growth_cells']), (3, 2))
        self.assertEqual(r['growth_iou'], .25)
        self.assertAlmostEqual(r['absolute_new_area_error_ha'], 3.24)
        self.assertAlmostEqual(r['new_area_ratio'], 1.5)

    def test_zero_observation_is_not_epsilon_or_perfect_iou(self):
        a = np.zeros((3, 3), bool); a[1, 1] = True
        same = growth_metrics(a, a, a)
        self.assertIsNone(same['growth_iou']); self.assertIsNone(same['new_area_ratio'])
        pred = a.copy(); pred[1, 2] = True
        r = growth_metrics(a, pred, a)
        self.assertEqual(r['growth_iou'], 0.)
        self.assertIsNone(r['relative_new_area_error_percent'])
        self.assertAlmostEqual(r['absolute_new_area_error_ha'], 3.24)

    def test_nonbinary_nonfinite_or_lost_prior_prediction_is_refused(self):
        a = np.zeros((3, 3), bool); a[1, 1] = True
        for pred in [np.zeros_like(a), np.full(a.shape, np.nan), np.full(a.shape, 2)]:
            with self.assertRaises(ValueError): growth_metrics(a, pred, a)
        # The observed perimeter may shrink: report it rather than deleting prior damage.
        r = growth_metrics(a, a, np.zeros_like(a))
        self.assertEqual(r['observed_missing_initial_cells'], 1)

    def test_time_uses_local_solar_mapping_and_rejects_naive_utc(self):
        case, weather = time_fixture()
        r = validate_time_alignment(case, weather)
        self.assertEqual(r['status'], 'PASS')
        self.assertIn('21:00:00', r['utc_times'][0])
        broken = copy.deepcopy(weather)
        broken['segments'][0]['start_utc'] = case['evaluation_reference']['initial_state_time'] + '+00:00'
        with self.assertRaises(ValueError): validate_time_alignment(case, broken)
        broken = copy.deepcopy(case)
        broken['evaluation_reference']['observed_state_times_0_to_48h'][2] = '2018-08-05T00:00:00'
        with self.assertRaises(ValueError): validate_time_alignment(broken, weather)

    def test_nontrain_is_refused_before_geometry_access(self):
        case, weather = time_fixture()
        for split in ('validation', 'test'):
            bad = copy.deepcopy(case); bad['split'] = split
            with self.assertRaises(ValueError): validate_time_alignment(bad, weather)
            with self.assertRaises(ValueError): rasterize_observation(bad, {}, None)

    def test_replicates_are_averaged_inside_paired_fire_and_missing_is_not_zero(self):
        initial = np.zeros((5, 5), bool); initial[0, 0] = True
        def score(n, obs):
            p = initial.copy(); p.flat[1:1+n] = True
            t = initial.copy(); t.flat[1:1+obs] = True
            return growth_metrics(initial, p, t)
        rows = []
        for sid, obs, counts in [('a', 2, (2, 0, 2, 4)), ('b', 0, (0, 1, 1, 1))]:
            metrics = {m: score(n, obs) for m, n in zip(('simfire','ca0','ca1','ca2'), counts)}
            rows.append({'scenario_id': sid, 'complete': True, 'fully_covered': True,
                         'metrics': {'raw': {'48': metrics}}})
        rows.append({'scenario_id': 'missing', 'complete': False})
        s = summarize_endpoint(rows, methods=('simfire','ca0','ca1','ca2','ca_mean3'))
        self.assertEqual(s['complete_ids'], ['a','b'])
        self.assertEqual(s['observed_positive_ids'], ['a'])
        self.assertEqual(s['missing_ids'], ['missing'])
        # mean(0,1,.5)=.5; thresholding a mean mask or pooling cells gives another value.
        self.assertAlmostEqual(s['methods']['ca_mean3']['mean_growth_iou'], .5)
        self.assertAlmostEqual(s['methods']['ca_mean3']['mean_absolute_new_area_error_ha'], 3.78)
        self.assertEqual(s['methods']['ca_mean3']['stalled_cases_with_predicted_growth'], 1.)
        self.assertAlmostEqual(s['contrasts']['ca_mean3_minus_simfire']['growth_iou']['mean'], -.5)

    def test_envelope_preserves_intermediate_growth_and_missing_is_explicit(self):
        a = np.zeros((3,3), bool); a[0,0] = True
        b = a.copy(); b[1,1] = True
        env = observed_envelope([a,b,a])
        self.assertTrue(env[-1][1,1])
        with self.assertRaises(ValueError): observed_envelope([a,None,a])

    def test_scoring_cannot_open_future_feds_before_both_prediction_cohorts(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts import audit_paired_observed_growth as runner
        case, _ = time_fixture()
        with tempfile.TemporaryDirectory() as folder, patch.object(runner,'observations') as obs:
            with self.assertRaises(FileNotFoundError):
                runner.score(Path(folder), {}, {}, [case], {})
            obs.assert_not_called()

    def test_time_pooled_replicates_average_ratios_before_case_aggregation(self):
        from scripts.audit_paired_observed_growth import time_pooled
        def metric(hits, pred):
            return {'growth_intersection_cells':hits, 'predicted_growth_cells':pred,
                    'observed_growth_cells':2}
        methods = {'simfire':metric(2,2),'ca0':metric(0,0),'ca1':metric(2,2),
                   'ca2':metric(2,4),'persistence':metric(0,0),'ellipse':metric(1,1)}
        row = {'scenario_id':'x','complete':True,
               'metrics':{'raw':{str(h):methods for h in (12,24,36,48)}}}
        result = time_pooled([row],'raw')
        self.assertEqual(result['case_ids'],['x'])
        self.assertAlmostEqual(result['mean_case_time_pooled_iou']['ca_mean3'],.5)


try:
    from shapely.geometry import box
    import rasterio
except ImportError:
    HAS_GEO = False
else:
    HAS_GEO = True
try:
    import fiona
except ImportError:
    HAS_FIONA = False
else:
    HAS_FIONA = True


@unittest.skipUnless(HAS_GEO, 'Optional GIS stack required')
class ObservationRasterTest(unittest.TestCase):
    @unittest.skipUnless(HAS_FIONA, 'Optional Fiona reader required')
    def test_full_exact_time_parts_include_a_component_outside_the_grid(self):
        from unittest.mock import patch
        from shapely.geometry import mapping
        from wildfire_rl.observed_growth_audit import read_geometry_parts
        case, _ = time_fixture(); case['evaluation_reference']['source_fire_id'] = '7'
        times = case['evaluation_reference']['observed_state_times_0_to_48h']
        features = [{'properties': {'fireID': 7, 't': t}, 'geometry': mapping(geom)}
                    for t in times for geom in (box(0,0,1,1), box(20,20,21,21))]
        class Source:
            crs_wkt = 'EPSG:32612'
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def __iter__(self): return iter(features)
            def filter(self, **kwargs): raise AssertionError('bbox could hide an outside component')
        with patch('fiona.open', return_value=Source()):
            data = read_geometry_parts([case], {2018: 'unused'})
        self.assertEqual([len(s['parts']) for s in data['fixture']], [2]*5)

    def test_complete_geometry_coverage_is_separate_from_clipped_mask(self):
        case, _ = time_fixture()
        grid = {'shape': [4,4], 'crs':'EPSG:32612', 'raster_transform':[1,0,0,0,-1,4]}
        r = rasterize_observation(case, grid, box(3,1,5,2))
        self.assertEqual(r['status'], 'ok')
        self.assertTrue(r['mask'].any()); self.assertFalse(r['fully_covered'])
        self.assertAlmostEqual(r['outside_area_m2'], 1.)
        self.assertAlmostEqual(r['outside_fraction'], .5)

    def test_missing_or_invalid_geometry_never_becomes_stalled_fire(self):
        case, _ = time_fixture()
        grid = {'shape': [4,4], 'crs':'EPSG:32612', 'raster_transform':[1,0,0,0,-1,4]}
        r = rasterize_observation(case, grid, None)
        self.assertEqual(r['status'], 'missing'); self.assertIsNone(r['mask'])
        from shapely.geometry import Polygon
        invalid = Polygon([(0,0),(2,2),(0,2),(2,0),(0,0)])
        r = rasterize_observation(case, grid, invalid)
        self.assertEqual(r['status'], 'invalid'); self.assertIsNone(r['mask'])


if __name__ == '__main__': unittest.main()
