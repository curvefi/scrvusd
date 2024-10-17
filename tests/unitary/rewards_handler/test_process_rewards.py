import boa


def test_default_behavior(rewards_handler, crvusd, vault, rate_manager):
    distributed_amount = 10**18 * 100
    boa.deal(crvusd, rewards_handler, distributed_amount)

    rewards_handler.set_distribution_time(86_400 * 7, sender=rate_manager)

    assert crvusd.balanceOf(rewards_handler) == distributed_amount

    rewards_handler.process_rewards()

    assert crvusd.balanceOf(rewards_handler) == 0

    # TODO more assertions to validate internal vault logic
    # This probably requires boa eval for vvm.


def test_over_time(rewards_handler):
    with boa.reverts("rewards should be distributed over time"):
        rewards_handler.process_rewards()


def test_no_rewards(rewards_handler, rate_manager):
    rewards_handler.set_distribution_time(1234, sender=rate_manager)

    with boa.reverts("no rewards to distribute"):
        rewards_handler.process_rewards()


def test_snapshots_taking(rewards_handler, rate_manager, crvusd):
    rewards_handler.set_distribution_time(1234, sender=rate_manager)  # to enable process_rewards
    assert rewards_handler.get_len_snapshots() == 0
    boa.deal(crvusd, rewards_handler, 1)
    rewards_handler.process_rewards()
    assert crvusd.balanceOf(rewards_handler) == 0  # crvusd gone
    assert rewards_handler.get_len_snapshots() == 1  # first snapshot taken

    boa.deal(crvusd, rewards_handler, 1)
    rewards_handler.process_rewards()
    assert crvusd.balanceOf(rewards_handler) == 0  # crvusd gone (again)
    assert rewards_handler.get_len_snapshots() == 1  # not changed since dt has not passed

    boa.env.time_travel(seconds=rewards_handler.min_snapshot_dt_seconds())
    boa.deal(crvusd, rewards_handler, 1)
    rewards_handler.process_rewards()
    assert crvusd.balanceOf(rewards_handler) == 0  # crvusd gone (they always go)
    assert rewards_handler.get_len_snapshots() == 2  # changed since dt has passed
