import textwrap

import boa
import pytest
import address_book as ab


@pytest.fixture()
def new_depositor(crvusd, vault):
    def _new_depositor(amount):
        depositor = boa.env.generate_address()
        boa.deal(crvusd, depositor, amount)

        with boa.env.prank(depositor):
            crvusd.approve(vault.address, amount, sender=depositor)
            vault.deposit(amount, depositor)
        return depositor

    return _new_depositor


@pytest.fixture(autouse=True)
def inject_raw_weight(rewards_handler):
    raw_weight_source = textwrap.dedent("""
    @view
    @external
    def raw_weight() -> uint256:
        return twa._compute() * self.scaling_factor // MAX_BPS
    """)
    rewards_handler.inject_function(raw_weight_source)


def test_fee_splitter_cap(
    fee_splitter, crvusd, vault, rewards_handler, active_controllers, new_depositor, stablecoin_lens
):
    # test were we ask for so much that we hit the cap
    fee_splitter_cap = fee_splitter.receivers(0)[1]

    circulating_supply = stablecoin_lens.circulating_supply()

    # with the supply at the time of the fork
    # if we deposit 10_000_000 crvUSD in the vault
    # the weight asked will roughly be 16% (1600 bps)
    # which is above than the fee splitter cap of 10%
    # so the weight should be clamped to 1000 bps
    deposit_amount = int(circulating_supply * 0.16)

    new_depositor(deposit_amount)

    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=86_400 * 2)

    raw_weight = rewards_handler.inject.raw_weight()

    assert raw_weight > fee_splitter_cap

    # here checking the actual weight won't work as the weight is
    # capped at the source level (fee_splitter)
    assert rewards_handler.weight() == rewards_handler.inject.raw_weight()

    fee_splitter.dispatch_fees(active_controllers)

    fee_collector_after = crvusd.balanceOf(ab.crvusd_fee_collector)
    rewards_handler_after = crvusd.balanceOf(rewards_handler.address)

    # amount received by the rewards_handler was capped at the source
    assert fee_collector_after / rewards_handler_after == 9_000 / 1_000


def test_minimum_weight(rewards_handler, minimum_weight, vault, crvusd, new_depositor):
    # when there are no depositors in the vault we should be
    assert rewards_handler.weight() == minimum_weight

    # with the supply at the time of the fork
    # if we deposit 1_000_000 crvUSD in the vault
    # the weight asked will roughly be 1.6% (160 bps)
    # which is less than the minimum weight of 5%
    # so the weight should be clamped to 500 bps
    deposit_amount = 1_000_000 * 10**18

    new_depositor(deposit_amount)

    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=86_400 * 2)

    raw_weight = rewards_handler.inject.raw_weight()

    assert raw_weight < minimum_weight
    assert rewards_handler.weight() == minimum_weight


def test_dynamic_weight_depositors(
    crvusd, vault, rewards_handler, minimum_weight, fee_splitter, active_controllers, new_depositor
):
    # =============== DEPOSITS ===============
    # test were as people deposit the amount asked increases

    deposit_amount = 100_000 * 10**18

    # we fill the checkpoint at the beginning
    # with a dummy value
    prev_weight = 0

    depositors = []

    for i in range(100):
        rewards_handler.take_snapshot()

        depositor = new_depositor(deposit_amount)
        depositors.append(depositor)

        # roughly 1 deposit every day
        boa.env.time_travel(seconds=86_400)

        raw_weight = rewards_handler.inject.raw_weight()
        fee_splitter_cap = fee_splitter.receivers(0)[1]

        # ================= WEIGHTS CHECKS ==================

        with boa.env.anchor():
            fee_splitter.dispatch_fees(active_controllers)
            fee_collector_after = crvusd.balanceOf(ab.crvusd_fee_collector)
            rewards_handler_after = crvusd.balanceOf(rewards_handler.address)

        if raw_weight < rewards_handler.minimum_weight():
            assert rewards_handler.weight() >= raw_weight
            assert rewards_handler.weight() == rewards_handler.minimum_weight() == minimum_weight

        elif rewards_handler.minimum_weight() <= raw_weight <= fee_splitter_cap:
            assert rewards_handler.weight() > prev_weight

            # if the weight is actually dynamic we want to make sure
            # that the distribution is done according to the weight

            balance_ratio = fee_collector_after * 10_000 // rewards_handler_after
            excess = 1_000 - raw_weight
            weight_ratio = (9_000 + excess) * 10_000 // raw_weight

            assert balance_ratio == weight_ratio

        elif raw_weight > fee_splitter_cap:
            # amount received by the rewards_handler was capped at the source
            assert fee_collector_after / rewards_handler_after == 9_000 / 1_000

        else:
            raise AssertionError("This should not happen")

        # update the checkpoint
        prev_weight = rewards_handler.weight()

    # =============== WITHDRAWALS ===============

    # we time travel by a week because otherwise the
    # twa would still increase during the first withdrawals
    # which is totally correct but would break some assertions
    # that expect the weight to be strictly decreasing
    boa.env.time_travel(seconds=86_400 * 7)

    prev_weight = float("inf")

    for d in depositors:
        with boa.env.prank(d):
            depositor_shares = vault.balanceOf(d)
            assert depositor_shares > 0

            vault.redeem(depositor_shares, d, d)

            # roughly 1 withdrawal every day
            boa.env.time_travel(seconds=86_400)
            rewards_handler.take_snapshot()

            raw_weight = rewards_handler.inject.raw_weight()

            assert raw_weight < prev_weight

            prev_weight = raw_weight


def test_dynamic_weight_supply_changes(
    controller_factory, crvusd, rewards_handler, vault, new_depositor
):
    # as the supply changes the weight asked changes

    # we pick one controller from which we can borrow
    wsteth_controller_addy = controller_factory.controllers(1)
    wsteth_controller = boa.from_etherscan(wsteth_controller_addy, "wstheth_controller")

    wsteth = boa.from_etherscan(wsteth_controller.collateral_token())

    # Here alice takes the role of the borrower
    alice = boa.env.generate_address()

    # need a big depositor to make the weight go up
    # since we deal with boa this won't reduce the dynamic weight
    deposit_amount = 1_000_000 * 10**18
    new_depositor(deposit_amount)

    # update the weight
    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=86_400)

    # checkpoint of the weight
    prev_weight = rewards_handler.inject.raw_weight()

    # need a big borrower to make the weight go down
    collateral_amount = 1000 * 10**18
    loaned_amount = 1_000_000 * 10**18
    boa.deal(wsteth, alice, collateral_amount)

    with boa.env.prank(alice):
        wsteth.approve(wsteth_controller.address, collateral_amount)
        wsteth_controller.create_loan(collateral_amount, loaned_amount, 10)
        assert crvusd.balanceOf(alice) == loaned_amount

    # update the weight
    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=86_400)

    # make sure that the weight has decreased
    current_weight = rewards_handler.inject.raw_weight()

    assert prev_weight > current_weight
