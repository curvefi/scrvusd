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
def all_stablecoins():
    return [ab.dai, ab.usdt, ab.usdc, ab.usde, ab.frax]


@pytest.fixture(scope="module")
def all_yield_stables():
    return [ab.sdai, ab.sfrax, ab.susde]


@pytest.fixture(scope="module")
def all_cryptos():
    return [ab.weth, ab.steth, ab.wbtc, ab.tbtc]


@pytest.fixture(scope="module")
def stableswap_pool(request, vault, dev_address):
    factory = boa.from_etherscan(ab.factory_stableswap_ng, "factory_stableswap_ng")

    # Retrieve token addresses and asset types from request.param
    token_combo = request.param
    coins = [vault.address] + [token["address"] for token in token_combo]
    asset_types = [3] + [token.get("asset_type") for token in token_combo]

    pool_size = 2
    A = 2000
    fee = 1000000
    ma_exp_time = 866
    implementation_idx = 0
    method_ids = [b""] * pool_size
    oracles = ["0x0000000000000000000000000000000000000000"] * pool_size
    OFFPEG_FEE_MULTIPLIER = 20000000000

    with boa.env.prank(dev_address):
        pool = factory.deploy_plain_pool(
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

    return pool_interface.at(pool)


@pytest.fixture
def add_liquidity(request, vault, dev_address):
    """Fixture to add liquidity to a deployed pool."""

    # Retrieve token addresses and asset types from request.param
    token_combo = request.param
    paired_tokens = [token["address"] for token in token_combo]
    token_contracts = [vault] + [boa.from_etherscan(token, "token") for token in paired_tokens]
    decimals = [token.decimals() for token in token_contracts]

    # Fund `dev_address` with each token
    for i, token in enumerate(token_contracts):
        boa.deal(token, dev_address, 10_000_000 * 10 ** decimals[i])

    # # Call add_liquidity from alice's account
    # with boa.env.prank(alice):
    #     stableswap_pool.add_liquidity([deposit_amount] * n_coins, 0)  # Use 0 for min_mint_amount

    return stableswap_pool  # Return pool with added liquidity


@pytest.fixture(scope="module")
def twocrypto_pool(vault, pair_cryptocoin): ...


@pytest.fixture(scope="module")
def tricrypto_pool(vault): ...
