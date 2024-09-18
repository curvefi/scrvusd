# pragma version ~=0.4

from interfaces import IPegKeeper
from interfaces import IController
from interfaces import IControllerFactory
from interfaces import IMonetaryPolicy

# bound from factory
MAX_CONTROLLERS: constant(uint256) = 50000
# bound from monetary policy
MAX_PEG_KEEPERS: constant(uint256) = 1001
# could have been any other controller
WETH_CONTROLLER_IDX: constant(uint256) = 3

# the crvusd controller factory
factory: immutable(IControllerFactory)


@deploy
def __init__(_factory: IControllerFactory):
    factory = _factory


@view
@internal
def _circulating_supply() -> uint256:
    """
    @notice Compute the circulating supply for crvUSD, `totalSupply` is
        incorrect since it takes into account all minted crvUSD (i.e. flashloans)
    @dev This function sacrifices some gas to fetch peg keepers from a
        unique source of truth to avoid having to manually maintain multiple
        lists across several contracts.
        For this reason we read the list of peg keepers contained in
        the monetary policy returned by a controller in the factory.
        factory -> weth controller -> monetary policy -> peg keepers
    """

    circulating_supply: uint256 = 0

    # Fetch the weth controller (index 3) under the assumption that
    # weth will always be a valid collateral for crvUSD, therefore its
    # monetary policy should always be up to date.
    controller: IController = staticcall factory.controllers(3)

    # We obtain the address of the current monetary policy used by the
    # weth controller because it contains a list of all the peg keepers.
    monetary_policy: IMonetaryPolicy = staticcall controller.monetary_policy()

    # Iterate over the peg keepers (since it's a fixed size array we
    # wait for a zero address to stop iterating).
    for i: uint256 in range(MAX_PEG_KEEPERS):
        pk: IPegKeeper = staticcall monetary_policy.peg_keepers(i)

        if pk.address == empty(address):
            # end of array
            break

        circulating_supply += staticcall pk.debt()

    n_controllers: uint256 = staticcall factory.n_collaterals()

    for i: uint256 in range(n_controllers, bound=MAX_CONTROLLERS):
        controller = staticcall factory.controllers(i)

        # add crvUSD minted by controller
        circulating_supply += staticcall controller.total_debt()

    return circulating_supply

@external
@view
def circulating_supply() -> uint256:
    return self._circulating_supply()
