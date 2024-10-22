import pytest
import boa


@pytest.mark.ignore_isolation
def test_take_snapshot_compute(vault, rewards_handler):
    n_days = 7
    dt = 3600
    snaps_per_day = 86_400 // dt
    for i_day in range(n_days):
        for i_snap in range(snaps_per_day):
            rewards_handler.take_snapshot()
            boa.env.time_travel(seconds=dt)
        boa.env.reset_gas_used()
        twa = rewards_handler.compute_twa()
        print(f"Compute TWA gas: {rewards_handler.call_trace().gas_used}")
        # print(rewards_handler._computation.get_gas_used())
        assert twa >= 0, f"Computed TWA is negative: {twa}"
