import json
import tempfile
from pathlib import Path
import unittest

from wildfire_rl.firehose_probe import (
    budget_action,
    cells_with_state,
    history_damage,
    input_tree_hash,
    override_seed,
    parse_terminal_state,
    terminal_damage_matches_grid_history,
    weather_horizon,
)


class FirehoseProbeTests(unittest.TestCase):
    def test_budget_switches_to_legacy_noop_after_exactly_b_requests(self):
        self.assertEqual([budget_action(17, used, 2) for used in range(4)],
                         [17, 17, -1, -1])
        self.assertEqual(budget_action(17, 0, 0), -1)

    def test_seed_override_is_explicit_and_preserves_other_arguments(self):
        self.assertEqual(override_seed('C2F --seed 123 --nthreads 1', 124),
                         'C2F --seed 124 --nthreads 1')
        with self.assertRaises(ValueError):
            override_seed('C2F --seed 12', 124)

    def test_grid_history_keeps_previously_affected_cells_after_treatment(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / 'ForestGrid00.csv'
            last = Path(tmp) / 'ForestGrid01.csv'
            first.write_text('0,1\n0,0\n')
            last.write_text('0,-1\n1,0\n')
            self.assertEqual(history_damage([first, last]), {1, 2})

    def test_input_hash_ignores_temporary_path_but_tracks_ignition_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a', Path(tmp) / 'b'
            a.mkdir()
            b.mkdir()
            for root in (a, b):
                (root / 'Ignitions.csv').write_text('Year,Ncell\n1,372\n')
            self.assertEqual(input_tree_hash(a), input_tree_hash(b))
            (b / 'Ignitions.csv').write_text('Year,Ncell\n1,381\n')
            self.assertNotEqual(input_tree_hash(a), input_tree_hash(b))

    def test_weather_horizon_uses_weather_rows_not_policy_action_interval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Weather.csv'
            path.write_text('Scenario,datetime,WS\ncase,00:00,2\ncase,01:00,3\n')
            self.assertEqual(weather_horizon(path), (2, 120))

    def test_weather_horizon_rejects_empty_file_and_invalid_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'Weather.csv'
            path.write_text('')
            with self.assertRaises(ValueError):
                weather_horizon(path)
            path.write_text('Scenario,datetime,WS\n')
            with self.assertRaises(ValueError):
                weather_horizon(path, minutes_per_weather_row=0)

    def test_cell_exports_are_one_based_row_major_and_keep_front_distinct(self):
        grid = [[1, 2], [-1, 0]]
        self.assertEqual(cells_with_state(grid, {1, 2}), [1, 2])
        self.assertEqual(cells_with_state(grid, {2}), [2])
        self.assertEqual(cells_with_state(grid, {-1}), [3])

    def test_terminal_record_validates_reason_ids_and_cumulative_front(self):
        record = {
            'schema': 'firehose-terminal-state-v1',
            'reason': 'weather_horizon',
            'cell_id_base': 1,
            'active_front_ncells': [3],
            'ever_affected_ncells': [1, 2, 3],
            'treated_ncells': [2],
            'available_cell_count': 1,
            'total_cell_count': 4,
            'fire_period': 8,
            'weather_period': 1,
        }
        line = 'FIREHOSE_TERMINAL_STATE ' + json.dumps(record)
        self.assertEqual(parse_terminal_state(['ordinary log', line]), record)
        self.assertIsNone(parse_terminal_state(['ordinary log']))
        for reason in ('weather_horizon', 'front_extinguished', 'grid_exhausted', 'no_ignition'):
            candidate = dict(record, reason=reason)
            self.assertEqual(
                parse_terminal_state(['FIREHOSE_TERMINAL_STATE ' + json.dumps(candidate)]),
                candidate,
            )
        with self.assertRaises(ValueError):
            parse_terminal_state([line, line])
        record['ever_affected_ncells'] = [1, 2, 5]
        with self.assertRaises(ValueError):
            parse_terminal_state(['FIREHOSE_TERMINAL_STATE ' + json.dumps(record)])
        record['ever_affected_ncells'] = [1, 2, 3]
        record['active_front_ncells'] = [4]
        with self.assertRaises(ValueError):
            parse_terminal_state(['FIREHOSE_TERMINAL_STATE ' + json.dumps(record)])

    def test_terminal_damage_explains_cells_hidden_by_treatment(self):
        terminal = {
            'ever_affected_ncells': [1, 2, 3],
            'treated_ncells': [2],
        }
        self.assertTrue(terminal_damage_matches_grid_history(terminal, {1, 3}))
        self.assertFalse(terminal_damage_matches_grid_history(terminal, {1, 4}))
        self.assertFalse(terminal_damage_matches_grid_history(
            {'ever_affected_ncells': [1, 2, 3], 'treated_ncells': []}, {1, 3}
        ))

    def test_cell_export_rejects_ragged_grids(self):
        with self.assertRaises(ValueError):
            cells_with_state([[0, 1], [2]], {1})
