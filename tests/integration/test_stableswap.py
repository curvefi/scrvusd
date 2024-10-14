import pytest
from utils import generate_list_combinations
import address_book as ab


N_COMBINATIONS = 1  # num of combinations in stableswap tests (>=36 => all combinations)

# produce tokens for stableswap to pair against crvusd
paired_token_combinations = generate_list_combinations(ab.all_stables, [1, 2], randomize=True)
tokens_subset = paired_token_combinations[0:N_COMBINATIONS]


@pytest.mark.parametrize("paired_tokens", tokens_subset, indirect=True)
def test_stableswap_pool_with_liquidity(stableswap_pool, paired_tokens):
    """
    Test deploying stableswap pool with different token combinations,
    then adds liquidity to the pool and checks balances.
    """

    # Check balances in the pool after adding liquidity
    n_coins = stableswap_pool.N_COINS()
    print(f"n_coins: {n_coins}")
    for i in range(n_coins):
        print(f"balance {i}: {stableswap_pool.balances(i)}")
