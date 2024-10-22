import pytest
import boa

FORK_BLOCK_SUPPLY = 62247189465433688283786326


def test_circulating_supply(stablecoin_lens):
    # circ supply for block of fork
    assert stablecoin_lens.circulating_supply() == FORK_BLOCK_SUPPLY


@pytest.mark.ignore_isolation
def test_gas_cost(stablecoin_lens):
    boa.env.reset_gas_used()
    _ = stablecoin_lens.circulating_supply()
    print(f"Compute TWA gas: {stablecoin_lens.call_trace().gas_used}")
