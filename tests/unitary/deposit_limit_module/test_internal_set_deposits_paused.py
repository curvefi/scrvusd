import boa


def test_default_behavior(deposit_limit_module):
    init_deposit_limit = deposit_limit_module.available_deposit_limit(boa.env.generate_address())

    # Call internal function directly to pause deposits
    deposit_limit_module.eval("self._set_deposits_paused(True)")

    # Verify that deposits are paused
    assert deposit_limit_module.available_deposit_limit(boa.env.generate_address()) == 0

    # now reverse the action
    deposit_limit_module.eval("self._set_deposits_paused(False)")
    assert (
        deposit_limit_module.available_deposit_limit(boa.env.generate_address())
        == init_deposit_limit
    )
