"""The finite B=1 decision tree and sequential policy evaluation on its no-op path."""


def action_sequences():
    return tuple([(0, 0, 0, 0)] + [tuple(action if k == decision else 0 for k in range(4))
                                 for decision in range(4) for action in range(1, 9)])


def policy_sequence(policy, observations, masks):
    """Before its only line, a policy sees exactly the no-op path's current state.

    Future observations, outcomes and labels are never passed to the policy.
    Once the line is placed, all remaining decisions are no-op.
    """
    actions = [0] * 4
    for k in range(4):
        action = int(policy(observations[k], masks[k]))
        if not 0 <= action <= 8:
            raise ValueError("policy action must be in [0, 8]")
        if action and masks[k][action]:
            actions[k] = action
            break
    return tuple(actions)


def audit_reference(rows, actions, damage_cells):
    values = {row["raw_damage_cells"] for row in rows
              if tuple(row["effective_actions"]) == tuple(actions)}
    if values != {damage_cells}:
        raise ValueError("B=1 table differs from the independent reference rollout")
    return True
