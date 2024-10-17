import pytest
import boa


@pytest.mark.gas_profile
def test_take_snapshot_compute(rewards_handler):
    n_days = 7
    dt = 600
    snaps_per_day = 86_400 // dt
    for i_day in range(n_days):
        for i_snap in range(snaps_per_day):
            rewards_handler.take_snapshot()
            boa.env.time_travel(seconds=dt)
        twa = rewards_handler.compute_twa()
        assert twa >= 0, f"Computed TWA is negative: {twa}"
