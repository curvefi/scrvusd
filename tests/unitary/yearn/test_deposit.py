import boa


def test_deposit(vault, crvusd, role_manager, vault_god):
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 10_000 * 10**18)

    vault.set_deposit_limit(10_000 * 10**18, sender=vault_god)

    with boa.env.prank(alice):
        crvusd.approve(vault, 10_000 * 10**18)
        vault.deposit(10_000 * 10**18, alice)

    assert vault.balanceOf(alice) == 10_000 * 10**18
    assert crvusd.balanceOf(alice) == 0

    with boa.env.prank(alice):
        vault.approve(vault, 10_000 * 10**18, sender=alice)
        vault.redeem(10_000 * 10**18, alice, alice, sender=alice)

    assert vault.balanceOf(alice) == 0
    assert crvusd.balanceOf(alice) == 10_000 * 10**18
