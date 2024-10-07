import boa


def test_default_behavior(rewards_handler, curve_dao):
    initial_twa_window = rewards_handler.twa_window()
    new_twa_window = initial_twa_window + 1000  # Increment by 1000 seconds

    with boa.env.prank(curve_dao):
        rewards_handler.set_twa_window(new_twa_window)

    # Verify that twa_window has been updated
    updated_twa_window = rewards_handler.twa_window()
    assert updated_twa_window == new_twa_window


def test_role_access(rewards_handler, curve_dao, dev_address):
    # validate that dev_address can't change twa parameters
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_twa_window(1, sender=dev_address)
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.set_twa_snapshot_dt(1, sender=dev_address)
