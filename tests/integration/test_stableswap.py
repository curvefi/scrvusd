import pytest

from utils import generate_token_combinations
import address_book as ab


@pytest.mark.parametrize(
    "stableswap_pool",
    generate_token_combinations(ab.all_stables),  # Generate token combinations
    indirect=True,  # Pass token combinations to the fixture
)
def test_stableswap_pool_with_liquidity(stableswap_pool, add_liquidity):
    """
    Test deploying stableswap pool with different token combinations,
    then adds liquidity to the pool and checks balances.
    """

    # Check balances in the pool after adding liquidity
    n_coins = stableswap_pool.n_coins()
    print(f"n_coins: {n_coins}")
    for i in range(n_coins):
        print(f"balance {i}: {stableswap_pool.balances(i)}")
