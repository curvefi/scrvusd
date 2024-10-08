import boa


def test_deposit(vault, crvusd, role_manager, vault_god, rewards_handler, curve_dao):
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 10**21)

    vault.set_deposit_limit(10**21, sender=vault_god)

    with boa.env.prank(alice):
        crvusd.approve(vault, 10**21)
        vault.deposit(10**21, alice)

    assert vault.balanceOf(alice) == 10**21
    assert crvusd.balanceOf(alice) == 0

    print(rewards_handler.distribution_time())
    boa.deal(crvusd, rewards_handler, 10**21)
    rewards_handler.set_distribution_time(86400 * 7, sender=curve_dao)
    rewards_handler.process_rewards()
    # we make 3 days pass

    for i in range(7):
        boa.env.time_travel(86400 * i)
        with boa.env.anchor(), boa.env.prank(alice):
            vault.approve(vault, 10**21, sender=alice)
            vault.redeem(10**21, alice, alice, sender=alice)
            assert vault.balanceOf(alice) == 0
            assert crvusd.balanceOf(alice) >= 10**21
            print("alice balance has increased")
            print(crvusd.balanceOf(alice))
