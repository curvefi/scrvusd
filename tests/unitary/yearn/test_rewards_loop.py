import boa


def print_stats(crvusd, vault, rewards_handler, accrual_strategy_ext):
    print(
        f"crvUSD balances: vault: {crvusd.balanceOf(vault)/1e18}, strategy: {crvusd.balanceOf(accrual_strategy_ext)/1e18}, rewards_handler: {crvusd.balanceOf(rewards_handler)/1e18}"  # noqa E501
    )
    print(
        f"strategy shares: vault: {accrual_strategy_ext.balanceOf(vault)/1e18}, totalSupply: {accrual_strategy_ext.totalSupply()/1e18}"  # noqa E501
    )


def test_get_rewards(vault, crvusd, vault_god, rewards_handler, accrual_strategy_ext, dev_address):

    # ##### assign keeper - TODO: fixture
    with boa.env.prank(dev_address):
        accrual_strategy_ext.setKeeper(rewards_handler.address)

    AIRDROP_AMOUNT = 1_000 * 10**18
    for i in range(10):
        print(f"Iteration {i}")
        print("pre-logic stats:")
        print_stats(crvusd, vault, rewards_handler, accrual_strategy_ext)

        boa.deal(crvusd, rewards_handler, AIRDROP_AMOUNT)
        assert crvusd.balanceOf(rewards_handler) == AIRDROP_AMOUNT
        print("mid-logic stats:")
        print_stats(crvusd, vault, rewards_handler, accrual_strategy_ext)

        with boa.env.prank(boa.env.generate_address()):
            rewards_handler.process_rewards()
        assert crvusd.balanceOf(rewards_handler) == 0
        print("post-logic stats:")
        print_stats(crvusd, vault, rewards_handler, accrual_strategy_ext)
        print("---------------------------")
