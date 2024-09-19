import boa


def test_set_twa_window(rewards_handler, curve_dao):
    initial_twa_window = rewards_handler.twa_window()
    new_twa_window = initial_twa_window + 1000  # Increment by 1000 seconds

    with boa.env.prank(curve_dao):
        rewards_handler.set_twa_window(new_twa_window)

    # Verify that twa_window has been updated
    updated_twa_window = rewards_handler.twa_window()
    assert updated_twa_window == new_twa_window
