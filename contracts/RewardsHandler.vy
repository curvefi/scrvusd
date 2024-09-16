# pragma version ~=0.4

from ethereum.ercs import IERC20
from ethereum.ercs import IERC165

from interfaces import IVault
from interfaces import IStablecoinLens as ILens

from snekmate.auth import access_control

initializes: access_control

import TWAP as twap
initializes: twap
exports: (
    twap.tvl_twap,
    twap.get_snapshot,
    twap.get_n_snapshots,
    twap.get_twap_window
)

RATE_ADMIN: public(constant(bytes32)) = keccak256("RATE_ADMIN")
WEEK: constant(uint256) = 86400 * 7  # 7 days

stablecoin: immutable(address)
vault: immutable(address)
# TODO should this be mutable and have a 22k overhead or immutable for just 0.1k
lens: address

# implements: IERC165


@deploy
def __init__(_stablecoin: address, _vault: address):
    access_control.__init__()
    twap.__init__(WEEK)  # twap_window = 1 week
    stablecoin = _stablecoin
    vault = _vault


@external
def take_snapshot():
    total_supply: uint256 = staticcall ILens(self.lens).circulating_supply()
    supply_in_vault: uint256 = staticcall IERC20(stablecoin).balanceOf(vault)
    supply_ratio: uint256 = supply_in_vault * 10**18 // total_supply
    if twap.last_timestamp + twap.min_snapshot_dt_seconds < block.timestamp:
        twap.last_timestamp = block.timestamp
        twap.store_snapshot(supply_ratio)



def supportsInterface(id: bytes4) -> bool:
    return True


@external
def adjust_twap_frequency(_min_snapshot_dt_seconds: uint256):
    # must be access controlled, otherwise ddos
    access_control._check_role(RATE_ADMIN, msg.sender)
    twap.min_snapshot_dt_seconds = _min_snapshot_dt_seconds


@external
def adjust_twap_window(_twap_window: uint256):
    # must be access controlled, otherwise ddos
    access_control._check_role(RATE_ADMIN, msg.sender)
    twap.twap_window = _twap_window


@external
@view
def weight() -> uint256:
    return twap.compute()


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
