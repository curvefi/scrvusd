import boa


def test_add_single_snapshot(setup_rewards_handler, snapshot_amount):
    rewards_handler = setup_rewards_handler

    # Take a snapshot
    rewards_handler.eval(f"twa._store_snapshot({snapshot_amount})")

    initial_len = rewards_handler.get_len_snapshots()
    assert initial_len == 1, f"Expected 1 snapshot, got {initial_len}"


def test_add_snapshot_before_min_interval(
    setup_rewards_handler, snapshot_amount, snapshot_interval
):
    rewards_handler = setup_rewards_handler

    # Take a snapshot
    rewards_handler.eval(f"twa._store_snapshot({snapshot_amount})")

    # Attempt to take another snapshot before min_snapshot_dt_seconds has passed
    boa.env.time_travel(seconds=snapshot_interval // 2)  # Less than one interval
    rewards_handler.eval(f"twa._store_snapshot({snapshot_amount})")

    # Verify that the snapshot was not added
    new_len = rewards_handler.get_len_snapshots()
    assert new_len == 1, f"Snapshot was added too soon; expected 1 snapshot, got {new_len}"


def test_add_snapshot_after_min_interval(setup_rewards_handler, snapshot_amount, snapshot_interval):
    rewards_handler = setup_rewards_handler

    # Take a snapshot
    rewards_handler.eval(f"twa._store_snapshot({snapshot_amount})")

    # Time travel beyond min_snapshot_dt_seconds and take another snapshot
    boa.env.time_travel(
        seconds=snapshot_interval + 10
    )  # Total of snapshot_interval + 10 seconds passed
    rewards_handler.eval(f"twa._store_snapshot({snapshot_amount})")

    # Verify that the snapshot was added
    final_len = rewards_handler.get_len_snapshots()
    assert final_len == 2, f"Expected 2 snapshots, got {final_len}"
