# pragma version ~=0.4

"""
@title Rewards Handler

@notice A contract that helps distributing rewards for scrvUSD, an ERC4626 vault
for crvUSD (yearn's vault v3 multi-vault implementaiton is used). Any crvUSD
token sent to this contract is considered donated as rewards for depositors and
will not be recoverable. This contract can receive funds to be distributed from
the FeeSplitter (crvUSD borrow rates revenues) and potentially other sources as
well. The amount of funds that this contract should receive from the fee
splitter is determined by computing the time-weighted average of the vault
balance over crvUSD circulating supply ratio. The contract handles the rewards
in a permissionless manner, anyone can take snapshots of the TVL and distribute
rewards. In case of manipulation of the time-weighted average, the contract
allows trusted contracts given the role of `RATE_MANGER` to correct the
distribution rate of the rewards.

@license Copyright (c) Curve.Fi, 2020-2024 - all rights reserved

@author curve.fi

@custom:security security@curve.fi
"""


################################################################
#                           INTERFACES                         #
################################################################


from ethereum.ercs import IERC20
from ethereum.ercs import IERC165

implements: IERC165

from contracts.interfaces import IDynamicWeight

implements: IDynamicWeight

# yearn vault's interface
from interfaces import IVault


################################################################
#                            MODULES                           #
################################################################


# we use access control because we want to have multiple addresses being able
# to adjust the rate while only the dao (which has the `DEFAULT_ADMIN_ROLE`)
# can appoint `RATE_MANAGER`s
from snekmate.auth import access_control
initializes: access_control
exports: (
    # we don't expose `supportsInterface` from access control
    access_control.grantRole,
    access_control.revokeRole,
    access_control.renounceRole,
    access_control.set_role_admin,
    access_control.DEFAULT_ADMIN_ROLE,
    access_control.hasRole,
    access_control.getRoleAdmin,
)

# import custom modules that contain helper functions.
import StablecoinLens as lens
initializes: lens

import TWA as twa
initializes: twa
exports: (
    twa.compute_twa,
    twa.snapshots,
    twa.get_len_snapshots,
    twa.twa_window,
    twa.min_snapshot_dt_seconds,
    twa.last_snapshot_timestamp,
)


################################################################
#                            EVENTS                            #
################################################################


event MinimumWeightUpdated:
    new_minimum_weight: uint256


event ScalingFactorUpdated:
    new_scaling_factor: uint256


################################################################
#                           CONSTANTS                          #
################################################################


RATE_MANAGER: public(constant(bytes32)) = keccak256("RATE_MANAGER")
RECOVERY_MANAGER: public(constant(bytes32)) = keccak256("RECOVERY_MANAGER")
WEEK: constant(uint256) = 86_400 * 7  # 7 days
MAX_BPS: constant(uint256) = 10**4  # 100%

_SUPPORTED_INTERFACES: constant(bytes4[3]) = [
    0x01FFC9A7,  # The ERC-165 identifier for ERC-165.
    0x7965DB0B,  # The ERC-165 identifier for `IAccessControl`.
    0xA1AAB33F,  # The ERC-165 identifier for the dynamic weight interface.
]


################################################################
#                            STORAGE                           #
################################################################


stablecoin: immutable(IERC20)
vault: public(immutable(IVault))

# scaling factor for the deposited token / circulating supply ratio.
scaling_factor: public(uint256)

# the minimum amount of rewards requested to the FeeSplitter.
minimum_weight: public(uint256)

# the time over which rewards will be distributed mirror of the private
# `profit_max_unlock_time` variable from yearn vaults.
distribution_time: public(uint256)


################################################################
#                          CONSTRUCTOR                         #
################################################################


@deploy
def __init__(
    _stablecoin: IERC20,
    _vault: IVault,
    minimum_weight: uint256,
    scaling_factor: uint256,
    controller_factory: lens.IControllerFactory,
    admin: address,
):
    lens.__init__(controller_factory)

    # initialize access control
    access_control.__init__()
    # admin (most likely the dao) controls who can be a rate manager
    access_control._grant_role(access_control.DEFAULT_ADMIN_ROLE, admin)
    # admin itself is a RATE_MANAGER and RECOVERY_MANAGER
    access_control._grant_role(RATE_MANAGER, admin)
    access_control._grant_role(RECOVERY_MANAGER, admin)
    # deployer does not control this contract
    access_control._revoke_role(access_control.DEFAULT_ADMIN_ROLE, msg.sender)

    twa.__init__(
        WEEK,  # twa_window = 1 week
        1,  #  min_snapshot_dt_seconds = 1 second
    )

    self._set_minimum_weight(minimum_weight)
    self._set_scaling_factor(scaling_factor)

    stablecoin = _stablecoin
    vault = _vault


################################################################
#                   PERMISSIONLESS FUNCTIONS                   #
################################################################


@external
def take_snapshot():
    """
    @notice Function that anyone can call to take a snapshot of the current
    deposited supply ratio in the vault. This is used to compute the time-weighted
    average of the TVL to decide on the amount of rewards to ask for (weight).

    @dev There's no point in MEVing this snapshot as the rewards distribution rate
    can always be reduced (if a malicious actor inflates the value of the snapshot)
    or the minimum amount of rewards can always be increased (if a malicious actor
    deflates the value of the snapshot).
    """

    # get the circulating supply from a helper function.
    # supply in circulation = controllers' debt + peg keppers' debt
    circulating_supply: uint256 = lens._circulating_supply()

    # obtain the supply of crvUSD contained in the vault by simply checking its
    # balance since it's an ERC4626 vault. This will also take into account
    # rewards that are not yet distributed.
    supply_in_vault: uint256 = staticcall stablecoin.balanceOf(vault.address)

    # here we intentionally reduce the precision of the ratio because the
    # dynamic weight interface expects a percentage in BPS.
    supply_ratio: uint256 = supply_in_vault * MAX_BPS // circulating_supply

    twa._take_snapshot(supply_ratio)


@external
def process_rewards():
    """
    @notice Permissionless function that let anyone distribute rewards (if any) to
    the crvUSD vault.
    """

    # prevent the rewards from being distributed untill the distribution rate
    # has been set
    assert (
        self.distribution_time != 0
    ), "rewards should be distributed over time"

    # any crvUSD sent to this contract (usually through the fee splitter, but
    # could also come from other sources) will be used as a reward for scrvUSD
    # vault depositors.
    available_balance: uint256 = staticcall stablecoin.balanceOf(self)

    assert available_balance > 0, "no rewards to distribute"

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
    @dev Returns `True` if this contract implements the interface defined by
    `interface_id`.
    @param interface_id The 4-byte interface identifier.
    @return bool The verification whether the contract implements the interface or
    not.
    """
    return interface_id in _SUPPORTED_INTERFACES


@external
@view
def weight() -> uint256:
    """
    @notice this function is part of the dynamic weight interface expected by the
    FeeSplitter to know what percentage of funds should be sent for rewards
    distribution to scrvUSD vault depositors.
    @dev `minimum_weight` acts as a lower bound for the percentage of rewards that
    should be distributed to depositors. This is useful to bootstrapping TVL by asking
    for more at the beginning and can also be increased in the future if someone
    tries to manipulate the time-weighted average of the tvl ratio.
    """
    raw_weight: uint256 = twa._compute() * self.scaling_factor // MAX_BPS
    return max(raw_weight, self.minimum_weight)


################################################################
#                         ADMIN FUNCTIONS                      #
################################################################


@external
def set_twa_snapshot_dt(_min_snapshot_dt_seconds: uint256):
    """
    @notice Setter for the time-weighted average minimal frequency.
    @param _min_snapshot_dt_seconds The minimum amount of time that should pass
    between two snapshots.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)
    twa._set_snapshot_dt(_min_snapshot_dt_seconds)


@external
def set_twa_window(_twa_window: uint256):
    """
    @notice Setter for the time-weighted average window
    @param _twa_window The time window used to compute the TWA value of the
    balance/supply ratio.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)
    twa._set_twa_window(_twa_window)


@external
def set_distribution_time(new_distribution_time: uint256):
    """
    @notice Admin function to correct the distribution rate of the rewards. Making
    this value lower will reduce the time it takes to stream the rewards, making it
    longer will do the opposite. Setting it to 0 will immediately distribute all the
    rewards.

    @dev This function can be used to prevent the rewards distribution from being
    manipulated (i.e. MEV twa snapshots to obtain higher APR for the vault). Setting
    this value to zero can be used to pause `process_rewards`.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)

    # we mirror the value of new_profit_max_unlock_time from the yearn vault
    # since it's not exposed publicly.
    self.distribution_time = new_distribution_time

    # change the distribution time of the rewards in the vault
    extcall vault.setProfitMaxUnlockTime(new_distribution_time)

    # enact the changes
    extcall vault.process_report(vault.address)


@external
def set_minimum_weight(new_minimum_weight: uint256):
    """
    @notice Update the minimum weight that the the vault will ask for.

    @dev This function can be used to prevent the rewards requested from being
    manipulated (i.e. MEV twa snapshots to obtain lower APR for the vault). Setting
    this value to zero makes the amount of rewards requested fully determined by the
    twa of the deposited supply ratio.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)
    self._set_minimum_weight(new_minimum_weight)


@internal
def _set_minimum_weight(new_minimum_weight: uint256):
    assert new_minimum_weight <= MAX_BPS, "minimum weight should be <= 100%"
    self.minimum_weight = new_minimum_weight

    log MinimumWeightUpdated(new_minimum_weight)


@external
def set_scaling_factor(new_scaling_factor: uint256):
    """
    @notice Update the scaling factor that is used in the weight calculation.
    This factor can be used to adjust the rewards distribution rate.
    """
    access_control._check_role(RATE_MANAGER, msg.sender)
    self._set_scaling_factor(new_scaling_factor)


@internal
def _set_scaling_factor(new_scaling_factor: uint256):
    self.scaling_factor = new_scaling_factor

    log ScalingFactorUpdated(new_scaling_factor)


@external
def recover_erc20(token: IERC20, receiver: address):
    """
    @notice This is a helper function to let an admin rescue funds sent by mistake
    to this contract. crvUSD cannot be recovered as it's part of the core logic of
    this contract.
    """
    access_control._check_role(RECOVERY_MANAGER, msg.sender)

    # if crvUSD was sent by accident to the contract the funds are lost and will
    # be distributed as rewards on the next `process_rewards` call.
    assert token != stablecoin, "can't recover crvusd"

    # when funds are recovered the whole balanced is sent to a trusted address.
    balance_to_recover: uint256 = staticcall token.balanceOf(self)

    assert extcall token.transfer(
        receiver, balance_to_recover, default_return_value=True
    )
