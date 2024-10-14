import os
import address_book as ab
import boa
import pytest

boa.set_etherscan(api_key=os.getenv("ETHERSCAN_API_KEY"))


@pytest.fixture(autouse=True, scope="module")
def better_traces(forked_env):
    # contains contracts that are not necessarily called
    # but appear in the traces
    boa.from_etherscan(ab.vault_original, "vault_original")


@pytest.fixture(scope="module")
def rpc_url():
    return os.getenv("ETH_RPC_URL") or "https://rpc.ankr.com/eth"


@pytest.fixture(scope="module", autouse=True)
def forked_env(rpc_url):
    block_to_fork = 20928372
    with boa.swap_env(boa.Env()):
        boa.fork(url=rpc_url, block_identifier=block_to_fork)
        # use this to disable caching
        # boa.fork(url=rpc_url, block_identifier=block_to_fork, cache_file=None)
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
def fee_splitter(scope="module"):
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


@pytest.fixture(scope="module")
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


@pytest.fixture(scope="module")
def stableswap_factory():
    return boa.from_etherscan(ab.factory_stableswap_ng, "factory_stableswap_ng")


@pytest.fixture(scope="module")
def paired_tokens(request):
    # This fixture is used to get upstream parametrization and populate the contracts
    # Retrieve paired token combinations via request.param
    tokens_list = request.param
    # update the dict with contracts
    for token in tokens_list:
        token["contract"] = boa.from_etherscan(token["address"], token["name"])
    return tokens_list


@pytest.fixture(scope="module")
def stableswap_pool(stableswap_factory, vault, dev_address, paired_tokens):
    # Retrieve token addresses and asset types from request.param
    pool_tokens = [
        {"asset_type": 3, "name": "scrvusd", "address": vault.address, "contract": vault},
        *paired_tokens,
    ]
    coins = [token["address"] for token in pool_tokens]
    asset_types = [token.get("asset_type") for token in pool_tokens]

    pool_size = len(coins)
    # pool parameters
    A, fee, ma_exp_time, implementation_idx = (2000, 1000000, 866, 0)
    method_ids = [b""] * pool_size
    oracles = ["0x0000000000000000000000000000000000000000"] * pool_size
    OFFPEG_FEE_MULTIPLIER = 20000000000

    # deploy pool
    with boa.env.prank(dev_address):
        pool_address = stableswap_factory.deploy_plain_pool(
            "pool_name",
            "POOL",
            coins,
            A,
            fee,
            OFFPEG_FEE_MULTIPLIER,
            ma_exp_time,
            implementation_idx,
            asset_types,
            method_ids,
            oracles,
        )
    pool_interface = boa.load_vyi("tests/integration/interfaces/CurveStableSwapNG.vyi")
    pool = pool_interface.at(pool_address)
    # fund dev with tokens (free-mint erc20s and deposit vaults)
    AMOUNT_STABLE = 1_000_000
    dev_balances = []
    for token in pool_tokens:
        if token["asset_type"] == 0:
            boa.deal(
                token["contract"], dev_address, AMOUNT_STABLE * 10 ** token["contract"].decimals()
            )
        elif token["asset_type"] == 3:
            underlying_token = token["contract"].asset()
            underlying_contract = boa.from_etherscan(underlying_token, "token")
            decimals = underlying_contract.decimals()
            boa.deal(
                underlying_contract,
                dev_address,
                AMOUNT_STABLE * 10**decimals,
            )
            underlying_contract.approve(
                token["contract"],
                AMOUNT_STABLE * 10**decimals,
                sender=dev_address,
            )
            token["contract"].deposit(AMOUNT_STABLE * 10**decimals, dev_address, sender=dev_address)
        # Approve pool to spend vault tokens
        token["contract"].approve(pool, 2**256 - 1, sender=dev_address)
        dev_balances.append(token["contract"].balanceOf(dev_address))
    pool.add_liquidity(dev_balances, 0, dev_address, sender=dev_address)
    return pool


@pytest.fixture(scope="module")
def twocrypto_pool(vault, pair_cryptocoin): ...


@pytest.fixture(scope="module")
def tricrypto_pool(vault): ...
