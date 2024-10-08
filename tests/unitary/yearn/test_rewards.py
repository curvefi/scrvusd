import boa


def test_get_rewards(vault, crvusd, vault_god, rewards_handler, accrual_strategy_ext, dev_address):
    # initial balances
    strat_balance_init = crvusd.balanceOf(accrual_strategy_ext)

    # 1-2. Alice deposits into st-crvUSD vault
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 10_000 * 10**18)
    print(
        f"1.Bal: {[crvusd.balanceOf(x)/1e18 for x in [alice, vault, rewards_handler, accrual_strategy_ext]]}"  # noqa E501
    )

    vault.set_deposit_limit(10_000_000 * 10**18, sender=vault_god)

    with boa.env.prank(alice):
        crvusd.approve(vault, 10_000 * 10**18)
        vault.deposit(10_000 * 10**18, alice)

    assert vault.balanceOf(alice) == 10_000 * 10**18
    assert crvusd.balanceOf(alice) == 0
    print(
        f"2.Bal: {[crvusd.balanceOf(x)/1e18 for x in [alice, vault, rewards_handler, accrual_strategy_ext]]}"  # noqa E501
    )
    print(
        f"2.Strat bal: {[accrual_strategy_ext.balanceOf(x)/1e18 for x in [vault, accrual_strategy_ext]]}, Total Supply: {accrual_strategy_ext.totalSupply()/1e18}"  # noqa E501
    )

    # 3. Rewards handler receives rewards
    assert crvusd.balanceOf(rewards_handler) == 0
    AIRDROP_AMOUNT = 1_000 * 10**18
    boa.deal(crvusd, rewards_handler, AIRDROP_AMOUNT)
    assert crvusd.balanceOf(rewards_handler) == AIRDROP_AMOUNT
    print(
        f"3. Bal: {[crvusd.balanceOf(x)/1e18 for x in [alice, vault, rewards_handler, accrual_strategy_ext]]}"  # noqa E501
    )
    print(
        f"3.Strat bal: {[accrual_strategy_ext.balanceOf(x)/1e18 for x in [vault, accrual_strategy_ext]]}, Total Supply: {accrual_strategy_ext.totalSupply()/1e18}"  # noqa E501
    )

    # ##### assign keeper - TODO: fixture
    with boa.env.prank(dev_address):
        accrual_strategy_ext.setKeeper(rewards_handler.address)

    # 4. Random address calls process_rewards -> rewards are transferred to accrual strategy
    assert crvusd.balanceOf(accrual_strategy_ext) == strat_balance_init
    with boa.env.prank(boa.env.generate_address()):
        rewards_handler.process_rewards()
    # events = rewards_handler.get_logs()
    # print(events)
    assert crvusd.balanceOf(rewards_handler) == 0
    # assert crvusd.balanceOf(accrual_strategy_ext) == AIRDROP_AMOUNT + strat_balance_init
    print(
        f"4. Bal: {[crvusd.balanceOf(x)/1e18 for x in [alice, vault, rewards_handler, accrual_strategy_ext]]}"  # noqa E501
    )
    print(
        f"4.Strat bal: {[accrual_strategy_ext.balanceOf(x)/1e18 for x in [vault, accrual_strategy_ext]]}, Total Supply: {accrual_strategy_ext.totalSupply()/1e18}"  # noqa E501
    )
    boa.env.time_travel(seconds=7 * 86_400)

    with boa.env.prank(alice):
        vault.approve(vault, 10_000 * 10**18, sender=alice)
        vault.redeem(10_000 * 10**18, alice, alice, sender=alice)
    assert vault.balanceOf(alice) == 0
    assert crvusd.balanceOf(alice) >= 10_000 * 10**18 + 0.99 * AIRDROP_AMOUNT
