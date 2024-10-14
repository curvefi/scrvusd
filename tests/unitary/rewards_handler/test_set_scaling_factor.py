import boa


def test_default_behavior(rewards_handler, rate_manager):
    rewards_handler.set_scaling_factor(12_000, sender=rate_manager)  # 20% boost
    events = rewards_handler.get_logs()

    # Verify event emission
    assert f"ScalingFactorUpdated(new_scaling_factor={12_000}" in repr(events)

    assert rewards_handler.scaling_factor() == 12_000


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_scaling_factor(12_000, sender=boa.env.generate_address())
