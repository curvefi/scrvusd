import boa


def test_default_behavior(rewards_handler, rate_manager):
    initial_twa_dt = rewards_handler.min_snapshot_dt_seconds()
    new_twa_dt = initial_twa_dt + 12
    with boa.env.prank(rate_manager):
        rewards_handler.set_twa_snapshot_dt(new_twa_dt)
    updated_twa_dt = rewards_handler.min_snapshot_dt_seconds()
    assert updated_twa_dt == new_twa_dt


def test_role_access(rewards_handler, curve_dao, dev_deployer):
    # validate that deployer can't change twa parameters
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_twa_window(1, sender=dev_deployer)
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_twa_snapshot_dt(1, sender=dev_deployer)
