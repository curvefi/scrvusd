import os
import address_book as ab
import boa
import pytest

boa.set_etherscan(api_key=os.getenv("ETHERSCAN_API_KEY"))
BOA_CACHE = False


@pytest.fixture(autouse=True, scope="module")
def better_traces(forked_env):
    # contains contracts that are not necessarily called
    # but appear in the traces
    boa.from_etherscan(ab.vault_original, "vault_original")


@pytest.fixture(scope="session")
def rpc_url():
    return os.getenv("ETH_RPC_URL") or "https://rpc.ankr.com/eth"


@pytest.fixture(scope="module", autouse=True)
def forked_env(rpc_url):
    block_to_fork = 20928372
    with boa.swap_env(boa.Env()):
        if BOA_CACHE:
            boa.fork(url=rpc_url, block_identifier=block_to_fork)
        else:
            boa.fork(url=rpc_url, block_identifier=block_to_fork, cache_file=None)
        boa.env.enable_fast_mode()
        yield


@pytest.fixture(scope="module")
def controller_factory():
    return boa.from_etherscan(ab.crvusd_controller_factory, "controller_factory")


@pytest.fixture(scope="module")
def lens(controller_factory):
    return boa.load("contracts/StablecoinLens.vy", controller_factory)


@pytest.fixture(scope="module")
def vault_factory():
    return boa.from_etherscan(ab.yearn_vault_factory, "vault_factory")


@pytest.fixture(scope="module")
def fee_splitter():
    _factory = boa.load_vyi("tests/integration/interfaces/IFeeSplitter.vyi")
    return _factory.at(ab.fee_splitter)


@pytest.fixture(scope="module")
def crvusd():
    return boa.from_etherscan(ab.crvusd, "crvusd")


@pytest.fixture(scope="module")
def vault(vault_factory):
    _vault_abi = boa.load_partial("contracts/yearn/VaultV3.vy")

    _vault_addy = vault_factory.deploy_new_vault(
        ab.crvusd,
        "Savings crvUSD",
        "scrvUSD",
        # TODO figure out who's going to be the role manager
        ab.dao_agent,
        86400 * 7,  # 1 week
    )

    _vault = _vault_abi.at(_vault_addy)

    # give the dao total control over the vault
    _vault.set_role(ab.dao_agent, int("11111111111111", 2), sender=ab.dao_agent)
    _vault.set_deposit_limit(2**256 - 1, sender=ab.dao_agent)
    return _vault


@pytest.fixture(scope="function")
def rewards_handler(vault):
    rh = boa.load(
        "contracts/RewardsHandler.vy",
        ab.crvusd,
        vault,
        500,  # 5%
        10_000,  # 1
        ab.crvusd_controller_factory,
        ab.dao_agent,
    )
    vault.set_role(rh, 2**11 | 2**5 | 2**0, sender=ab.dao_agent)
    return rh


@pytest.fixture(scope="module")
def dev_address():
    return boa.env.generate_address()
