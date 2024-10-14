import boa


def test_default_behavior(rewards_handler, crvusd, vault, curve_dao):
    distributed_amount = 10**18 * 100
    boa.deal(crvusd, rewards_handler, distributed_amount)

    rewards_handler.set_distribution_time(86_400 * 7, sender=curve_dao)

    assert crvusd.balanceOf(rewards_handler) == distributed_amount

    rewards_handler.process_rewards()

    assert crvusd.balanceOf(rewards_handler) == 0

    # TODO more assertions to validate internal vault logic
    # This probably requires boa eval for vvm.


def test_over_time(rewards_handler):
    with boa.reverts("rewards should be distributed over time"):
        rewards_handler.process_rewards()


def test_no_rewards(rewards_handler, curve_dao):
    rewards_handler.set_distribution_time(1234, sender=curve_dao)

    with boa.reverts("no rewards to distribute"):
        rewards_handler.process_rewards()
