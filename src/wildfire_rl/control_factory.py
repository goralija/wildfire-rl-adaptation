"""TRAIN-only common-line backends, independent of historical experiment runners."""
import hashlib
import numpy as np
from .feds_simfire_env import FedsSimFireEnv
from .feds_simfire_setup import (INPUT_ROOT,WEATHER,SimFireParams,load_case_inputs,
                                observed_weather_records,record_forcing)
from .feds_observation_v2 import SimFireObservationV2
from .paired_simulators import CABridgeEnv
from .synthetic_real_cases import crop_centre_lonlat,episode_start_utc,weather_from_segments


def spread_seed(scenario_id,replicate):
    """Preserve the original common-line CA replicate mapping."""
    return int.from_bytes(hashlib.sha256(('TASK040:'+scenario_id+':'+str(replicate)).encode()).digest()[:8],'big')%(2**31)


def ca_bridge(inputs,replicate=0):
    lon,_=crop_centre_lonlat(inputs['receipt']['grid'],0,0,size=256)
    hours=weather_from_segments(inputs['weather']['segments'],episode_start_utc(inputs['weather']),
                                lon,decisions=48,wind_adjustment=.1).steps
    params=SimFireParams(wind_adjustment_factor=.1)
    observed=[record_forcing(r,params) for r in observed_weather_records(inputs['weather'],'previous')]
    for k in range(4):
        expected=record_forcing(inputs['weather']['segments'][k],params);actual=hours[k*12]
        if not np.isclose(actual.wind_midflame_m_s*196.8503937007874,expected['wind_speed_midflame_ft_per_min_proxy']):
            raise ValueError('forcing speed mismatch')
        if not np.isclose(actual.wind_to_deg,expected['wind_direction_degrees_clockwise_north_to']):
            raise ValueError('forcing direction mismatch')
        if not np.isclose(actual.moisture,expected['fuel_moisture_fraction_proxy']):raise ValueError('moisture mismatch')
    return SimFireObservationV2(CABridgeEnv(inputs,hours,observed,seed=spread_seed(inputs['scenario_id'],replicate)))


def native_env(backend,scenario_id,*,spread_replicate=0,weather_path=WEATHER,input_root=INPUT_ROOT):
    if backend not in ('simfire','ca'):raise ValueError('backend must be simfire or ca')
    if type(spread_replicate) is not int or spread_replicate<0 or (backend=='simfire' and spread_replicate!=0):
        raise ValueError('nonnegative CA replicate or SimFire replicate0 required')
    inputs=load_case_inputs(scenario_id,split='train',weather_path=weather_path,input_root=input_root)
    if backend=='ca':return ca_bridge(inputs,spread_replicate),inputs
    env=FedsSimFireEnv(split='train',scenario_ids=[scenario_id],budgets=(1,),max_budget=4,
        line_placement='front_edge',weather_observation='previous',sim_params=SimFireParams(wind_adjustment_factor=.1),
        weather_path=weather_path,input_root=input_root)
    return SimFireObservationV2(env),inputs
