import boa


def test_default_behavior(crvusd, vault, rewards_handler, lens, role_manager):

    boa.deal(crvusd, rewards_handler, 10**23)
    rewards_handler.eval(f"self.lens = {lens.address}")
    # rewards_handler.take_snapshot()

    print(vault.roles(rewards_handler))

    vault.add_strategy(vault, sender=rewards_handler.address)

    rewards_handler.process_rewards()

    assert crvusd.balanceOf(rewards_handler) == 0
