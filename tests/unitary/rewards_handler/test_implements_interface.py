SUPPORTED_INTERFACES = [
    b"\x01\xff\xc9\xa7",  # ERC165
    b"\x79\x65\xdb\x0b",  # access_control.vy
    b"\xa1\xaa\xb3\x3f",  # dynamic weight
]


def test_default_behavior(rewards_handler):
    supported_interfaces = [
        rewards_handler.supportsInterface(interface) for interface in SUPPORTED_INTERFACES
    ]
    assert all(supported_interfaces)

    assert not rewards_handler.supportsInterface(b"\xde\xad\xbe\xef")
