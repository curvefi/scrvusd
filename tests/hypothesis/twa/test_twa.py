import boa
from hypothesis import HealthCheck, Verbosity, settings
from hypothesis import strategies as st
from hypothesis.stateful import invariant, rule

from tests.hypothesis.twa.stateful_base import TWAStatefulBase


def test_state_machine():
    # Explicitly run the state machine
    TestTWAStateful = TWAStateful.TestCase()
    TestTWAStateful.run()


@settings(
    max_examples=10,
    stateful_step_count=1000,
    suppress_health_check=[
        HealthCheck.large_base_example
    ],  # skips issue when trying to add 1000 examples with 0 dt
    verbosity=Verbosity.verbose,
)
class TWAStateful(TWAStatefulBase):

    @invariant()
    def check_initialization(self):
        assert self.twa_window > 0, "TWA window must be set"
        assert self.min_snapshot_dt_seconds > 0, "Minimum snapshot interval must be set"

    @invariant()
    def check_crude_twa_invariant(self):
        """
        Crude invariant to ensure that the computed TWA is reasonable.
        It checks that the TWA is non-negative and is between the minimum and maximum
        values of the snapshots within the TWA window.
        """
        # Get current block timestamp
        current_time = boa.env.evm.patch.timestamp

        # Calculate the time window start
        time_window_start = current_time - self.twa_window

        # Collect snapshots within the TWA window
        snapshots_in_window = [
            snapshot for snapshot in self.snapshots if snapshot["timestamp"] >= time_window_start
        ]

        # Also consider the last snapshot just outside TWA window (needed for trapezoidal rule)
        previous_snapshot = None
        for snapshot in self.snapshots:
            if snapshot["timestamp"] < time_window_start:
                previous_snapshot = snapshot
            else:
                break  # We passed the start of the window

            # If a previous snapshot exists, we add it to the window (on the boundary)
            # not changing timestamp as we only assert values here
            if previous_snapshot:
                snapshots_in_window.append(previous_snapshot)

        # If there are still no snapshots (even outside the window), TWA should be zero
        if not snapshots_in_window:
            contract_twa = self.twa_contract.compute_twa()
            python_twa = self.python_compute_twa()

            # Assert both TWAs are zero
            assert contract_twa == 0, f"Contract TWA should be zero but is {contract_twa}"
            assert python_twa == 0, f"Python TWA should be zero but is {python_twa}"
            return

        # Extract tracked values from snapshots in the window
        tracked_values = [snapshot["tracked_value"] for snapshot in snapshots_in_window]

        # Compute the min and max values of the tracked values
        min_value = min(tracked_values)
        max_value = max(tracked_values)
        # Compute the TWA from the contract and Python model
        contract_twa = self.twa_contract.compute_twa()
        python_twa = self.python_compute_twa()

        # Ensure that the TWA is non-negative
        assert contract_twa >= 0, f"Contract TWA is negative: {contract_twa}"
        assert python_twa >= 0, f"Python TWA is negative: {python_twa}"

        # Ensure that the TWA is between the min and max values of the snapshots
        assert (
            min_value <= contract_twa <= max_value
        ), f"Contract TWA {contract_twa} is not between min {min_value} and max {max_value}"
        assert (
            min_value <= python_twa <= max_value
        ), f"Python TWA {python_twa} is not between min {min_value} and max {max_value}"

    @rule(
        value=st.integers(min_value=0, max_value=100_000_000 * 10**18),  # 0 to 100 million crvUSD
        timestamp_delta=st.integers(
            min_value=0, max_value=10 * 86400
        ),  # 0s to 10 days between snapshots
    )
    def take_snapshot_rule(self, value, timestamp_delta):
        """
        Rule to test taking snapshots in both the Python model and the contract.
        """
        boa.env.time_travel(seconds=timestamp_delta)
        # Call snapshot-taking functions in both the Python model and the contract
        self.twa_contract.eval(f"self._take_snapshot({value})")
        self.python_take_snapshot(value)

        # Assert equal numbe of the snapshots
        contract_snapshot_len = self.twa_contract.get_len_snapshots()
        python_snapshot_len = len(self.snapshots)

        assert contract_snapshot_len == python_snapshot_len, (
            "Mismatch in snapshot length: "
            + f"contract={contract_snapshot_len}, python={python_snapshot_len}"
        )

    @rule(
        timestamp_delta=st.integers(
            min_value=0, max_value=10 * 86400
        ),  # 0s to 10days between compute calls
    )
    def compute_twa_rule(self, timestamp_delta):
        boa.env.time_travel(seconds=timestamp_delta)
        # TWA computation for contract/python model
        contract_twa = self.twa_contract.compute_twa()
        python_twa = self.python_compute_twa()

        # Assert that both values are the same
        assert (
            contract_twa == python_twa
        ), f"Mismatch in TWA: contract={contract_twa}, python={python_twa}"


# TestTWAStateful = TWAStateful.TestCase
