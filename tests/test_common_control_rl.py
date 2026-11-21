import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

try:
    import torch
    import sb3_contrib
    import numpy as np
except ImportError as exc:
    raise unittest.SkipTest('optional SB3/Torch required: %s' % exc)

from test_common_control import environment
from wildfire_rl.common_control_rl import create_model, save_policy_arrays, load_policy_arrays, policy_digest


class CommonPPOTests(unittest.TestCase):
    def test_identical_initialization_masked_learning_and_safe_roundtrip(self):
        torch.set_num_threads(1)
        a=create_model(environment(),seed=17)
        b=create_model(environment(),seed=17)
        self.assertEqual(policy_digest(a),policy_digest(b))
        before=policy_digest(a)
        a.learn(16)
        self.assertNotEqual(before,policy_digest(a))
        self.assertEqual(a.num_timesteps,16)
        self.assertTrue(all(np.isfinite(v) for v in a.logger.name_to_value.values()
                            if isinstance(v,(float,int))))
        env=environment();obs,_=env.reset();mask=env.action_masks()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'policy.npz';contract={'plan':'test','backend':'fake'}
            save_policy_arrays(a,path,contract)
            rng=(random.getstate(),np.random.get_state(),torch.random.get_rng_state().clone())
            restored=load_policy_arrays(path,contract)
            self.assertEqual(rng[0],random.getstate())
            np.testing.assert_equal(rng[1],np.random.get_state())
            self.assertTrue(torch.equal(rng[2],torch.random.get_rng_state()))
            self.assertEqual(policy_digest(a),policy_digest(restored))
            for _ in range(4):
                mask=env.action_masks()
                action=int(a.predict(obs,action_masks=mask,deterministic=True)[0])
                self.assertTrue(mask[action])
                self.assertEqual(action,int(restored.predict(obs,action_masks=mask,deterministic=True)[0]))
                obs,_,_,_,_=env.step(action)
            with patch('numpy.load',side_effect=AssertionError('guard must run first')):
                with self.assertRaises(ValueError):load_policy_arrays(path,{'plan':'other'})
            with path.open('ab') as f:f.write(b'tamper')
            with self.assertRaises(ValueError):load_policy_arrays(path,contract)

    def test_receipt_tensor_manifest_is_checked(self):
        model=create_model(seed=29)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'policy.npz';save_policy_arrays(model,path,{})
            receipt=json.loads(path.with_suffix('.json').read_text())
            receipt['tensors'].pop(next(iter(receipt['tensors'])))
            path.with_suffix('.json').write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):load_policy_arrays(path,{})
