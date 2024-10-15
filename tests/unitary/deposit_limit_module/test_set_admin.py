import boa


def test_default_behavior(deposit_limit_module, dev_deployer, curve_dao, dev_multisig):
    # Verify that dev_deployer is not an admin
    assert not deposit_limit_module.is_admin(dev_deployer)

    # Call function to set admin status
    with boa.env.prank(dev_multisig):
        deposit_limit_module.set_admin(curve_dao, True)

    # Verify that curve_dao is now an admin
    assert deposit_limit_module.is_admin(curve_dao)

    # Revoke admin role
    with boa.env.prank(curve_dao):
        deposit_limit_module.set_admin(dev_multisig, False)

    # Verify that dev_deployer is no longer an admin
    assert not deposit_limit_module.is_admin(dev_multisig)


def test_set_admin_unauthorized(deposit_limit_module, curve_dao, security_agent):
    # Verify that curve_dao is not an admin
    assert not deposit_limit_module.is_admin(curve_dao)

    # Attempt to set admin status using an unauthorized (non-admin) address
    with boa.env.prank(security_agent), boa.reverts("Caller is not an admin"):
        deposit_limit_module.set_admin(curve_dao, True)

    # Verify that curve_dao is not an admin since the call should have failed
    assert not deposit_limit_module.is_admin(curve_dao)
