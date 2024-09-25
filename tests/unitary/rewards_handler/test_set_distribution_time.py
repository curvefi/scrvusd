import boa


def test_default_behavior(rewards_handler, curve_dao):
    rewards_handler.set_distribution_time(1234, sender=curve_dao)

    assert rewards_handler.distribution_time() == 1234

    # TODO wait for eval in vvm to test this properly


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_distribution_time(1234)
