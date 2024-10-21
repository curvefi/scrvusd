import boa
import pytest


@pytest.fixture()
def rewards_handler_deployer():
    return boa.load_partial("contracts/RewardsHandler.vy")


def test_default_behavior(
    rewards_handler_deployer,
    crvusd,
    vault,
    minimum_weight,
    scaling_factor,
    stablecoin_lens,
    curve_dao,
):
    rewards_handler = rewards_handler_deployer(
        crvusd, vault, stablecoin_lens, minimum_weight, scaling_factor, curve_dao
    )

    assert rewards_handler._immutables.stablecoin == crvusd.address
    assert rewards_handler._immutables.vault == vault.address
    assert rewards_handler.vault() == vault.address
    assert rewards_handler.minimum_weight() == minimum_weight
    assert rewards_handler._storage.minimum_weight.get() == minimum_weight
    assert rewards_handler.scaling_factor() == scaling_factor
    assert rewards_handler._storage.scaling_factor.get() == scaling_factor
    assert rewards_handler.stablecoin_lens() == stablecoin_lens.address
    assert rewards_handler.hasRole(rewards_handler.DEFAULT_ADMIN_ROLE(), curve_dao)
    assert rewards_handler.hasRole(rewards_handler.RATE_MANAGER(), curve_dao)
    # eoa would be the deployer from which we revoke the role
    assert not rewards_handler.hasRole(rewards_handler.DEFAULT_ADMIN_ROLE(), boa.env.eoa)
    assert rewards_handler.eval("twa.twa_window") == 86_400 * 7
    assert rewards_handler.eval("twa.min_snapshot_dt_seconds") == 3600  # 1 hr
