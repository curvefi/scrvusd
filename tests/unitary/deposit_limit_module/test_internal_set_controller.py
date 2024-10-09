import boa


def test_default_behavior(deposit_limit_module):
    address = boa.env.generate_address()

    # Call internal function directly to set controller status to a generated address
    deposit_limit_module.eval(f"self._set_controller({address}, True)")

    # Verify that the address is now a controller
    assert deposit_limit_module.is_controller(address)

    # Revoke controller role using the internal function
    deposit_limit_module.eval(f"self._set_controller({address}, False)")

    # Verify that the address is no longer a controller
    assert not deposit_limit_module.is_controller(address)
