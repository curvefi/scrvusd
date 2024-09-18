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
    # TODO discuss whether to expose this from the interface
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

RATE_ADMIN: public(constant(bytes32)) = keccak256("RATE_ADMIN")
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
):
    lens.__init__(controller_factory)

    # TODO check who has access to what at deployment time
    access_control.__init__()

    twa.__init__(
        WEEK,  # twa_window = 1 week
        1,  #  min_snapshot_dt_seconds = 1 second (if 0, then spam is possible)
    )

    stablecoin = _stablecoin
    vault = _vault


@external
def take_snapshot():
    total_supply: uint256 = lens._circulating_supply()
    supply_in_vault: uint256 = staticcall stablecoin.balanceOf(vault.address)
    supply_ratio: uint256 = supply_in_vault * 10**18 // total_supply
    twa.store_snapshot(supply_ratio)


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
def adjust_twa_frequency(_min_snapshot_dt_seconds: uint256):
    access_control._check_role(RATE_ADMIN, msg.sender)
    twa.adjust_min_snapshot_dt_seconds(_min_snapshot_dt_seconds)


@external
def adjust_twa_window(_twa_window: uint256):
    access_control._check_role(RATE_ADMIN, msg.sender)
    twa.adjust_twa_window(_twa_window)


@external
@view
def weight() -> uint256:
    return min(twa.compute(), self.minimum_weight)


@external
def process_rewards():
    available_balance: uint256 = staticcall stablecoin.balanceOf(self)
    extcall stablecoin.transfer(vault.address, available_balance)
    extcall vault.setProfitMaxUnlockTime(WEEK)
    extcall vault.process_report(vault.address)


@external
def correct_distribution_rate(new_profit_max_unlock_time: uint256):
    access_control._check_role(RATE_ADMIN, msg.sender)
    extcall vault.setProfitMaxUnlockTime(new_profit_max_unlock_time)
    extcall vault.process_report(self)
