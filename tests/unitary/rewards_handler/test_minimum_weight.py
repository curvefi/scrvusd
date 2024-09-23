def test_default_behavior_constructor(rewards_handler, minimum_weight):
    # rewards handler should correspond to the one at construction
    assert rewards_handler.minimum_weight() == minimum_weight


def test_default_behavior_setter(rewards_handler, curve_dao):
    rewards_handler.set_minimum_weight(2000, sender=curve_dao)
    assert rewards_handler.minimum_weight() == 2000
