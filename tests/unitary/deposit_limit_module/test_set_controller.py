import boa


def test_default_behavior(deposit_limit_module, dev_address, security_agent):
    # Verify that security_agent is not yet a security_agent
    assert not deposit_limit_module.is_security_agent(security_agent)

    # Set security_agent status using dev_address privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_security_agent(security_agent, True)

    # Verify that security_agent is now a security_agent
    assert deposit_limit_module.is_security_agent(security_agent)

    # Revoke security_agent role using dev_address privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_security_agent(security_agent, False)

    # Verify that security_agent is no longer a security_agent
    assert not deposit_limit_module.is_security_agent(security_agent)


def test_set_security_agent_unauthorized(deposit_limit_module, curve_dao, security_agent):
    # Verify that curve_dao is not a security_agent initially
    assert not deposit_limit_module.is_security_agent(curve_dao)

    # Attempt to set security_agent status using an unauthorized (non-admin) address
    with boa.env.prank(security_agent), boa.reverts("Caller is not an admin"):
        deposit_limit_module.set_security_agent(curve_dao, True)

    # Verify that curve_dao is still not a security_agent since the call should have failed
    assert not deposit_limit_module.is_security_agent(curve_dao)
