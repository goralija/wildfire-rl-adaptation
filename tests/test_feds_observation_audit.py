import copy
import unittest
from unittest import mock

try:
    import numpy as np
except ImportError:
    raise unittest.SkipTest('optional NumPy dependency is not installed')

from wildfire_rl.feds_observation_audit import (
    audit_features, RBFModel, fit_models, predict_sequence, nested_actions, inner_folds,
)
from wildfire_rl.feds_b1_learning import observation_features


def observation():
    grid=np.zeros((4,16,16));grid[0,8,8]=1;grid[1,8,9]=1;grid[3]=.4
    return {'grid':grid.tolist(),'weather':[.1,1.,0.,.2],'time':[0.], 'budget':[.25,.25]}


class ObservationAuditTests(unittest.TestCase):
    def test_feature_dimensions_and_no_future_metadata(self):
        obs=observation()
        for kind,size in [('summary',28),('directional',76),('full_grid',1031)]:
            a=audit_features(obs,kind)
            changed=copy.deepcopy(obs);changed['future_weather']=[99];changed['scenario_id']='secret'
            np.testing.assert_array_equal(a,audit_features(changed,kind))
            self.assertEqual(a.shape,(size,))
            self.assertTrue(np.isfinite(a).all())
        np.testing.assert_array_equal(audit_features(obs,'summary'),observation_features(obs))
        with self.assertRaises(ValueError):audit_features(obs,'terrain')

    def test_rbf_uses_fitting_scaler_only_and_has_constant_distance_fallback(self):
        x=np.array([[0.,0.],[1.,0.],[2.,0.]])
        model=RBFModel(x,np.column_stack([x[:,0],x[:,0]**2]),.01,.5)
        before=(model.mean.copy(),model.scale.copy(),model.distance_scale)
        model.predict(np.array([[1e9,1e9]]))
        np.testing.assert_array_equal(model.mean,before[0]);np.testing.assert_array_equal(model.scale,before[1])
        self.assertEqual(model.distance_scale,before[2])
        constant=RBFModel(np.zeros((3,2)),np.ones((3,9)),.1,2.)
        np.testing.assert_allclose(constant.predict(np.zeros((1,2))),1.)

    def test_rbf_learns_a_nonlinear_signal(self):
        x=np.array([[-1,-1],[-1,1],[1,-1],[1,1.]]*3)
        y=(x[:,0]*x[:,1])[:,None]
        model=RBFModel(x,y,.01,.5)
        np.testing.assert_array_equal(np.sign(model.predict(x)),np.sign(y))

    def test_inner_folds_are_disjoint_complete_and_order_independent(self):
        ids=['fire'+str(i) for i in range(13)]
        folds=inner_folds(ids)
        self.assertEqual(sorted(i for f in folds for i in f),list(range(13)))
        groups=[{ids[i] for i in f} for f in folds]
        self.assertEqual(groups,[{list(reversed(ids))[i] for i in f} for f in inner_folds(list(reversed(ids)))])

    def test_nested_selection_cannot_use_outer_heldout_rewards(self):
        rng=np.random.default_rng(19);x=rng.normal(size=(13,4,3))
        gains=np.zeros((13,4,9));gains[:,0,1]=20*(x[:,0,0]>0);gains[:,0,2]=20*(x[:,0,0]<=0)
        masks=np.ones((13,4,9),dtype=bool);ids=[str(i) for i in range(13)]
        first=nested_actions(x,gains,masks,ids,12,'rbf',[(.01,.5),(.1,2.)])
        changed=gains.copy();changed[12]=rng.normal(size=(4,9))*1e8
        second=nested_actions(x,changed,masks,ids,12,'rbf',[(.01,.5),(.1,2.)])
        self.assertEqual(first,second)

    def test_policy_can_wait_and_never_spends_more_than_one_or_uses_masked_action(self):
        x=np.zeros((8,4,2));g=np.zeros((8,4,9));g[:,2,3]=50
        masks=np.ones((8,4,9),dtype=bool)
        models=fit_models(x,g,masks,'rbf',(.01,.5))
        self.assertEqual(predict_sequence(models,x[0],masks[0]),[0,0,3,0])
        blocked=np.zeros((4,9),dtype=bool);blocked[:,0]=True
        self.assertEqual(predict_sequence(models,x[0],blocked),[0,0,0,0])
        g[:]=-10;g[:,:,0]=0
        models=fit_models(x,g,masks,'rbf',(.01,.5))
        self.assertEqual(predict_sequence(models,x[0],masks[0]),[0,0,0,0])

    def test_prediction_stops_reading_future_states_after_a_line(self):
        class Model:
            def predict(self,x):return np.array([[0.,10.]+[0.]*7])
        class Forbidden:
            def predict(self,x):raise AssertionError('future state used after line')
        self.assertEqual(predict_sequence([Model(),Forbidden(),Forbidden(),Forbidden()],
                         np.zeros((4,2)),np.ones((4,9),dtype=bool)),[1,0,0,0])


if __name__=='__main__':unittest.main()
