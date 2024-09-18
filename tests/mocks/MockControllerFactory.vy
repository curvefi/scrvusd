# pragma version ~=0.4.0

from contracts.interfaces import IControllerFactory
from contracts.interfaces import IController

implements: IControllerFactory

_controllers: DynArray[IController, 10000]

@external
@view
def controllers(i: uint256) -> IController:
    return self._controllers[i]

@external
@view
def n_collaterals() -> uint256:
    return len(self._controllers)
