import boa

import address_book as ab


def test_fee_splitter(fee_splitter, rewards_handler, crvusd, vault):
    # =============== SETUP ===============
    # As the vote has not yet passed to add the rewards_handler as a receiver
    # we need to set the receivers manually
    time = vault.profitMaxUnlockTime()
    rewards_handler.eval(f"self.distribution_time = {time}")

    assert crvusd.balanceOf(ab.crvusd_fee_collector) == 0
    assert crvusd.balanceOf(rewards_handler.address) == 0

    receivers = [
        # dao receives 10% less in this test
        (ab.crvusd_fee_collector, 9_000),
        # we add the rewards_handler as a receiver
        (rewards_handler.address, 1_000),
    ]

    fee_splitter.set_receivers(receivers, sender=ab.dao_agent)

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
    controllers = [fee_splitter.controllers(i) for i in range(1, 6)]

    fee_splitter.dispatch_fees(controllers)

    # sanity check that fees have been dispatched correctly
    # fee_collector_after = crvusd.balanceOf(ab.crvusd_fee_collector)
    # rewards_handler_after = crvusd.balanceOf(rewards_handler.address)

    # assert fee_collector_after/rewards_handler_after == 9_000/1_000

    rewards_handler.process_rewards()
