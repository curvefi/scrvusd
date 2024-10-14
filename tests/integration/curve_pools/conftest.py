import address_book as ab
import boa
import pytest


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
