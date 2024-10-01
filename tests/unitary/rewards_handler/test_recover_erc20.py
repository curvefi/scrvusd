import boa
import pytest


@pytest.fixture(scope="module")
def mock_erc20():
    return boa.load("tests/mocks/MockERC20.vy")


def test_default_behavior(rewards_handler, mock_erc20, curve_dao):
    rescue_address = boa.env.generate_address()
    boa.deal(mock_erc20, rewards_handler, 10**18)
    rewards_handler.recover_erc20(mock_erc20, rescue_address, sender=curve_dao)
    assert mock_erc20.balanceOf(rescue_address) == 10**18
    assert mock_erc20.balanceOf(rewards_handler) == 0


def test_crvusd_not_allowed(rewards_handler, crvusd, curve_dao):
    with boa.reverts("can't recover crvusd"):
        rewards_handler.recover_erc20(crvusd, boa.env.generate_address(), sender=curve_dao)


def test_role_access(rewards_handler):
    with boa.reverts("access_control: account is missing role"):
        rewards_handler.recover_erc20(boa.env.generate_address(), boa.env.generate_address())