import boa


def test_default_behavior(deposit_limit_module, dev_multisig):
    # Define a new deposit limit value
    new_limit = 1_000_000 * 10**18

    # Call the external function to set the max deposit limit using admin privileges
    with boa.env.prank(dev_multisig):
        deposit_limit_module.set_deposit_limit(new_limit)

    # Verify event emission
    events = deposit_limit_module.get_logs()
    assert f"DepositLimitChanged(new_deposit_limit={new_limit}" in repr(events)

    # Verify that max_deposit_limit has been updated correctly
    assert deposit_limit_module.max_deposit_limit() == new_limit


def test_set_deposit_limit_unauthorized_access(deposit_limit_module, dev_deployer):
    init_limit = deposit_limit_module.max_deposit_limit()

    # Attempt to set the deposit limit using a non-admin address and expect a revert
    with boa.env.prank(dev_deployer), boa.reverts("Caller is not an admin"):
        deposit_limit_module.set_deposit_limit(init_limit + 1)

    # Verify that max_deposit_limit has not changed from its default (assuming default is 0)
    assert deposit_limit_module.max_deposit_limit() == init_limit
