import boa


def test_role_access(rewards_handler, curve_dao, deployer):
    # validate that deployer can't change twa parameters
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_twa_window(1, sender=deployer)
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_twa_frequency(1, sender=deployer)
