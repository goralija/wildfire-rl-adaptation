import importlib.util
import unittest
from types import SimpleNamespace

if not importlib.util.find_spec('numpy') or not importlib.util.find_spec('gymnasium'):
    raise unittest.SkipTest('optional NumPy/Gymnasium dependencies are not installed')
import numpy as np
from wildfire_rl.feds_simfire_env import FedsSimFireEnv, front_edge_line_points
from wildfire_rl.feds_heuristics import heading_vector, sector_for_vector
from wildfire_rl.gridmet_weather import direction_from_to_simfire_direction


def fake_env(x,y,fuel=13):
    env=FedsSimFireEnv.__new__(FedsSimFireEnv)
    state=np.zeros((256,256),dtype=int);state[y,x]=1
    env.simulation=SimpleNamespace(fire_map=state);env.cumulative_burned=(state==1)
    env.fuel=np.full(state.shape,fuel);env.block_count=16
    env.initial_budget=env.remaining_budget=1;env.max_budget=4
    env.decision_index=0;env.horizon_steps=4
    env.observed_forcing=[{'wind_direction_degrees_clockwise_north_to':90.,
                          'wind_speed_midflame_ft_per_min_proxy':50.,
                          'fuel_moisture_fraction_proxy':.06}]*4
    return env


class ObservationContractTests(unittest.TestCase):
    def test_same_pooled_front_can_hide_different_native_line_anchors(self):
        a,b=fake_env(113,113),fake_env(126,126)
        for key in a._observation():
            np.testing.assert_array_equal(a._observation()[key],b._observation()[key])
        self.assertNotEqual(front_edge_line_points(a.simulation.fire_map,a.simulation.fire_map==1,0),
                            front_edge_line_points(b.simulation.fire_map,b.simulation.fire_map==1,0))

    def test_fuel_13_and_nonfuel_91_have_the_same_observed_fuel_channel(self):
        a,b=fake_env(128,128,13),fake_env(128,128,91)
        np.testing.assert_array_equal(a._observation()['grid'][3],b._observation()['grid'][3])
        self.assertFalse(np.array_equal(a.fuel,b.fuel))

    def test_wind_from_to_compass_and_north_up_raster_agree(self):
        # Wind FROM W/N/E/S travels E/S/W/N, corresponding to sectors 0/2/4/6.
        for wind_from,sector in [(270.,0),(0.,2),(90.,4),(180.,6)]:
            bearing=direction_from_to_simfire_direction(wind_from)
            dx,dy=heading_vector(np.sin(np.deg2rad(bearing)),np.cos(np.deg2rad(bearing)))
            self.assertEqual(sector_for_vector(dx,dy),sector)

if __name__=='__main__':unittest.main()
