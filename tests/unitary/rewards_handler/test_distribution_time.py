def test_default_behavior(rewards_handler):
    # at the beginning it has to be at 0 so that
    # process_rewards can't be called yet
    assert rewards_handler.distribution_time() == 0
