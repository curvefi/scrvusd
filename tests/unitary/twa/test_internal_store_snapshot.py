import boa


def test_default_behavior(rewards_handler):
    # Set minimum snapshot interval to 100 seconds
    rewards_handler.eval("twa.min_snapshot_dt_seconds = 100")

    # Take a snapshot
    rewards_handler.eval("twa._store_snapshot(100 * 10**18)")

    initial_len = rewards_handler.get_len_snapshots()
    assert initial_len == 1, f"Expected 1 snapshot, got {initial_len}"

    # Attempt to take another snapshot before min_snapshot_dt_seconds has passed
    boa.env.time_travel(seconds=50)  # Less than 100 seconds
    rewards_handler.eval("twa._store_snapshot(200 * 10**18)")

    # Verify that the snapshot was not added
    new_len = rewards_handler.get_len_snapshots()
    assert new_len == 1, f"Snapshot was added too soon; expected 1 snapshot, got {new_len}"

    # Time travel beyond min_snapshot_dt_seconds and take another snapshot
    boa.env.time_travel(seconds=60)  # Total of 110 seconds passed
    rewards_handler.eval("twa._store_snapshot(200 * 10**18)")

    # Verify that the snapshot was added
    final_len = rewards_handler.get_len_snapshots()
    assert final_len == 2, f"Expected 2 snapshots, got {final_len}"
