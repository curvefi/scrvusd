import boa

import address_book as ab


def test_fee_splitter(fee_splitter, rewards_handler, crvusd, vault, active_controllers):
    assert crvusd.balanceOf(ab.crvusd_fee_collector) == 0
    assert crvusd.balanceOf(rewards_handler.address) == 0

    # ============== SOME DEPOSITS JOIN THE VAULT ==============
    alice = boa.env.generate_address("alice")
    bob = boa.env.generate_address("bob")

    depositors = [alice, bob]

    deposit_amount = 100 * 10**18
    for d in depositors:
        boa.deal(crvusd, d, 100_000_000 * 10**18)
        crvusd.approve(vault.address, deposit_amount, sender=d)
        vault.deposit(deposit_amount, d, sender=d)

        # roughly 1 deposit every two days
        boa.env.time_travel(seconds=86400 * 2)
        rewards_handler.take_snapshot()

    # ============== DISPATCH FEES ==============

    # we skip the first one as the market is deprecated
    fee_splitter.dispatch_fees(active_controllers)

    # sanity check that fees have been dispatched correctly

    # ================= PROCESS REWARDS =================

    rewards_handler.process_rewards()

    # just a dummy placeholder that will have 0 crvUSD
    prev_d = boa.env.generate_address()

    for d in depositors:
        boa.deal(crvusd, d, 100_000_000 * 10**18)
        # withdraw the same amount as it was deposited
        vault.approve(vault.address, deposit_amount, sender=d)
        # deposit amount = shares when conversion rate is 1:1
        vault.redeem(deposit_amount, d, d, sender=d)

        # roughly 1 withdrawal every two days
        boa.env.time_travel(seconds=86400 * 2)

        assert vault.balanceOf(d) == 0
        # depositors that withdrew later should accrue more rewards
        assert crvusd.balanceOf(d) > crvusd.balanceOf(prev_d)

        prev_d = d
