# import boa
# import hypothesis
from hypothesis import note, settings
from hypothesis import strategies as st
from hypothesis.stateful import rule

from tests.hypothesis.twa.stateful_base import TWAStatefulBase


@settings(max_examples=100, stateful_step_count=10)
class TWAStateful(TWAStatefulBase):
    @rule(value=st.integers(min_value=1, max_value=1000))
    def test_rule(self, value):
        note(f"Running test rule with value: {value}")
        pass


TestTWAStateful = TWAStateful.TestCase
