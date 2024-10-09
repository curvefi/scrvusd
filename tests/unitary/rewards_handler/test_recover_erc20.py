import boa
import pytest


@pytest.fixture(scope="module")
def mock_erc20():
    return boa.load("tests/mocks/MockERC20.vy")


@pytest.fixture(scope="module")
def recovery_manager(rewards_handler, curve_dao):
    _recovery_admin = boa.env.generate_address()
    rewards_handler.grantRole(rewards_handler.RECOVERY_MANAGER(), _recovery_admin, sender=curve_dao)
    return _recovery_admin


def test_default_behavior(rewards_handler, mock_erc20, recovery_manager):
    rescue_address = boa.env.generate_address()
    boa.deal(mock_erc20, rewards_handler, 10**18)
    rewards_handler.recover_erc20(mock_erc20, rescue_address, sender=recovery_manager)
    assert mock_erc20.balanceOf(rescue_address) == 10**18
    assert mock_erc20.balanceOf(rewards_handler) == 0


def test_crvusd_not_allowed(rewards_handler, crvusd, recovery_manager):
    with boa.reverts("can't recover crvusd"):
        rewards_handler.recover_erc20(crvusd, boa.env.generate_address(), sender=recovery_manager)


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.recover_erc20(boa.env.generate_address(), boa.env.generate_address())
