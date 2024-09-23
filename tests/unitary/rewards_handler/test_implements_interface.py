SUPPORTED_INTERFACES = [
    b"\x01\xFF\xC9\xA7",  # ERC165
    b"\x79\x65\xDB\x0B",  # access_control.vy
    b"\xA1\xAA\xB3\x3F",  # dynamic weight
]


def test_default_behavior(rewards_handler):
    supported_interfaces = [
        rewards_handler.supportsInterface(interface) for interface in SUPPORTED_INTERFACES
    ]
    assert all(supported_interfaces)

    assert not rewards_handler.supportsInterface(b"\xde\xad\xbe\xef")
