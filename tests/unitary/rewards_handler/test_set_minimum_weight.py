import boa


def test_default_behavior(rewards_handler, curve_dao):
    rewards_handler.set_minimum_weight(2000, sender=curve_dao)
    assert rewards_handler.minimum_weight() == 2000


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_minimum_weight(2000, sender=boa.env.generate_address())
