# pragma version ~=0.4

from ethereum.ercs import IERC20
import TWAP as twap

stablecoin: immutable(address)
vault: immutable(address)

initializes: twap

# TODO add interface for yearn vault

@deploy
def __init__(_stablecoin: address, _vault: address):
    stablecoin = _stablecoin
    vault = _vault

@external
def take_snapshot():
    total_supply: uint256 = self._get_total_supply()
    supply_in_vault: uint256 = staticcall IERC20(stablecoin).balanceOf(vault)
    supply_ratio: uint256 = supply_in_vault * 10 ** 18 // total_supply

    twap.take_snapshot(supply_ratio)


def _get_total_supply() -> uint256:
    # TODO implement this
    return 0


@external
@view
def tvl_twap() -> uint256:
    return twap.compute()

# TODO implement EIP165 for weight

# TODO implement the rest of the logic to move rewards

@external
@view
def weight() -> uint256:
    return twap.compute()

