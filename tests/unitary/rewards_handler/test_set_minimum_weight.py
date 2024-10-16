import boa


def test_default_behavior(rewards_handler, rate_manager):
    rewards_handler.set_minimum_weight(2000, sender=rate_manager)
    events = rewards_handler.get_logs()

    # Verify event emission
    assert f"MinimumWeightUpdated(new_minimum_weight={2000}" in repr(events)

    assert rewards_handler.minimum_weight() == 2000


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_minimum_weight(2000, sender=boa.env.generate_address())
