import pytest
import boa
from utils import generate_list_combinations
import address_book as ab


N_COMBINATIONS = 3  # num of combinations in stableswap tests (>=36 => all combinations)

# produce tokens for stableswap to pair against crvusd
paired_token_combinations = generate_list_combinations(ab.all_stables, [1, 2], randomize=True)
tokens_subset = paired_token_combinations[0:N_COMBINATIONS]


def test_accrue_value(alice, dev_deployer, vault, crvusd, crvusd_init_balance):
    # fund alice
    assert crvusd.balanceOf(alice) == 0
    boa.deal(crvusd, alice, crvusd_init_balance)
    with boa.env.prank(alice):
        crvusd.approve(vault, crvusd_init_balance)
        vault.deposit(crvusd_init_balance, alice)

    # basic boilerplate test to check vault functionality of rewards accrual without pools involved
    alice_value_0 = vault.convertToAssets(vault.balanceOf(alice))

    # deposit crvusd rewards into vault & time travel
    boa.deal(crvusd, dev_deployer, crvusd_init_balance)
    crvusd.transfer(vault, crvusd_init_balance, sender=dev_deployer)
    vault.process_report(vault, sender=ab.dao_agent)
    boa.env.time_travel(seconds=86_400 * 7)

    # check alice's assets value increased
    alice_value_1 = vault.convertToAssets(vault.balanceOf(alice))
    assert alice_value_1 > alice_value_0
    assert alice_value_1 == alice_value_0 + crvusd_init_balance


@pytest.mark.parametrize(
    "paired_tokens",
    tokens_subset,
    indirect=True,
    ids=[f"scrvusd+{'+'.join([token['name'] for token in tokens])}" for tokens in tokens_subset],
)
def test_stableswap_pool_liquidity(
    stableswap_pool,
    paired_tokens,
    vault,
    alice,
    dev_deployer,
    crvusd_init_balance,
    crvusd,
):
    # test where we check that value grows even when deposited as LP
    n_coins = stableswap_pool.N_COINS()
    # fund alice
    assert crvusd.balanceOf(alice) == 0
    boa.deal(crvusd, alice, crvusd_init_balance)
    with boa.env.prank(alice):
        crvusd.approve(vault, crvusd_init_balance)
        vault.deposit(crvusd_init_balance, alice)

    alice_value_0 = vault.convertToAssets(vault.balanceOf(alice))
    alice_rate = alice_value_0 / vault.totalAssets()
    # deposit single-sided scrvusd liq into pool (i.e. trade into equal parts)
    add_liq_amounts = [0] * n_coins
    add_liq_amounts[0] = vault.balanceOf(alice)
    vault.approve(stableswap_pool, add_liq_amounts[0], sender=alice)
    pool_shares = stableswap_pool.add_liquidity(add_liq_amounts, 0, alice, sender=alice)
    assert stableswap_pool.balanceOf(alice) > 0

    # now increase shares value by 5%
    amt_reward = int(vault.totalAssets() * 0.05)
    boa.deal(crvusd, dev_deployer, amt_reward)
    crvusd.transfer(vault, amt_reward, sender=dev_deployer)
    vault.process_report(vault, sender=ab.dao_agent)
    boa.env.time_travel(seconds=86_400 * 7)

    # remove liq (one-sided)
    stableswap_pool.remove_liquidity_one_coin(pool_shares, 0, 0, alice, sender=alice)
    alice_value_1 = vault.convertToAssets(vault.balanceOf(alice))

    alice_expected_full_reward = alice_rate * amt_reward
    # because we deposited LP, we only get 1/N_COINS of the reward (50% or 33% for 2, 3 coins)
    # relative tolerance because of one-sided LP deposit & withdraw eat fees
    # 5% relative tolerance to expected reward
    assert alice_value_1 - alice_value_0 == pytest.approx(
        alice_expected_full_reward / n_coins, rel=0.05
    )


@pytest.mark.parametrize(
    "paired_tokens",
    tokens_subset,
    indirect=True,
    ids=[f"scrvusd+{'+'.join([token['name'] for token in tokens])}" for tokens in tokens_subset],
)
def test_stableswap_pool_prices_with_vault_growth(
    stableswap_pool, pool_tokens, vault, dev_deployer, crvusd, paired_tokens
):
    """
    Test where vault shares grow (rewards airdropped), and we expect that pool prices change accordingly.
    To balance the pool, dev removes liquidity in a balanced way at each iteration.
    """
    n_coins = stableswap_pool.N_COINS()
    growth_rate = 0.01  # Vault growth per iteration (1%)
    airdropper = boa.env.generate_address()
    decimals = [token["decimals"] for token in pool_tokens]
    prev_dy = [stableswap_pool.get_dy(0, i, 10 ** decimals[0]) for i in range(1, n_coins)]
    # Iteratively grow vault and adjust pool prices
    for _ in range(10):  # Run 10 iterations
        # Step 1: Inflate vault by 1%
        current_assets = vault.totalAssets()
        amt_reward = int(current_assets * growth_rate)
        boa.deal(crvusd, airdropper, amt_reward)
        crvusd.transfer(vault, amt_reward, sender=airdropper)
        vault.process_report(vault, sender=ab.dao_agent)
        boa.env.time_travel(seconds=86_400 * 7)

        # Step 2: Dev removes 5% of liquidity in a balanced way
        stableswap_pool.remove_liquidity(
            stableswap_pool.balanceOf(dev_deployer) // 20,
            [0] * n_coins,
            dev_deployer,
            True,
            sender=dev_deployer,
        )
        # Check pool prices after each iteration
        cur_dy = [stableswap_pool.get_dy(0, i, 10 ** decimals[0]) for i in range(1, n_coins)]
        for i in range(n_coins - 1):
            assert cur_dy[i] > prev_dy[i]  # important that in balanced pool dy increases
            assert (
                cur_dy[i] / prev_dy[i] - 1 == pytest.approx(growth_rate, rel=0.2)
            )  # price should grow along with vault (fees tolerated, we approx 1% growth with 20% tolerance)
            prev_dy[i] = cur_dy[i]
