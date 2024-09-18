# pragma version ~=0.4

from ethereum.ercs import IERC20
from ethereum.ercs import IERC165

from interfaces import IVault
from interfaces import IControllerFactory

from snekmate.auth import access_control

import StablecoinLens as lens

initializes: access_control

import TWA as twa
initializes: twa
exports: (
    # TODO add missing getters
    twa.compute_twa,
    twa.snapshots,
    twa.get_len_snapshots,
    twa.twa_window,
    # we don't expose `supportsInterface` from access control
    access_control.grantRole,
    access_control.revokeRole,
    access_control.renounceRole,
    access_control.set_role_admin,
    access_control.DEFAULT_ADMIN_ROLE,
    access_control.hasRole,
    access_control.getRoleAdmin,
)

implements: IERC165
initializes: lens

RATE_MANAGER: public(constant(bytes32)) = keccak256("RATE_MANAGER")
WEEK: constant(uint256) = 86400 * 7  # 7 days

_SUPPORTED_INTERFACES: constant(bytes4[3]) = [
    0x01FFC9A7,  # The ERC-165 identifier for ERC-165.
    0x7965DB0B,  # The ERC-165 identifier for `IAccessControl`.
    0xA1AAB33F,  # The ERC-165 identifier for the dynamic weight interface.
]

stablecoin: immutable(IERC20)
vault: immutable(IVault)

minimum_weight: public(uint256)


@deploy
def __init__(
    _stablecoin: IERC20,
    _vault: IVault,
    minimum_weight: uint256,
    controller_factory: IControllerFactory,
    admin: address
):
    lens.__init__(controller_factory)

    access_control.__init__()
    access_control._set_role_admin(RATE_MANAGER, access_control.DEFAULT_ADMIN_ROLE)
    access_control._grant_role(access_control.DEFAULT_ADMIN_ROLE, admin)
    access_control._revoke_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)

    twa.__init__(
        WEEK,  # twa_window = 1 week
        1,  #  min_snapshot_dt_seconds = 1 second (if 0, then spam is possible)
    )

    stablecoin = _stablecoin
    vault = _vault

################################################################
#                   PERMISSIONLESS FUNCTIONS                   #
################################################################

@external
def take_snapshot():
    """
    @notice Function that anyone can call to take a
        snapshot of the current balance/supply ratio
        in the vault. This is used to compute the
        time-weighted average of the TVL to decide
        on the amount of rewards to ask for (weight).
    """

    # get the circulating supply from a helper function
    # (supply in circulation = controllers' debt + peg
    # keppers' debt)
    circulating_supply: uint256 = lens._circulating_supply()

    # obtain the supply of crvUSD contained in the
    # vault by simply checking its balance since it's
    # an ERC4626 vault. This will also take into account
    # rewards that are not yet distributed.
    supply_in_vault: uint256 = staticcall stablecoin.balanceOf(vault.address)

    supply_ratio: uint256 = supply_in_vault * 10**18 // circulating_supply

    twa.store_snapshot(supply_ratio)


@external
def process_rewards():
    """
    @notice Permissionless function that let anyone
    distribute rewards (if any) to the crvUSD vault.
    """

    # any crvUSD sent to this contract (usually
    # through the fee splitter, but could also
    # come from other sources) will be used as
    # a reward for crvUSD stakers in the vault.
    available_balance: uint256 = staticcall stablecoin.balanceOf(self)

    # we distribute funds in 2 steps:
    # 1. transfer the actual funds
    extcall stablecoin.transfer(vault.address, available_balance)
    # 2. start streaming the rewards to users
    extcall vault.process_report(vault.address)


################################################################
#                         VIEW FUNCTIONS                       #
################################################################


@external
@view
def supportsInterface(interface_id: bytes4) -> bool:
    """
    @dev Returns `True` if this contract implements the
         interface defined by `interface_id`.
    @param interface_id The 4-byte interface identifier.
    @return bool The verification whether the contract
            implements the interface or not.
    """
    return interface_id in _SUPPORTED_INTERFACES


@external
@view
def weight() -> uint256:
    """
    @notice this function is part of the dynamic weight
        interface expected by the FeeSplitter to know
        what percentage of funds should be sent for
        rewards distribution to crvUSD stakerks.
    @dev `minimum_weight` acts as a lower bound for
        the percentage of rewards that should be
        distributed to stakers. This is useful to
        bootstrapping TVL by asking for more at the
        beginning and can also be increased in the
        future if someone tries to manipulate the
        time-weighted average of the tvl ratio.
    """
    return max(twa.compute(), self.minimum_weight)


################################################################
#                         ADMIN FUNCTIONS                      #
################################################################


@external
def set_twa_frequency(_min_snapshot_dt_seconds: uint256):
    """
    @notice Setter for the time-weighted average minimal
        frequency.
    @param _min_snapshot_dt_seconds The minimum amount of
        time that should pass between two snapshots.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)
    twa.set_min_snapshot_dt_seconds(_min_snapshot_dt_seconds)


@external
def set_twa_window(_twa_window: uint256):
    """
    @notice Setter for the time-weighted average window
    @param _twa_window The time window used to compute
        the TWA value of the balance/supply ratio.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)
    twa.set_twa_window(_twa_window)


@external
def set_distribution_rate(new_profit_max_unlock_time: uint256):
    """
    @notice Admin function to correct the distribution
    rate of the rewards. Making this value lower will reduce
    the time it takes to stream the rewards, making it longer
    will do the opposite. Setting it to 0 will immediately
    distribute all the rewards.
    @dev This function can be used to prevent the rewards
    distribution from being manipulated (i.e. MEV twa
    snapshots to obtain higher APR for the vault).
    """
    access_control._check_role(RATE_MANAGER, msg.sender)

    extcall vault.setProfitMaxUnlockTime(new_profit_max_unlock_time)
    extcall vault.process_report(self)
