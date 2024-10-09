import boa


def test_available_deposit_limit_paused(deposit_limit_module, security_agent, dev_address):
    """
    Tests that the available deposit limit returns 0 when deposits are paused.
    """
    # Set security_agent status for security_agent using dev_address privileges
    with boa.env.prank(dev_address):
        deposit_limit_module.set_security_agent(security_agent, True)

    # Pause deposits
    with boa.env.prank(security_agent):
        deposit_limit_module.set_deposits_paused(True)

    # Check that the available deposit limit is 0 when deposits are paused
    assert deposit_limit_module.available_deposit_limit(security_agent) == 0


def test_available_deposit_limit_below_max(
    deposit_limit_module, dev_address, crvusd, vault, vault_init_deposit_cap, vault_god
):
    """
    Tests the available deposit limit when the vault balance is below the max deposit limit.
    """

    # add infinite deposit limit (just to be able to deposit)
    vault.set_deposit_limit(2**256 - 1, sender=vault_god)
    # Set the mock vault and stablecoin balances
    deal_balance = int(0.7 * vault_init_deposit_cap)
    boa.deal(crvusd, dev_address, deal_balance)
    crvusd.approve(vault.address, deal_balance, sender=dev_address)
    vault.deposit(deal_balance, dev_address, sender=dev_address)

    # Set the max deposit limit higher than the vault balance
    limit_balance = vault_init_deposit_cap
    with boa.env.prank(dev_address):
        deposit_limit_module.set_deposit_limit(limit_balance)

    # Check that the available deposit limit is the difference between max limit and vault balance
    expected_limit = limit_balance - deal_balance
    assert (
        deposit_limit_module.available_deposit_limit(boa.env.generate_address()) == expected_limit
    )


def test_available_deposit_limit_above_max(
    deposit_limit_module, dev_address, crvusd, vault, vault_init_deposit_cap, vault_god
):
    """
    Tests the available limit when the vault balance is equal to or above the max deposit cap.
    """

    # add infinite deposit limit (just to be able to deposit)
    vault.set_deposit_limit(2**256 - 1, sender=vault_god)
    # Set the vault balance to be above the max deposit limit
    deal_balance = int(1.2 * vault_init_deposit_cap)
    boa.deal(crvusd, dev_address, deal_balance)
    crvusd.approve(vault.address, deal_balance, sender=dev_address)
    vault.deposit(deal_balance, dev_address, sender=dev_address)

    # Set the max deposit limit lower than the vault balance
    with boa.env.prank(dev_address):
        deposit_limit_module.set_deposit_limit(vault_init_deposit_cap)

    # Check that the available limit is 0 when the vault balance is above the max deposit cap
    assert deposit_limit_module.available_deposit_limit(boa.env.generate_address()) == 0
