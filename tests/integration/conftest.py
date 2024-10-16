import os
import address_book as ab
import boa
import pytest

boa.set_etherscan(api_key=os.getenv("ETHERSCAN_API_KEY"))
BOA_CACHE = False


@pytest.fixture(autouse=True)
def better_traces(forked_env):
    # contains contracts that are not necessarily called
    # but appear in the traces
    boa.from_etherscan(ab.vault_original, "vault_original")


@pytest.fixture()
def rpc_url():
    return os.getenv("ETH_RPC_URL") or "https://rpc.ankr.com/eth"


@pytest.fixture(autouse=True)
def forked_env(rpc_url):
    block_to_fork = 20928372
    with boa.swap_env(boa.Env()):
        if BOA_CACHE:
            boa.fork(url=rpc_url, block_identifier=block_to_fork)
        else:
            boa.fork(url=rpc_url, block_identifier=block_to_fork, cache_file=None)
        boa.env.enable_fast_mode()
        yield


@pytest.fixture()
def controller_factory():
    return boa.from_etherscan(ab.crvusd_controller_factory, "controller_factory")


@pytest.fixture()
def lens(controller_factory):
    return boa.load("contracts/StablecoinLens.vy", controller_factory)


@pytest.fixture()
def vault_factory():
    return boa.from_etherscan(ab.yearn_vault_factory, "vault_factory")


@pytest.fixture()
def fee_splitter(rewards_handler):
    _fee_splitter_abi = boa.load_vyi("tests/integration/interfaces/IFeeSplitter.vyi")

    _fee_splitter = _fee_splitter_abi.at(ab.fee_splitter)

    receivers = [
        # we add the rewards_handler as a receiver
        (rewards_handler.address, 1_000),
        # dao receives 10% less than what it currently does
        # and it the excess receiver
        (ab.crvusd_fee_collector, 9_000),
    ]

    assert _fee_splitter.excess_receiver() == ab.crvusd_fee_collector

    _fee_splitter.set_receivers(receivers, sender=ab.dao_agent)

    return _fee_splitter


@pytest.fixture()
def crvusd():
    return boa.from_etherscan(ab.crvusd, "crvusd")


@pytest.fixture()
def vault(vault_factory):
    _vault_abi = boa.load_partial("contracts/yearn/VaultV3.vy")

    _vault_addy = vault_factory.deploy_new_vault(
        ab.crvusd,
        "Savings crvUSD",
        "scrvUSD",
        ab.dao_agent,
        86400 * 7,  # 1 week
    )

    _vault = _vault_abi.at(_vault_addy)

    # give the dao total control over the vault
    _vault.set_role(ab.dao_agent, int("11111111111111", 2), sender=ab.dao_agent)
    _vault.set_deposit_limit(2**256 - 1, sender=ab.dao_agent)
    # monkeypatch the contract_name
    _vault.contract_name = "scrvUSD"

    return _vault


@pytest.fixture()
def minimum_weight():
    return 500


@pytest.fixture()
def rewards_handler(vault, minimum_weight):
    rh = boa.load(
        "contracts/RewardsHandler.vy",
        ab.crvusd,
        vault,
        minimum_weight,  # 5%
        10_000,  # 1
        ab.crvusd_controller_factory,
        ab.dao_agent,
    )
    vault.set_role(rh, 2**11 | 2**5 | 2**0, sender=ab.dao_agent)

    # this will always be the same in prod since the
    # only actor authorized to call this is the rewards
    # handler through its own method
    time = vault.profitMaxUnlockTime()
    rh.eval(f"self.distribution_time = {time}")

    return rh


@pytest.fixture()
def active_controllers(fee_splitter):
    # useful to call dispatch_fees
    # we skip the first one as the market is deprecated
    return [fee_splitter.controllers(i) for i in range(1, 6)]
