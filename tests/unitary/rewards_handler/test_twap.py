import boa


def test_boa_timemachine():
    for i in range(10):
        current_timestamp = boa.env.evm.patch.timestamp
        boa.env.time_travel(blocks=1)
        assert boa.env.evm.patch.timestamp > current_timestamp


def test_twap_single_deposit(vault, crvusd, rewards_handler, lens, vault_god):
    # Prepare Alice's balance
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 100_000_000 * 10**18)
    crvusd.approve(vault.address, 2**256 - 1, sender=alice)

    # Set up RewardsHandler
    rewards_handler.eval(f"self.lens = {lens.address}")

    # Set vault deposit limit
    vault.set_deposit_limit(crvusd.balanceOf(alice), sender=vault_god)

    # Deposit and take snapshots over time
    AMT_DEPOSIT = 10 * 10**18
    TWAP_WINDOW = rewards_handler.get_twap_window()

    vault.deposit(AMT_DEPOSIT, alice, sender=alice)
    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=TWAP_WINDOW + 1)

    # Compute TWAP
    twap = rewards_handler.tvl_twap()
    assert (
        twap == AMT_DEPOSIT * 10**18 // lens.circulating_supply()
    ), "TWAP does not match expected deposit amount"


def test_twap_multiple_deposits(
    vault, crvusd, rewards_handler, lens, vault_god
):
    # Prepare Alice's balance
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 100_000_000 * 10**18)
    crvusd.approve(vault.address, 2**256 - 1, sender=alice)

    # Set up RewardsHandler
    rewards_handler.eval(f"self.lens = {lens.address}")

    # Set vault deposit limit
    vault.set_deposit_limit(crvusd.balanceOf(alice), sender=vault_god)

    # Define parameters
    AMT_DEPOSIT = 10 * 10**18
    TWAP_WINDOW = rewards_handler.get_twap_window()
    N_ITERATIONS = 5
    TIME_BETWEEN_DEPOSITS = (
        TWAP_WINDOW // N_ITERATIONS
    )  # Let's make 5 deposits within TWAP window
    staked_supply_rates = []

    # Deposit and take snapshots at regular intervals
    for i in range(N_ITERATIONS):
        # Deposit into the vault
        vault.deposit(AMT_DEPOSIT, alice, sender=alice)

        # Store a snapshot in the rewards handler
        rewards_handler.take_snapshot()

        # Get the staked_supply_rate from the snapshot
        rate, _ = rewards_handler.get_snapshot(i)
        staked_supply_rates.append(rate)

        # Advance time after each deposit
        boa.env.time_travel(seconds=TIME_BETWEEN_DEPOSITS)

    # Advance time to complete the TWAP window
    remaining_time = TWAP_WINDOW - TIME_BETWEEN_DEPOSITS * N_ITERATIONS
    if remaining_time > 0:
        boa.env.time_travel(seconds=remaining_time)

    # Compute the expected TWAP as a simple average
    expected_twap = sum(staked_supply_rates) // len(staked_supply_rates)

    # Compute TWAP from the contract
    twap = rewards_handler.tvl_twap()

    # Actual staked rate
    staked_rate = (
        AMT_DEPOSIT * N_ITERATIONS * 10**18 // lens.circulating_supply()
    )
    print(f"Staked rate: {staked_rate}, TWAP: {twap}")
    # Compare the expected TWAP to the contract's TWAP
    assert twap < staked_rate, "TWAP is too high"
    assert (
        twap == expected_twap
    ), f"TWAP {twap} does not match expected {expected_twap}"
