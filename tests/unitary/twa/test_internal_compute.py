import boa


def test_default_behavior_compute_twa_no_snapshots(
    rewards_handler, setup_vault, alice, amt_deposit
):
    vault = setup_vault

    # Deposit and take snapshots over time
    vault.deposit(amt_deposit, alice, sender=alice)

    assert rewards_handler.get_len_snapshots() == 0
    twa = rewards_handler.compute_twa()
    assert twa == 0, f"Expected TWA to be 0 when no snapshots, got {twa}"


def test_default_behavior_one_deposit_boa(setup_rewards_handler, snapshot_amount):
    rewards_handler = setup_rewards_handler
    twa_window = rewards_handler.twa_window()

    rewards_handler.eval(f"twa._take_snapshot({snapshot_amount})")
    boa.env.time_travel(seconds=twa_window + 1)
    assert rewards_handler.compute_twa() == snapshot_amount


def test_default_behavior_many_deposits_boa(setup_rewards_handler):
    rewards_handler = setup_rewards_handler

    twa_window = rewards_handler.twa_window()
    N_ITER = 10
    AMT_ADD = 10 * 10**18
    for i in range(N_ITER):
        snapshot_amount = AMT_ADD * (i + 1)  # simulate constant tvl growth
        rewards_handler.eval(f"twa._take_snapshot({snapshot_amount})")
        boa.env.time_travel(seconds=twa_window // N_ITER)
    assert rewards_handler.compute_twa() < snapshot_amount
    boa.env.time_travel(seconds=twa_window)
    assert rewards_handler.compute_twa() == snapshot_amount


def test_default_behavior_twa_one_deposit(
    setup_vault, setup_rewards_handler, alice, amt_deposit, stablecoin_lens
):
    vault = setup_vault
    rewards_handler = setup_rewards_handler
    twa_window = rewards_handler.twa_window()

    vault.deposit(amt_deposit, alice, sender=alice)
    rewards_handler.take_snapshot()
    boa.env.time_travel(seconds=twa_window + 1)

    # Compute TWA
    twa = rewards_handler.compute_twa()

    circulating_supply = stablecoin_lens.circulating_supply()
    expected_twa = amt_deposit * 10**4 // circulating_supply

    assert twa == expected_twa, "TWA does not match expected amount"


def test_default_behavior_twa_trapezoid(
    setup_vault, setup_rewards_handler, alice, amt_deposit, stablecoin_lens
):
    vault = setup_vault
    rewards_handler = setup_rewards_handler
    twa_window = rewards_handler.twa_window()

    vault.deposit(amt_deposit, alice, sender=alice)
    rewards_handler.take_snapshot()

    boa.env.time_travel(seconds=twa_window)

    vault.deposit(amt_deposit, alice, sender=alice)
    rewards_handler.take_snapshot()

    # Compute TWA
    twa = rewards_handler.compute_twa()
    # 1.5 * AMT_DEPOSIT because we have two equal deposits and trapezoidal rule
    circulating_supply = stablecoin_lens.circulating_supply()
    expected_twa = 1.5 * amt_deposit * 10**4 // circulating_supply
    assert twa == expected_twa, "TWA does not match expected amount"


def test_default_behavior_twa_multiple_deposits(
    setup_vault, setup_rewards_handler, alice, amt_deposit, stablecoin_lens
):
    vault = setup_vault
    rewards_handler = setup_rewards_handler

    twa_window = rewards_handler.twa_window()

    N_ITER = 5
    time_between_deposits = twa_window // N_ITER

    deposited_supply_rates = []
    timestamps = []

    for i in range(N_ITER):
        vault.deposit(amt_deposit, alice, sender=alice)
        rewards_handler.take_snapshot()

        rate, ts = rewards_handler.snapshots(i)
        deposited_supply_rates.append(rate)
        timestamps.append(ts)

        boa.env.time_travel(seconds=time_between_deposits)

    remaining_time = twa_window - time_between_deposits * N_ITER
    if remaining_time > 0:
        boa.env.time_travel(seconds=remaining_time)

    total_weighted_deposited_supply_rate = 0
    total_time = 0
    for i in range(len(deposited_supply_rates) - 1):
        current_rate = deposited_supply_rates[i]
        next_rate = deposited_supply_rates[i + 1]

        current_timestamp = timestamps[i]
        next_timestamp = timestamps[i + 1]

        time_delta = next_timestamp - current_timestamp

        trapezoidal_rate = (current_rate + next_rate) // 2

        total_weighted_deposited_supply_rate += trapezoidal_rate * time_delta
        total_time += time_delta

    if len(deposited_supply_rates) > 0:
        last_rate = deposited_supply_rates[-1]
        last_timestamp = timestamps[-1]
        time_delta = boa.env.evm.patch.timestamp - last_timestamp

        total_weighted_deposited_supply_rate += last_rate * time_delta
        total_time += time_delta

    expected_twa = total_weighted_deposited_supply_rate // total_time

    twa = rewards_handler.compute_twa()

    total_deposited_amount = amt_deposit * N_ITER
    circulating_supply = stablecoin_lens.circulating_supply()
    deposited_rate = total_deposited_amount * 10**4 // circulating_supply

    assert twa <= deposited_rate, "TWA is unexpectedly higher than the staked rate"
    assert twa == expected_twa, f"TWA {twa} does not match expected {expected_twa}"
