import boa


def test_default_behavior(rewards_handler, curve_dao):
    initial_min_snapshot_dt = rewards_handler.min_snapshot_dt_seconds()

    # Define a new min_snapshot_dt_seconds value
    new_min_snapshot_dt = initial_min_snapshot_dt + 12

    with boa.env.prank(curve_dao):
        rewards_handler.set_twa_snapshot_dt(new_min_snapshot_dt)

    # Verify that min_snapshot_dt_seconds has been updated
    updated_min_snapshot_dt = rewards_handler.min_snapshot_dt_seconds()
    assert updated_min_snapshot_dt == new_min_snapshot_dt
