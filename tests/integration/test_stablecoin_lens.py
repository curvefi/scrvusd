FORK_BLOCK_SUPPLY = 61914061856509260204722729


def test_circulating_supply(stablecoin_lens):
    # circ supply for block of fork
    assert stablecoin_lens.circulating_supply() == FORK_BLOCK_SUPPLY
