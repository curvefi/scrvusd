def test_default_behavior(rewards_handler, vault):
    assert rewards_handler.vault() == vault.address
