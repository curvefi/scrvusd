# pragma version ~=0.4

"""
@title Temporary Deposit Limit Module for yearn vaults
@notice This contract temporarily controls deposits into a yearn vault and manages roles (admin and security_agent).
@dev Admins can appoint new admins and security_agents, while security_agents can pause or resume deposits.
This module will be removed once the vault is battle-tested and proven stable.
"""


################################################################
#                           INTERFACES                         #
################################################################

from interfaces import IVault

################################################################
#                           STORAGE                            #
################################################################

# Two main roles: admin and security_agent
is_admin: public(HashMap[address, bool])
is_security_agent: public(HashMap[address, bool])

# Main contract state for deposit control
deposits_paused: public(bool)

# Max deposit limit
max_deposit_limit: public(uint256)

# Stablecoin/Vault addresses
vault: public(immutable(IVault))

################################################################
#                         CONSTRUCTOR                          #
################################################################

@deploy
def __init__(
    _vault: IVault,
    max_deposit_limit: uint256,
):
    """
    @notice Initializes the contract by assigning the deployer as the initial admin and security_agent.
    """
    self._set_admin(msg.sender, True)
    self._set_security_agent(msg.sender, True)
    self._set_deposits_paused(False)  # explicit non-paused at init
    self._set_deposit_limit(max_deposit_limit)

    vault = _vault


################################################################
#                      INTERNAL FUNCTIONS                      #
################################################################

@internal
def _set_admin(_address: address, is_admin: bool):
    """
    @notice Internal function to assign or revoke admin role.
    @param address The address to be granted or revoked admin status.
    @param is_admin Boolean indicating if the address should be an admin.
    """
    self.is_admin[_address] = is_admin


@internal
def _set_security_agent(_address: address, is_security_agent: bool):
    """
    @notice Internal function to assign or revoke security_agent role.
    @param address The address to be granted or revoked security_agent status.
    @param is_security_agent Boolean indicating if the address should be a security_agent.
    """
    self.is_security_agent[_address] = is_security_agent


@internal
def _set_deposits_paused(is_paused: bool):
    """
    @notice Internal function to pause or unpause deposits.
    @param is_paused Boolean indicating if deposits should be paused.
    """
    self.deposits_paused = is_paused


@internal
def _set_deposit_limit(new_limit: uint256):
    """
    @notice Internal function to set the maximum deposit limit.
    @param new_limit The new maximum deposit limit.
    """
    self.max_deposit_limit = new_limit


################################################################
#                        EXTERNAL FUNCTIONS                    #
################################################################

@external
def set_admin(new_admin: address, is_admin: bool):
    """
    @notice Allows an admin to grant or revoke admin role to another address.
    @param new_admin The address to grant or revoke admin role.
    @param is_admin Boolean indicating if the address should be an admin.
    @dev Only callable by an admin.
    """
    assert self.is_admin[msg.sender], "Caller is not an admin"
    self._set_admin(new_admin, is_admin)


@external
def set_security_agent(new_security_agent: address, is_security_agent: bool):
    """
    @notice Allows an admin to grant or revoke security_agent role to another address.
    @param new_security_agent The address to grant or revoke security_agent role.
    @param is_security_agent Boolean indicating if the address should be a security_agent.
    @dev Only callable by an admin.
    """
    assert self.is_admin[msg.sender], "Caller is not an admin"
    self._set_security_agent(new_security_agent, is_security_agent)


@external
def set_deposits_paused(state: bool):
    """
    @notice Allows a security_agent to pause or resume deposits.
    @param state Boolean indicating the desired paused state for deposits.
    @dev Only callable by a security_agent.
    """
    assert self.is_security_agent[msg.sender], "Caller is not a security_agent"
    self._set_deposits_paused(state)


@external
def set_deposit_limit(new_limit: uint256):
    """
    @notice Allows an admin to update the maximum deposit limit.
    @param new_limit The new maximum deposit limit.
    @dev Only callable by an admin.
    """
    assert self.is_admin[msg.sender], "Caller is not an admin"
    self._set_deposit_limit(new_limit)


################################################################
#                        VIEW FUNCTIONS                        #
################################################################

@view
@external
def available_deposit_limit(receiver: address) -> uint256:
    """
    @notice Checks the available deposit limit for a given receiver.
    @param receiver The address querying deposit limit.
    @return uint256 Returns the maximum deposit limit if deposits are not paused,
    otherwise returns (self.max_deposit_limit - vault_balance).
    """
    if self.deposits_paused:
        return 0
    if self.max_deposit_limit == max_value(uint256):
        return max_value(uint256)
    else:
        vault_balance: uint256 = staticcall vault.totalAssets()
        if vault_balance >= self.max_deposit_limit:
            return 0
        else:
            return self.max_deposit_limit - vault_balance
