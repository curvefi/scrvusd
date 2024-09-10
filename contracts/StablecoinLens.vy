# pragma version ~=0.4

from interfaces import IPegKeeper
from interfaces import IController

MAX_CONTROLLERS: constant(uint256) = 50000 # TODO check actual number
MAX_PEG_KEEPERS: constant(uint256) = 100 # TODO check actual number

controllers: DynArray[address, MAX_CONTROLLERS]
peg_keepers: DynArray[address, MAX_PEG_KEEPERS]


@view
@external
def circulating_supply() -> uint256:
    total_supply: uint256 = 0

    # TODO how to optimize this
    for pk: address in self.peg_keepers:
        if pk != empty(address):
            total_supply += staticcall IPegKeeper(pk).debt()

    # TODO get correct value for this
    n_controllers: uint256 = 0
    for i: uint256 in range(n_controllers, bound=MAX_CONTROLLERS):
        controller: address = self.controllers[i]
        total_supply += staticcall IController(controller).total_debt()

    return total_supply
