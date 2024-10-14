import boa


def test_deposit(vault, crvusd, role_manager, vault_god):
    alice = boa.env.generate_address()
    amt_in = 100 * 10**18
    boa.deal(crvusd, alice, amt_in)

    vault.set_deposit_limit(amt_in, sender=vault_god)

    with boa.env.prank(alice):
        crvusd.approve(vault, amt_in)
        vault.deposit(amt_in, alice)

    assert vault.balanceOf(alice) == amt_in
    assert crvusd.balanceOf(alice) == 0

    with boa.env.prank(alice):
        vault.approve(vault, amt_in, sender=alice)
        vault.redeem(amt_in, alice, alice, sender=alice)

    assert vault.balanceOf(alice) == 0
    assert crvusd.balanceOf(alice) == amt_in
