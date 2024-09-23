import boa


def test_default_behavior(rewards_handler):
    rewards_handler.internal._set_minimum_weight(1234)
    assert rewards_handler.minimum_weight() == 1234


def test_more_than_max_bps(rewards_handler):
    with boa.reverts("minimum weight should be <= 100%"):
        rewards_handler.internal._set_minimum_weight(10001)
