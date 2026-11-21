"""Post-hoc TRAIN growth diagnostics; no simulator or policy is fitted here."""

from datetime import datetime, timedelta, timezone
import numpy as np

from .gridmet_weather import feds_overpass_utc


METHODS = ('simfire', 'ca0', 'ca1', 'ca2', 'ca_mean3', 'persistence', 'ellipse')


def require_train(case):
    if case.get('split') != 'train' or case.get('event', {}).get('year') not in (2018, 2019):
        raise ValueError('Only selected TRAIN2018/2019 cases are permitted')


def validate_time_alignment(case, weather):
    """Check labels and all forcing boundaries using the established solar-time rule."""
    require_train(case)
    reference = case['evaluation_reference']
    labels = reference['observed_state_times_0_to_48h']
    if (len(labels) != 5 or labels[0] != reference['initial_state_time']
            or weather.get('split') != 'train'
            or weather.get('initial_state_time') != labels[0]):
        raise ValueError('Five matching TRAIN comparison labels required')
    parsed = [datetime.fromisoformat(t) for t in labels]
    if any(t.tzinfo is not None for t in parsed) or any(
            t != parsed[0] + timedelta(hours=12*k) for k, t in enumerate(parsed)):
        raise ValueError('FEDS labels must be naive and exactly12h apart')
    longitude = float(weather['weather_sample_location']['longitude'])
    utc = [feds_overpass_utc(t, longitude) for t in labels]
    segments = weather['segments']
    if len(segments) != 4:
        raise ValueError('Four forcing segments required')
    deviations = []
    for k, segment in enumerate(segments):
        for field, expected in [('start_utc', utc[k]), ('end_utc', utc[k+1])]:
            actual = datetime.fromisoformat(segment[field])
            if actual.tzinfo is None:
                raise ValueError('Forcing timestamps require a timezone')
            deviations.append(abs((actual.astimezone(timezone.utc)-expected).total_seconds()))
    if max(deviations) > .001:
        raise ValueError('FEDS overpass and forcing boundaries disagree')
    return {'status': 'PASS', 'feds_labels': labels,
            'utc_times': [t.isoformat() for t in utc], 'longitude': longitude,
            'max_segment_boundary_error_seconds': max(deviations)}


def _mask(values):
    a = np.asarray(values)
    if (a.ndim != 2 or not a.size or not np.isfinite(a).all()
            or not np.isin(a, [0, 1]).all()):
        raise ValueError('Finite binary nonempty2D mask required')
    return a.astype(bool)


def growth_metrics(initial, predicted, observed, resolution=180.):
    initial, predicted, observed = map(_mask, (initial, predicted, observed))
    if initial.shape != predicted.shape or observed.shape != initial.shape:
        raise ValueError('All masks must have the same shape')
    if np.any(initial & ~predicted):
        raise ValueError('Prediction lost cumulative initial damage')
    # binary_burn_metrics rejects empty full observed masks. Growth-only empty targets
    # are valid here; use counts directly while keeping the same overlap definitions.
    from .feds_spread_metrics import growth_overlap_metrics
    if not np.isfinite(resolution) or resolution <= 0:
        raise ValueError('Positive finite resolution required')
    p, o = predicted & ~initial, observed & ~initial
    pc, oc, hit = int(p.sum()), int(o.sum()), int((p & o).sum())
    hectares = resolution**2 / 10000.
    return {'predicted_growth_cells': pc, 'observed_growth_cells': oc,
            'growth_intersection_cells': hit,
            **growth_overlap_metrics(hit, pc, oc),
            'predicted_new_area_ha': pc*hectares, 'observed_new_area_ha': oc*hectares,
            'signed_new_area_error_ha': (pc-oc)*hectares,
            'absolute_new_area_error_ha': abs(pc-oc)*hectares,
            'new_area_ratio': pc/oc if oc else None,
            'relative_new_area_error_percent': 100.*(pc-oc)/oc if oc else None,
            'observed_missing_initial_cells': int((initial & ~observed).sum()),
            'observed_total_cells': int(observed.sum()), 'initial_cells': int(initial.sum()),
            'false_growth_when_stalled': int(oc == 0 and pc > 0)}


def observed_envelope(masks):
    if not masks or any(m is None for m in masks):
        raise ValueError('Complete observations required; missing is not zero')
    arrays = [_mask(m) for m in masks]
    if any(m.shape != arrays[0].shape for m in arrays):
        raise ValueError('Observation masks must share a grid')
    return [m.copy() for m in np.logical_or.accumulate(arrays)]


def rasterize_observation(case, grid, geometry):
    """Rasterize complete projected geometry, retaining missing/invalid/coverage flags."""
    require_train(case)  # Before optional imports or geometry access.
    if geometry is None:
        return {'status': 'missing', 'mask': None, 'fully_covered': False}
    if geometry.is_empty or not geometry.is_valid or geometry.area <= 0:
        return {'status': 'invalid', 'mask': None, 'fully_covered': False}
    from affine import Affine
    from rasterio.features import rasterize
    from rasterio.transform import array_bounds
    from shapely.geometry import box
    height, width = grid['shape']
    transform = Affine(*grid['raster_transform'][:6])
    extent = box(*array_bounds(height, width, transform))
    outside = float(geometry.difference(extent).area)
    mask = rasterize([(geometry, 1)], out_shape=(height, width), transform=transform,
                     fill=0, all_touched=True, dtype='uint8').astype(bool)
    return {'status': 'ok', 'mask': mask, 'fully_covered': outside <= 1e-6,
            'vector_area_m2': float(geometry.area), 'outside_area_m2': outside,
            'outside_fraction': outside/float(geometry.area),
            'raster_cells': int(mask.sum()),
            'edge_contact': bool(mask[0].any() or mask[-1].any()
                                 or mask[:,0].any() or mask[:,-1].any())}


def read_geometry_parts(cases, archive_paths):
    """One full TRAIN annual pass, retaining every part of selected exact-time states."""
    for case in cases:
        require_train(case)
    import fiona
    from shapely.geometry import shape
    result = {}
    for year in sorted({c['event']['year'] for c in cases}):
        selected = [c for c in cases if c['event']['year'] == year]
        wanted = {}
        for case in selected:
            states = []
            for timestamp in case['evaluation_reference']['observed_state_times_0_to_48h']:
                state = {'timestamp': timestamp, 'parts': []}
                states.append(state)
                key = (str(int(case['evaluation_reference']['source_fire_id'])), timestamp)
                if key in wanted:
                    raise ValueError('Ambiguous duplicate fire/time in selected cases')
                wanted[key] = state
            result[case['scenario_id']] = states
        with fiona.open(archive_paths[year]) as source:
            crs = source.crs_wkt or source.crs or 'EPSG:9311'
            for state in wanted.values(): state['source_crs'] = crs
            for feature in source:
                properties = feature['properties']
                if properties.get('fireID') is None or properties.get('t') is None:
                    continue
                key = (str(int(properties['fireID'])), str(properties['t']))
                if key in wanted and feature.get('geometry'):
                    wanted[key]['parts'].append(shape(feature['geometry']))
    return result


def _metric(row, method, kind, horizon):
    data = row['metrics'][kind][str(horizon)]
    if method != 'ca_mean3':
        return data[method]
    replicas = [data['ca'+str(k)] for k in range(3)]
    return {key: (float(np.mean([r[key] for r in replicas]))
                  if all(r[key] is not None for r in replicas) else None)
            for key in replicas[0]}


def paired_contrast(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.ndim != 1 or a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Same finite paired cases required')
    if not len(a):
        return {'cases': 0, 'mean': None, 'ci95': None}
    delta = a-b
    indices = np.random.default_rng(0).integers(len(a), size=(10000, len(a)))
    return {'cases': len(a), 'mean': float(delta.mean()),
            'ci95': np.quantile(delta[indices].mean(axis=1), [.025,.975]).tolist()}


def summarize_endpoint(rows, *, kind='raw', horizon=48, fully_covered=False,
                       methods=METHODS):
    """Equal weight per fire; average scalar metrics within fire over CA replicas."""
    ids = [r['scenario_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate case, not an independent replica')
    complete = [r for r in rows if r['complete'] and (not fully_covered or r['fully_covered'])]
    values = {m: [_metric(r,m,kind,horizon) for r in complete] for m in methods}
    reference = values['simfire']
    for method, records in values.items():
        if any(a['observed_growth_cells'] != b['observed_growth_cells']
               for a,b in zip(reference,records)):
            raise ValueError('Methods must share observed targets')
    positive = [k for k,r in enumerate(reference) if r['observed_growth_cells'] > 0]
    stalled = [k for k,r in enumerate(reference) if r['observed_growth_cells'] == 0]
    def mean(x): return float(np.mean(x)) if len(x) else None
    summary = {}
    for method, records in values.items():
        predicted = sum(r['predicted_growth_cells'] for r in records)
        observed = sum(r['observed_growth_cells'] for r in records)
        hits = sum(r['growth_intersection_cells'] for r in records)
        summary[method] = {
            'mean_growth_iou': mean([records[k]['growth_iou'] for k in positive]),
            'mean_absolute_new_area_error_ha': mean([r['absolute_new_area_error_ha'] for r in records]),
            'mean_signed_new_area_error_ha': mean([r['signed_new_area_error_ha'] for r in records]),
            'mean_predicted_new_area_ha': mean([r['predicted_new_area_ha'] for r in records]),
            'mean_observed_new_area_ha': mean([r['observed_new_area_ha'] for r in records]),
            'mean_new_area_ratio_observed_positive': mean([records[k]['new_area_ratio'] for k in positive]),
            'median_new_area_ratio_observed_positive': (float(np.median([records[k]['new_area_ratio'] for k in positive])) if positive else None),
            'pooled_area_ratio': predicted/observed if observed else None,
            'pooled_growth_precision': hits/predicted if predicted else None,
            'pooled_growth_recall': hits/observed if observed else None,
            'stalled_cases': len(stalled),
            'stalled_cases_with_predicted_growth': sum(records[k]['false_growth_when_stalled'] for k in stalled),
            'mean_false_new_area_ha_when_stalled': mean([records[k]['predicted_new_area_ha'] for k in stalled]),
        }
    contrasts = {}
    for method in methods:
        if method == 'simfire': continue
        records = values[method]
        contrasts[method+'_minus_simfire'] = {
            'growth_iou': paired_contrast([records[k]['growth_iou'] for k in positive],
                                         [reference[k]['growth_iou'] for k in positive]),
            'absolute_new_area_error_ha': paired_contrast(
                [r['absolute_new_area_error_ha'] for r in records],
                [r['absolute_new_area_error_ha'] for r in reference]),
        }
    return {'kind':kind, 'horizon':horizon, 'fully_covered_only':fully_covered,
            'complete_ids':[r['scenario_id'] for r in complete],
            'observed_positive_ids':[complete[k]['scenario_id'] for k in positive],
            'missing_ids':[r['scenario_id'] for r in rows if not r['complete']],
            'excluded_censored_ids':[r['scenario_id'] for r in rows if r['complete'] and fully_covered and not r['fully_covered']],
            'methods':summary, 'contrasts':contrasts}
