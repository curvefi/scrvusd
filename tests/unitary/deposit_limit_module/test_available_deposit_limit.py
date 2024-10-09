import boa


def test_default_behavior(deposit_limit_module, dev_address, deposit_limit_controller):
    # Verify that deposits are unpaused by default
    assert not deposit_limit_module.deposits_paused()

    # Check that available deposit limit returns the maximum when deposits are unpaused
    max_limit = deposit_limit_module.available_deposit_limit(deposit_limit_controller)
    assert deposit_limit_module.available_deposit_limit(deposit_limit_controller) == max_limit

    # Set controller status for external_controller using dev_address privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_controller(deposit_limit_controller, True)

    # Pause deposits
    with boa.env.prank(deposit_limit_controller):
        deposit_limit_module.set_deposits_paused(True)

    # Verify that available deposit limit is zero when deposits are paused
    assert deposit_limit_module.available_deposit_limit(deposit_limit_controller) == 0

    # Unpause deposits
    with boa.env.prank(deposit_limit_controller):
        deposit_limit_module.set_deposits_paused(False)

    # Verify that available deposit limit returns the maximum again when deposits are unpaused
    assert deposit_limit_module.available_deposit_limit(deposit_limit_controller) == max_limit
