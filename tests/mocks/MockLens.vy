# pragma version ~=0.4

supply: uint256


@view
@external
def circulating_supply() -> uint256:
    return self.supply
