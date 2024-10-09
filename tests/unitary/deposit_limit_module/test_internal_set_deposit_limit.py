# import boa


def test_internal_set_deposit_limit_default_behavior(deposit_limit_module):
    # Define a new deposit limit value
    new_limit = 1_000_000 * 10**18

    # Call the internal function directly to set the max deposit limit
    deposit_limit_module.eval(f"self._set_deposit_limit({new_limit})")

    # Verify that the max_deposit_limit has been updated correctly
    assert deposit_limit_module.max_deposit_limit() == new_limit
