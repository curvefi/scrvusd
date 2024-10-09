import boa


def test_default_behavior(deposit_limit_module):
    address = boa.env.generate_address()
    # Call internal function directly to set admin status to random addres
    deposit_limit_module.eval(f"self._set_admin({address}, True)")

    # Verify that curve_dao is now an admin
    assert deposit_limit_module.is_admin(address)

    # Revoke admin role
    deposit_limit_module.eval(f"self._set_admin({address}, False)")

    # Verify that curve_dao is no longer an admin
    assert not deposit_limit_module.is_admin(address)
