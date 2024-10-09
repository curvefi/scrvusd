# pragma version ~=0.4

"""
@title Deposit Limit Module for yearn vaults
@notice This contract controls deposits into yearn vault, and additionally manages roles (admin and controller).
@dev Admins can appoint new admins and controllers, while controllers can pause or resume deposits.
"""


################################################################
#                           STORAGE                            #
################################################################

# Two main roles: admin and controller
is_admin: public(HashMap[address, bool])
is_controller: public(HashMap[address, bool])

# Main contract state for deposit control
deposits_paused: public(bool)


################################################################
#                         CONSTRUCTOR                          #
################################################################

@deploy
def __init__():
    """
    @notice Initializes the contract by assigning the deployer as the initial admin and controller.
    """
    self._set_admin(msg.sender, True)
    self._set_controller(msg.sender, True)
    self._set_deposits_paused(False)


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
def _set_controller(_address: address, is_controller: bool):
    """
    @notice Internal function to assign or revoke controller role.
    @param address The address to be granted or revoked controller status.
    @param is_controller Boolean indicating if the address should be a controller.
    """
    self.is_controller[_address] = is_controller


@internal
def _set_deposits_paused(is_paused: bool):
    """
    @notice Internal function to pause or unpause deposits.
    @param is_paused Boolean indicating if deposits should be paused.
    """
    self.deposits_paused = is_paused


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
def set_controller(new_controller: address, is_controller: bool):
    """
    @notice Allows an admin to grant or revoke controller role to another address.
    @param new_controller The address to grant or revoke controller role.
    @param is_controller Boolean indicating if the address should be a controller.
    @dev Only callable by an admin.
    """
    assert self.is_admin[msg.sender], "Caller is not an admin"
    self._set_controller(new_controller, is_controller)


@external
def set_deposits_paused(state: bool):
    """
    @notice Allows a controller to pause or resume deposits.
    @param state Boolean indicating the desired paused state for deposits.
    @dev Only callable by a controller.
    """
    assert self.is_controller[msg.sender], "Caller is not a controller"
    self._set_deposits_paused(state)


################################################################
#                        VIEW FUNCTIONS                        #
################################################################

@view
@external
def available_deposit_limit(receiver: address) -> uint256:
    """
    @notice Checks the available deposit limit for a given receiver.
    @param receiver The address querying deposit limit.
    @return uint256 Returns the maximum deposit limit if deposits are not paused, otherwise returns 0.
    """
    if self.deposits_paused:
        return 0
    else:
        return max_value(uint256)