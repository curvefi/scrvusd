import boa


def test_default_behavior(deposit_limit_module, dev_address):
    # Pause deposits using the security_agent privileges of dev_address
    with boa.env.prank(dev_address):
        deposit_limit_module.set_deposits_paused(True)

    # Verify that deposits are paused
    assert deposit_limit_module.deposits_paused()

    # Resume deposits
    with boa.env.prank(dev_address):
        deposit_limit_module.set_deposits_paused(False)

    # Verify that deposits are no longer paused
    assert not deposit_limit_module.deposits_paused()


def test_set_deposits_paused_unauthorized(deposit_limit_module, security_agent):
    # Verify deposits are initially unpaused
    assert not deposit_limit_module.deposits_paused()

    # Attempt to pause deposits using an unauthorized address
    with boa.env.prank(security_agent), boa.reverts("Caller is not a security_agent"):
        deposit_limit_module.set_deposits_paused(True)

    # Verify that deposits are still unpaused since the call should have failed
    assert not deposit_limit_module.deposits_paused()
