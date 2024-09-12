import boa


def test_deposit(vault, crvusd, role_manager, vault_god):
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 10**21)

    vault.set_deposit_limit(10**21, sender=vault_god)

    with boa.env.prank(alice):
        crvusd.approve(vault, 10**21)
        vault.deposit(10**21, alice)

    assert vault.balanceOf(alice) == 10**21
    assert crvusd.balanceOf(alice) == 0

    with boa.env.prank(alice):
        vault.approve(vault, 10**21, sender=alice)
        vault.redeem(10**21, alice, alice, sender=alice)

    assert vault.balanceOf(alice) == 0
    assert crvusd.balanceOf(alice) == 10**21
