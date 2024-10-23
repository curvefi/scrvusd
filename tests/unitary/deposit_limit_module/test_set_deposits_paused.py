import boa


def test_default_behavior(
    deposit_limit_module,
    dev_multisig,
):
    # Pause deposits using the security_agent privileges of dev_multisig
    with boa.env.prank(dev_multisig):
        deposit_limit_module.set_deposits_paused(True)

    # Verify event emission
    events = deposit_limit_module.get_logs()
    assert f"DepositsPaused(status={True}" in repr(events)

    # Verify that deposits are paused
    assert deposit_limit_module.deposits_paused()

    # Resume deposits
    with boa.env.prank(dev_multisig):
        deposit_limit_module.set_deposits_paused(False)

    # Verify that deposits are no longer paused
    assert not deposit_limit_module.deposits_paused()


def test_set_deposits_paused_unauthorized(
    deposit_limit_module,
    dev_deployer,
):
    # Verify deposits are initially unpaused
    assert not deposit_limit_module.deposits_paused()

    # Attempt to pause deposits using an unauthorized address
    with (
        boa.env.prank(dev_deployer),
        boa.reverts("Caller is not a security_agent"),
    ):
        deposit_limit_module.set_deposits_paused(True)

    # Verify that deposits are still unpaused since the call should have failed
    assert not deposit_limit_module.deposits_paused()
