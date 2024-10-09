import boa


def test_available_deposit_limit_paused(
    deposit_limit_module, deposit_limit_controller, dev_address
):
    """
    Tests that the available deposit limit returns 0 when deposits are paused.
    """
    # Set controller status for external_controller using dev_address privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_controller(deposit_limit_controller, True)

    # Pause deposits
    with boa.env.prank(deposit_limit_controller):
        deposit_limit_module.set_deposits_paused(True)

    # Check that the available deposit limit is 0 when deposits are paused
    assert deposit_limit_module.available_deposit_limit(deposit_limit_controller) == 0


def test_available_deposit_limit_below_max(deposit_limit_module, dev_address, crvusd, vault):
    """
    Tests the available deposit limit when the vault balance is below the max deposit limit.
    """
    # Set the mock vault and stablecoin balances
    deal_balance = 700_000 * 10**18
    boa.deal(crvusd, vault, deal_balance)

    # Set the max deposit limit higher than the vault balance
    limit_balance = 1_000_000 * 10**18
    with boa.env.prank(dev_address):
        deposit_limit_module.set_deposit_limit(limit_balance)

    # Check that the available deposit limit is the difference between max limit and vault balance
    expected_limit = limit_balance - deal_balance
    assert (
        deposit_limit_module.available_deposit_limit(boa.env.generate_address()) == expected_limit
    )


def test_available_deposit_limit_above_max(deposit_limit_module, dev_address, crvusd, vault):
    """
    Tests the available limit when the vault balance is equal to or above the max deposit cap.
    """
    # Set the vault balance to be above the max deposit limit
    deal_balance = 1_200_000 * 10**18
    boa.deal(crvusd, vault, deal_balance)

    # Set the max deposit limit lower than the vault balance
    limit_balance = 1_000_000 * 10**18
    with boa.env.prank(dev_address):
        deposit_limit_module.set_deposit_limit(limit_balance)

    # Check that the available limit is 0 when the vault balance is above the max deposit cap
    assert deposit_limit_module.available_deposit_limit(boa.env.generate_address()) == 0
