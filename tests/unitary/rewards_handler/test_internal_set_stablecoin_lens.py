import boa


def test_default_behavior(rewards_handler):
    new_lens = boa.env.generate_address()
    rewards_handler.internal._set_stablecoin_lens(new_lens)
    assert rewards_handler.stablecoin_lens() == new_lens


def test_zero_address(rewards_handler):
    with boa.reverts("no lens"):
        rewards_handler.internal._set_stablecoin_lens("0x0000000000000000000000000000000000000000")
