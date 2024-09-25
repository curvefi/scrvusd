def test_default_behavior(rewards_handler, minimum_weight):
    # rewards handler should correspond to the one at construction
    assert rewards_handler.minimum_weight() == minimum_weight
