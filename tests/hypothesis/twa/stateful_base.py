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
        min_snapshot_dt_seconds=st.integers(min_value=1, max_value=86400),  # 1 second to 1 day
    )
    def setup(self, twa_window, min_snapshot_dt_seconds):
        """Initialize the TWA contract and set up initial parameters."""
        note("SETUP")
        self.twa_contract = TWAStatefulBase.twa_deployer(twa_window, min_snapshot_dt_seconds)

        self.twa_window = twa_window
        self.min_snapshot_dt_seconds = min_snapshot_dt_seconds
        self.snapshots = []
        self.last_snapshot_timestamp = 0

    def python_take_snapshot(self, value):
        """
        Python model of the contract's `_take_snapshot` function.
        Mirrors the contract logic and updates the internal state.
        """
        # Contract logic: only take a snapshot if the time condition is met
        block_timestamp = boa.env.evm.patch.timestamp
        if self.last_snapshot_timestamp + self.min_snapshot_dt_seconds <= block_timestamp:
            self.last_snapshot_timestamp = block_timestamp
            self.snapshots.append({"tracked_value": value, "timestamp": block_timestamp})
            note(
                f"python_take_snapshot: Python snapshot added: value={value}, timestamp={block_timestamp}"  # noqa: E501
            )
        else:
            note("python_take_snapshot: Python snapshot skipped (time condition not met)")

    def python_compute_twa(self):
        """
        Python version of the contract's _compute function.
        Computes the TWA (Time-Weighted Average) based on the snapshots in self.snapshots.
        """
        block_timestamp = boa.env.evm.patch.timestamp

        num_snapshots = len(self.snapshots)
        if num_snapshots == 0:
            note("python_compute_twa: No snapshots, no TWA")
            return 0

        time_window_start = block_timestamp - self.twa_window

        total_weighted_tracked_value = 0
        total_time = 0

        # Iterate backwards over all snapshots
        index_array_end = num_snapshots - 1
        for i in range(0, num_snapshots):
            i_backwards = index_array_end - i
            current_snapshot = self.snapshots[i_backwards]
            next_snapshot = current_snapshot

            if i != 0:  # If not the first iteration, get the next snapshot
                next_snapshot = self.snapshots[i_backwards + 1]

            interval_start = current_snapshot["timestamp"]

            # Adjust interval start if it is before the time window start
            if interval_start < time_window_start:
                interval_start = time_window_start

            if i == 0:
                # For the last snapshot, interval end is the block_timestamp
                interval_end = block_timestamp
            else:
                # For other snapshots, interval end is the timestamp of the next snapshot
                interval_end = next_snapshot["timestamp"]

            if interval_end <= time_window_start:
                break

            time_delta = interval_end - interval_start

            # Interpolation using the trapezoidal rule
            averaged_tracked_value = (
                current_snapshot["tracked_value"] + next_snapshot["tracked_value"]
            ) // 2

            # Accumulate weighted rate and time
            total_weighted_tracked_value += averaged_tracked_value * time_delta
            total_time += time_delta

        if total_time == 0 and len(self.snapshots) == 1:
            # case when only snapshot is taken in the block where computation is called
            return self.snapshots[0]["tracked_value"]

        # Ensure there is non-zero time for division
        if total_time == 0:
            raise ValueError("TWA: Zero total time!")

        # Calculate TWA
        twa = total_weighted_tracked_value // total_time
        note(f"python_compute_twa: Computed TWA: {twa}")
        return twa
