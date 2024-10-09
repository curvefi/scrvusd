import boa


def test_default_behavior(deposit_limit_module, dev_address, deposit_limit_controller):

    # Verify that external_controller is not yet a controller
    assert not deposit_limit_module.is_controller(deposit_limit_controller)

    # Set controller status for external_controller using dev_address privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_controller(deposit_limit_controller, True)

    # Verify that external_controller is now a controller
    assert deposit_limit_module.is_controller(deposit_limit_controller)

    # Revoke controller role for dev_address using external_controller privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_controller(deposit_limit_controller, False)

    # Verify that external_controller is no longer a controller
    assert not deposit_limit_module.is_controller(deposit_limit_controller)


def test_set_controller_unauthorized(deposit_limit_module, curve_dao, deposit_limit_controller):
    # Verify that curve_dao is not a controller initially
    assert not deposit_limit_module.is_controller(curve_dao)

    # Attempt to set controller status using an unauthorized (non-admin) address
    with boa.env.prank(deposit_limit_controller), boa.reverts("Caller is not an admin"):
        deposit_limit_module.set_controller(curve_dao, True)

    # Verify that curve_dao is still not a controller since the call should have failed
    assert not deposit_limit_module.is_controller(curve_dao)
