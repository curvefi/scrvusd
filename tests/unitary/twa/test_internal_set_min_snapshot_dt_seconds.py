def test_default_behavior(rewards_handler, rate_manager):
    initial_min_snapshot_dt = rewards_handler.min_snapshot_dt_seconds()

    # Define a new min_snapshot_dt_seconds value
    new_min_snapshot_dt = initial_min_snapshot_dt + 12

    rewards_handler.eval(f"twa._set_snapshot_dt({new_min_snapshot_dt})")
    # Verify event emission
    events = rewards_handler.get_logs()
    assert f"SnapshotIntervalUpdated(new_dt_seconds={new_min_snapshot_dt}" in repr(events)

    # Verify that min_snapshot_dt_seconds has been updated
    updated_min_snapshot_dt = rewards_handler.min_snapshot_dt_seconds()
    assert updated_min_snapshot_dt == new_min_snapshot_dt
