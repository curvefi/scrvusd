import boa


def test_deposit(vault, crvusd, role_manager):
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 10**21)

    deposit_admin = boa.env.generate_address()

    with boa.env.prank(role_manager):
        vault.set_role(deposit_admin, int("11111111111111111111111", 2))

    vault.set_deposit_limit(10**21, sender=deposit_admin)

    with boa.env.prank(alice):
        crvusd.approve(vault, 10**21)
        vault.deposit(10**21, alice)
