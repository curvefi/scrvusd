import boa


def test_deploy_vault(vault_factory, crvusd):
    vault = vault_factory.deploy_new_vault(
        crvusd,
        "Staked crvUSD",
        "st-crvUSD",
        # TODO figure out who's going to be the role manager
        boa.env.generate_address(),
        1234,
    )
    vault = boa.load_partial("contracts/yearn/VaultV3.vy").at(vault)
    assert vault.name() == "Staked crvUSD"
