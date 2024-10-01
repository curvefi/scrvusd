import boa
from hypothesis import note
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize  # , invariant, rule


class TWAStatefulBase(RuleBasedStateMachine):
    twa_deployer = boa.load_partial("contracts/TWA.vy")

    def __init__(self):
        super().__init__()
        note("INIT")
        self.twa_contract = None
        self.twa_window = None
        self.min_snapshot_dt_seconds = None
        self.snapshots = []
        self.last_snapshot_timestamp = 0

    @initialize(
        twa_window=st.integers(min_value=1, max_value=86400 * 7),  # 1 second to 1 week
        min_snapshot_dt_seconds=st.integers(min_value=1, max_value=3600),  # 1 second to 1 hour
    )
    def setup(self, twa_window, min_snapshot_dt_seconds):
        """Initialize the TWA contract and set up initial parameters."""
        note("SETUP")
        self.twa_contract = TWAStatefulBase.twa_deployer(twa_window, min_snapshot_dt_seconds)

        self.twa_window = twa_window
        self.min_snapshot_dt_seconds = min_snapshot_dt_seconds
        self.snapshots = []
        self.last_snapshot_timestamp = 0

    # def python_take_snapshot(self, value, timestamp):
    #     """
    #     Python model of the contract's `_take_snapshot` function.
    #     Mirrors the contract logic and updates the internal state.
    #     """
    #     # Contract logic: only take a snapshot if the time condition is met
    #     if self.last_snapshot_timestamp + self.min_snapshot_dt_seconds <= timestamp:
    #         self.last_snapshot_timestamp = timestamp
    #         self.snapshots.append({"tracked_value": value, "timestamp": timestamp})
    #         note(f"Python snapshot added: value={value}, timestamp={timestamp}")
    #     else:
    #         note("Python snapshot skipped (time condition not met)")
