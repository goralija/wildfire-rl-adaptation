"""Deployable fixed heuristics for the explicitly versioned v2 observation."""
from .feds_heuristics import make_heuristic,advancing_front_policy


def advancing_front64_policy(observation,mask):
    return advancing_front_policy({**observation,'grid':observation['global_grid']},mask)


def make_repaired_heuristic(name):
    if name=='advancing_front64':return advancing_front64_policy
    return make_heuristic(name)
