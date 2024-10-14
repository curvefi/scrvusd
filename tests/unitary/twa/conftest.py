import boa
import pytest

# Constants
INITIAL_BALANCE = 100_000_000 * 10**18
AMT_DEPOSIT = 10 * 10**18
SNAPSHOT_AMOUNT = 100 * 10**18
MIN_SNAPSHOT_DT = 60
TWA_WINDOW = 1000


@pytest.fixture()
def alice(crvusd):
    alice = boa.env.generate_address()
    boa.deal(crvusd, alice, INITIAL_BALANCE)
    return alice


@pytest.fixture()
def setup_vault(vault, crvusd, vault_god, alice):
    crvusd.approve(vault.address, 2**256 - 1, sender=alice)
    vault.set_deposit_limit(crvusd.balanceOf(alice), sender=vault_god)
    return vault


@pytest.fixture()
def setup_rewards_handler(rewards_handler, rate_manager, twa_window, snapshot_interval):
    with boa.env.prank(rate_manager):
        rewards_handler.set_twa_window(twa_window)
        rewards_handler.set_twa_snapshot_dt(snapshot_interval)
    return rewards_handler


@pytest.fixture()
def amt_deposit():
    return AMT_DEPOSIT


@pytest.fixture()
def snapshot_amount():
    return SNAPSHOT_AMOUNT


@pytest.fixture()
def snapshot_interval():
    return MIN_SNAPSHOT_DT


@pytest.fixture()
def twa_window():
    return TWA_WINDOW
