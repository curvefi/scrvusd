FORK_BLOCK_SUPPLY = 62182303636759107878108289


def test_circulating_supply(stablecoin_lens):
    # circ supply for block of fork
    assert stablecoin_lens.circulating_supply() == FORK_BLOCK_SUPPLY
