import boa


def test_default_behavior(deposit_limit_module):
    address = boa.env.generate_address()

    # Call internal function directly to set security_agent status to a generated address
    deposit_limit_module.eval(f"self._set_security_agent({address}, True)")

    # Verify that the address is now a security_agent
    assert deposit_limit_module.is_security_agent(address)

    # Revoke security_agent role using the internal function
    deposit_limit_module.eval(f"self._set_security_agent({address}, False)")

    # Verify that the address is no longer a security_agent
    assert not deposit_limit_module.is_security_agent(address)
