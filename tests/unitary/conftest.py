import boa
import pytest


@pytest.fixture(scope="module")
def yearn_gov():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def vault_original():
    return boa.load("contracts/yearn/Vault.vy")


@pytest.fixture(scope="module")
def vault_factory(vault_original, yearn_gov):
    return boa.load(
        "contracts/yearn/VaultFactory.vy",
        "mock factory",
        vault_original,
        yearn_gov,
    )


@pytest.fixture(scope="module")
def crvusd():
    return boa.load("tests/mocks/MockERC20.vy")


@pytest.fixture(scope="module")
def role_manager():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def vault(vault_factory, crvusd, role_manager):
    vault_deployer = boa.load_partial("contracts/yearn/Vault.vy")

    address = vault_factory.deploy_new_vault(
        crvusd, "Staked crvUSD", "st-crvUSD", role_manager, 0
    )

    return vault_deployer.at(address)


@pytest.fixture(scope="module")
def lens():
    lens = boa.load("tests/mocks/MockLens.vy")

    lens.eval("self.supply = 10 ** 24")

    return lens


@pytest.fixture(scope="module")
def rewards_handler(vault, crvusd, role_manager):
    rh = boa.load("contracts/RewardsHandler.vy", crvusd, vault)

    vault.set_role(rh, 2**11 | 2**5 | 2**0, sender=role_manager)

    return rh
