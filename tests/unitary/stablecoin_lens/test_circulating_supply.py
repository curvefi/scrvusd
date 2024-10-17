from conftest import MOCK_CRV_USD_CIRCULATING_SUPPLY


def test_circulating_supply(stablecoin_lens):
    assert stablecoin_lens.circulating_supply() == MOCK_CRV_USD_CIRCULATING_SUPPLY
