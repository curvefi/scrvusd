# pragma version ~=0.4

debt: public(uint256)


@deploy
def __init__(circulating_supply: uint256):
    self.debt = circulating_supply
