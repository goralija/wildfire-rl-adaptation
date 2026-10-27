import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from wildfire_rl.checkpoint_audit import audit_checkpoint


class CheckpointAuditTests(unittest.TestCase):
    def test_inspects_json_without_deserializing_embedded_pickle(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.zip'
            with zipfile.ZipFile(path, 'w') as z:
                z.writestr('data', json.dumps({'num_timesteps': 42,
                           'policy_kwargs': {':serialized:': 'not valid pickle',
                                             'features_extractor_class': 'custom.CNN'}}))
                z.writestr('_stable_baselines3_version', '1.5.0')
                z.writestr('policy.pth', 'never executed')
            result = audit_checkpoint(path)
            self.assertEqual(result['sb3_version'], '1.5.0')
            self.assertEqual(result['num_timesteps'], 42)
            self.assertEqual(result['features_extractor_class'], 'custom.CNN')
            self.assertEqual(len(result['sha256']), 64)
            self.assertFalse(result['deserialized'])
