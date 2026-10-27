"""Transparent baselines. L2 policies rank active fire by distance to ignition."""

from .simulator import FIRE

POLICIES = ('none', 'random', 'min_l2', 'max_l2', 'priority')


def choose_action(env, policy, rng):
    if policy not in POLICIES:
        raise ValueError(f'unknown policy: {policy}')
    valid = [i for i, valid in enumerate(env.action_masks()[:-1]) if valid]
    if policy == 'none' or not valid:
        return env.noop
    if policy == 'random':
        return rng.choice(valid)
    burning = [i for i in valid if env.state[i] == FIRE]
    if not burning:
        return env.noop

    def distance(a, b):
        ar, ac = divmod(a, env.scenario.cols)
        br, bc = divmod(b, env.scenario.cols)
        return (ar - br)**2 + (ac - bc)**2

    if policy == 'priority':
        # Suppress active fire nearest a priority cell. This is a transparent
        # baseline, not an implementation of optimal asset protection.
        targets = env.scenario.priority or env.scenario.ignition
        return min(burning, key=lambda i: (min(distance(i, p) for p in targets), i))
    rank = lambda i: min(distance(i, p) for p in env.scenario.ignition)
    if policy == 'min_l2':
        return min(burning, key=lambda i: (rank(i), i))
    return min(burning, key=lambda i: (-rank(i), i))
