def test_default_behavior(rewards_handler):
    initial_twa_window = rewards_handler.twa_window()
    new_twa_window = initial_twa_window + 1000  # Increment by 1000 seconds

    rewards_handler.eval(f"twa._set_twa_window({new_twa_window})")
    events = rewards_handler.get_logs()

    # Verify event emission
    assert f"TWAWindowUpdated(new_window={new_twa_window}" in repr(events)

    # Verify that twa_window has been updated
    updated_twa_window = rewards_handler.twa_window()
    assert updated_twa_window == new_twa_window
