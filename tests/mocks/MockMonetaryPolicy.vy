# pragma version ~=0.4.0

from contracts.interfaces import IMonetaryPolicy
from contracts.interfaces import IPegKeeper

implements: IMonetaryPolicy

peg_keeper_array: IPegKeeper[1000]


@external
@view
def peg_keepers(i: uint256) -> IPegKeeper:
    return self.peg_keeper_array[i]
