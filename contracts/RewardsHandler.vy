# pragma version ~=0.4

from ethereum.ercs import IERC20
from ethereum.ercs import IERC165

from interfaces import IVault
from interfaces import IStablecoinLens as ILens

from snekmate.auth import access_control

initializes: access_control


import TWA as twa
initializes: twa
exports: (
    twa.compute_twa,
    twa.snapshots,
    twa.get_len_snapshots,
    twa.twa_window,
    twa.min_snapshot_dt_seconds,
    twa.last_snapshot_timestamp
)

RATE_ADMIN: public(constant(bytes32)) = keccak256("RATE_ADMIN")
WEEK: constant(uint256) = 86400 * 7  # 7 days

stablecoin: immutable(address)
vault: immutable(address)
# TODO should this be mutable and have a 22k overhead or immutable for just 0.1k
lens: address

# implements: IERC165


@deploy
def __init__(_stablecoin: address, _vault: address, _dao: address):
    twa.__init__(WEEK, 1)  # twa_window = 1 week, min_snapshot_dt_seconds = 1 second (if 0, then spam is possible)

    stablecoin = _stablecoin
    vault = _vault

    access_control.__init__()
    access_control._grant_role(RATE_ADMIN, _dao)
    access_control._revoke_role(empty(bytes32), msg.sender)

@external
def take_snapshot():
    total_supply: uint256 = staticcall ILens(self.lens).circulating_supply()
    supply_in_vault: uint256 = staticcall IERC20(stablecoin).balanceOf(vault)
    supply_ratio: uint256 = supply_in_vault * 10**18 // total_supply
    twa._store_snapshot(supply_ratio)


def supportsInterface(id: bytes4) -> bool:
    return True


@external
def adjust_twa_frequency(_min_snapshot_dt_seconds: uint256):
    access_control._check_role(RATE_ADMIN, msg.sender)
    twa._adjust_min_snapshot_dt_seconds(_min_snapshot_dt_seconds)


@external
def adjust_twa_window(_twa_window: uint256):
    access_control._check_role(RATE_ADMIN, msg.sender)
    twa._adjust_twa_window(_twa_window)


@external
@view
def weight() -> uint256:
    # TODO - should implement lower bound for weight, otherwise will be close to 0 at init TVL
    return twa._compute()


@external
def process_rewards():
    available_balance: uint256 = staticcall IERC20(stablecoin).balanceOf(self)
    extcall IERC20(stablecoin).transfer(vault, available_balance)
    extcall IVault(vault).setProfitMaxUnlockTime(WEEK)
    extcall IVault(vault).process_report(vault)


@external
def correct_distribution_rate(new_profit_max_unlock_time: uint256):
    access_control._check_role(RATE_ADMIN, msg.sender)
    extcall IVault(vault).setProfitMaxUnlockTime(new_profit_max_unlock_time)
    extcall IVault(vault).process_report(self)
