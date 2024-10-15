import address_book as ab
import boa
import pytest


@pytest.fixture()
def alice():
    return boa.env.generate_address()


@pytest.fixture()
def dev_address():
    return boa.env.generate_address()


@pytest.fixture()
def crvusd_init_balance():
    return 1_000 * 10**18


@pytest.fixture()
def stableswap_factory():
    return boa.from_etherscan(ab.factory_stableswap_ng, "factory_stableswap_ng")


@pytest.fixture()
def paired_tokens(request):
    # This fixture is used to get upstream parametrization and populate the contracts
    # Retrieve paired token combination [token1, token2] via request.param
    tokens_list = request.param
    # update the dict with contracts
    for token in tokens_list:
        token["contract"] = boa.from_etherscan(token["address"], token["name"])
        token["decimals"] = token["contract"].decimals()
    return tokens_list


@pytest.fixture()
def pool_tokens(paired_tokens, vault):
    # in any pool first is scrvusd, then one or two other tokens
    return [
        {
            "name": "scrvusd",
            "address": vault.address,
            "contract": vault,
            "asset_type": 3,
            "decimals": 18,
        },
        *paired_tokens,
    ]


@pytest.fixture()
def stableswap_pool(stableswap_factory, vault, dev_address, pool_tokens):
    # Retrieve token addresses and asset types from request.param
    coins = [token["address"] for token in pool_tokens]
    asset_types = [token.get("asset_type") for token in pool_tokens]

    pool_size = len(coins)
    # pool parameters
    A, fee, ma_exp_time, implementation_idx = (2000, 1000000, 866, 0)
    method_ids = [b""] * pool_size
    oracles = ["0x0000000000000000000000000000000000000000"] * pool_size
    offpeg_fee_mp = 20000000000
    # deploy pool
    with boa.env.prank(dev_address):
        pool_address = stableswap_factory.deploy_plain_pool(
            "pool_name",
            "POOL",
            coins,
            A,
            fee,
            offpeg_fee_mp,
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
            boa.deal(token["contract"], dev_address, AMOUNT_STABLE * 10 ** token["decimals"])
        elif token["asset_type"] == 3:
            underlying_token = token["contract"].asset()
            underlying_contract = boa.from_etherscan(underlying_token, "token")
            decimals = underlying_contract.decimals()
            boa.deal(
                underlying_contract,
                dev_address,
                AMOUNT_STABLE * 10**decimals
                + underlying_contract.balanceOf(
                    dev_address
                ),  # in case of dai + sdai deal would overwrite, so we add the previous balance
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
