import boa


def test_default_behavior(rewards_handler, rate_manager):
    new_lens = boa.env.generate_address()
    rewards_handler.set_stablecoin_lens(new_lens, sender=rate_manager)
    events = rewards_handler.get_logs()

    # Verify event emission
    assert f"StablecoinLensUpdated(new_stablecoin_lens={new_lens}" in repr(events)

    assert rewards_handler.stablecoin_lens() == new_lens


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_stablecoin_lens(
            boa.env.generate_address(), sender=boa.env.generate_address()
        )
