# pragma version ~=0.4.0

from contracts.interfaces import IController
from contracts.interfaces import IMonetaryPolicy

implements: IController

_monetary_policy: address
total_debt: public(uint256)

@external
@view
def monetary_policy() -> IMonetaryPolicy:
    return IMonetaryPolicy(self._monetary_policy)
