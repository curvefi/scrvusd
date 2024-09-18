import boa


def test_compute_twa_no_snapshots(rewards_handler, crvusd, vault, lens, vault_god):
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
    vault.deposit(AMT_DEPOSIT, alice, sender=alice)

    assert rewards_handler.get_len_snapshots() == 0
    twa = rewards_handler.compute_twa()
    assert twa == 0, f"Expected TWA to be 0 when no snapshots, got {twa}"


def test_one_deposit_boa(rewards_handler):
    rewards_handler.eval("twa.twa_window = 1000")
    rewards_handler.eval("twa._store_snapshot(100 * 10**18)")
    boa.env.time_travel(seconds=2000)
    assert rewards_handler.compute_twa() == 100 * 10**18


def test_twa_one_deposit(vault, crvusd, rewards_handler, lens, vault_god):
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
    TWA_WINDOW = rewards_handler.twa_window()

    vault.deposit(AMT_DEPOSIT, alice, sender=alice)
    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=TWA_WINDOW + 1)

    # Compute TWA
    twa = rewards_handler.compute_twa()
    expected_twa = AMT_DEPOSIT * 10**18 // lens.circulating_supply()
    assert twa == expected_twa, "TWA does not match expected amount"


def test_twa_two_deposits(vault, crvusd, rewards_handler, lens, vault_god):
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
    TWA_WINDOW = rewards_handler.twa_window()

    vault.deposit(AMT_DEPOSIT, alice, sender=alice)
    rewards_handler.take_snapshot()

    boa.env.time_travel(seconds=TWA_WINDOW)

    vault.deposit(AMT_DEPOSIT, alice, sender=alice)
    rewards_handler.take_snapshot()

    # Compute TWA
    twa = rewards_handler.compute_twa()
    expected_twa = 1.5 * AMT_DEPOSIT * 10**18 // lens.circulating_supply()
    assert twa == expected_twa, "TWA does not match expected amount"


def test_twa_multiple_deposits(vault, crvusd, rewards_handler, lens, vault_god):
    # Prepare Alice's balance
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, 100_000_000 * 10**18)
    crvusd.approve(vault.address, 2**256 - 1, sender=alice)

    # Set up RewardsHandler
    rewards_handler.eval(f"self.lens = {lens.address}")

    # Set vault deposit limit to Alice's full balance
    vault.set_deposit_limit(crvusd.balanceOf(alice), sender=vault_god)

    # Define parameters
    AMT_DEPOSIT = 10 * 10**18  # Amount to deposit per iteration
    TWA_WINDOW = rewards_handler.twa_window()  # TWA window (e.g., one week)
    N_ITERATIONS = 5  # Number of deposits
    TIME_BETWEEN_DEPOSITS = TWA_WINDOW // N_ITERATIONS  # Time between each deposit

    # Store the staked supply rates after each snapshot
    staked_supply_rates = []
    timestamps = []

    # Perform deposits and take snapshots at regular intervals
    for i in range(N_ITERATIONS):
        # Deposit into the vault
        vault.deposit(AMT_DEPOSIT, alice, sender=alice)

        # Take a snapshot of the staked supply rate in the rewards handler
        rewards_handler.take_snapshot()

        # Retrieve the staked_supply_rate from the most recent snapshot
        rate, ts = rewards_handler.snapshots(i)
        staked_supply_rates.append(rate)
        timestamps.append(ts)

        # Move forward in time to simulate the next interval
        boa.env.time_travel(seconds=TIME_BETWEEN_DEPOSITS)

    # Advance time to complete the TWA window
    remaining_time = TWA_WINDOW - TIME_BETWEEN_DEPOSITS * N_ITERATIONS
    if remaining_time > 0:
        boa.env.time_travel(seconds=remaining_time)

    # Now validate TWA computation
    total_weighted_staked_supply_rate = 0
    total_time = 0
    # go through all, we are within single window
    for i in range(len(staked_supply_rates) - 1):
        # Get the current snapshot and the next one
        current_rate = staked_supply_rates[i]
        next_rate = staked_supply_rates[i + 1]

        # Get the corresponding timestamps
        current_timestamp = timestamps[i]
        next_timestamp = timestamps[i + 1]

        # Calculate the time delta between the two snapshots
        time_delta = next_timestamp - current_timestamp

        # Apply the trapezoidal rule: average of current and next rate,
        # weighted by the time delta
        trapezoidal_rate = (current_rate + next_rate) // 2

        # Accumulate the weighted staked supply rate and total time
        total_weighted_staked_supply_rate += trapezoidal_rate * time_delta
        total_time += time_delta

    # Handle the last interval (from the last snapshot to the current time)
    if len(staked_supply_rates) > 0:
        last_rate = staked_supply_rates[-1]
        last_timestamp = timestamps[-1]
        time_delta = boa.env.evm.patch.timestamp - last_timestamp

        # For the last period, we assume the rate stays constant
        # up to the current time
        total_weighted_staked_supply_rate += last_rate * time_delta
        total_time += time_delta

    # Compute the expected TWA based on a simple average of
    # staked_supply_rates
    expected_twa = total_weighted_staked_supply_rate // total_time

    # Get the TWA from the contract
    twa = rewards_handler.compute_twa()

    # Calculate the actual staked rate for comparison
    total_staked_amount = AMT_DEPOSIT * N_ITERATIONS
    circulating_supply = lens.circulating_supply()
    staked_rate = total_staked_amount * 10**18 // circulating_supply

    print(f"Staked rate: {staked_rate}, Contract TWA: {twa}")

    # Compare the TWA from the contract against the expected values
    assert twa <= staked_rate, "TWA is unexpectedly higher than the staked rate"
    assert twa == expected_twa, f"TWA {twa} does not match expected {expected_twa}"
