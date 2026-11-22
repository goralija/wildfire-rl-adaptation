import json
from pathlib import Path
import tempfile
import unittest

try:
    import torch
    import sb3_contrib
except ImportError as exc:
    raise unittest.SkipTest('optional SB3/Torch required: %s'%exc)

from test_common_control import environment
from wildfire_rl.common_control_rl import create_model,load_policy_arrays,policy_digest
from wildfire_rl.paired_ppo_learning import LazyTrainingCases
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_paired_ppo_learning import LearningCallback,contract


class LearningMilestoneTests(unittest.TestCase):
    def test_recorded_failure_stops_training_before_another_rollout(self):
        torch.set_num_threads(1)
        env=environment();model=create_model(env,seed=43)
        plan={'training_steps':2048}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);job=root/'job';job.mkdir()
            (root/'stop.json').write_text('{"reason":"test"}')
            callback=LearningCallback(job,{},'fake',43,plan)
            with self.assertRaisesRegex(RuntimeError,'another job failed'):
                model.learn(16,callback=callback)
            self.assertEqual(callback.rows,[])
        env.close()

    def test_checkpoint512_is_saved_after_update_and_has_guarded_numeric_roundtrip(self):
        torch.set_num_threads(1)
        def factory(sid):
            env=environment();env.unwrapped.scenario_id=sid;return env
        env=LazyTrainingCases(['a','b'],factory);model=create_model(env,seed=43)
        plan={'training_steps':2048,'architecture':{'test':'mlp'},'control':{'reward':{'version':'test'}}}
        guard={'plan':'test'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cb=LearningCallback(root,guard,'fake',43,plan);cb.model=model;cb.save(0)
            initial=policy_digest(model);model.learn(528,callback=cb)
            self.assertEqual(cb.saved,[0,512]);self.assertEqual(len(cb.rows),528)
            self.assertEqual(sum(r['done'] for r in cb.rows),132)
            restored=load_policy_arrays(root/'policy-512.npz',contract(guard,'fake',43,512,plan))
            self.assertNotEqual(initial,policy_digest(restored))
            self.assertEqual(json.loads((root/'status.json').read_text())['steps'],512)
            self.assertEqual([r['scenario_id'] for r in cb.rows if r['done']],['a','b']*66)
        env.close()
