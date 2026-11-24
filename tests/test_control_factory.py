import unittest
from unittest.mock import patch
try:
    import numpy
    import gymnasium
except ImportError as exc:
    raise unittest.SkipTest(str(exc))
from wildfire_rl.control_factory import native_env,spread_seed


class ControlFactoryTests(unittest.TestCase):
    def test_invalid_backend_or_replicate_rejected_before_input_access(self):
        with patch('wildfire_rl.control_factory.load_case_inputs') as load:
            for backend,rep in [('unknown',0),('ca',-1),('simfire',1)]:
                with self.assertRaises(ValueError):native_env(backend,'fixture',spread_replicate=rep)
            load.assert_not_called()

    def test_case_loader_is_always_train_only(self):
        with patch('wildfire_rl.control_factory.load_case_inputs',side_effect=ValueError('sentinel')) as load:
            with self.assertRaisesRegex(ValueError,'sentinel'):native_env('ca','fixture')
            self.assertEqual(load.call_args.kwargs['split'],'train')

    def test_case_seed_is_stable_and_replicates_distinct(self):
        self.assertEqual(spread_seed('fixture',0),spread_seed('fixture',0))
        self.assertNotEqual(spread_seed('fixture',0),spread_seed('fixture',1))
        self.assertGreaterEqual(spread_seed('fixture',0),0)
        self.assertLess(spread_seed('fixture',0),2**31)
