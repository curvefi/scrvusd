# pragma version ~=0.4

from ethereum.ercs import IERC20
from ethereum.ercs import IERC165
from interfaces import IVault

from snekmate.auth import access_control

initializes: access_control

from interfaces import IStablecoinLens as ILens

import TWAP as twap

RATE_ADMIN: public(constant(bytes32)) = keccak256("RATE_ADMIN")

stablecoin: immutable(address)
vault: immutable(address)
# TODO should this be mutable and have a 22k overhead or immutable for just 0.1k
lens: address
WEEK: constant(uint256) = 86400 * 7  # 7 days

# implements: IERC165
initializes: twap


@deploy
def __init__(_stablecoin: address, _vault: address):
    access_control.__init__()
    stablecoin = _stablecoin
    vault = _vault


@external
def take_snapshot():
    total_supply: uint256 = staticcall ILens(self.lens).circulating_supply()
    supply_in_vault: uint256 = staticcall IERC20(stablecoin).balanceOf(vault)
    supply_ratio: uint256 = supply_in_vault * 10**18 // total_supply

    twap.take_snapshot(supply_ratio)


@external
@view
def tvl_twap() -> uint256:
    return twap.compute()


def supportsInterface(id: bytes4) -> bool:
    return True


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

    extcall IVault(vault).setProfitMaxUnlockTime(WEEK)
    extcall IVault(vault).process_report(self)
