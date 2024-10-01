import boa

# import hypothesis
from hypothesis import HealthCheck, settings
from hypothesis import strategies as st
from hypothesis.stateful import invariant, rule

from tests.hypothesis.twa.stateful_base import TWAStatefulBase


# Use the twa_testcase_instance fixture to run multiple instances of the test in parallel
def test_state_machine(twa_testcase_instance):
    twa_testcase_instance.run()


@settings(
    max_examples=3,  # 3 examples per workr (set up workers amount in conftest.py)
    stateful_step_count=1000,
    suppress_health_check=[
        HealthCheck.large_base_example
    ],  # skips issue when trying to add 1000 examples with 0 dt
)
class TWAStateful(TWAStatefulBase):

    @invariant()
    def check_initialization(self):
        assert self.twa_window > 0, "TWA window must be set"
        assert self.min_snapshot_dt_seconds > 0, "Minimum snapshot interval must be set"

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
