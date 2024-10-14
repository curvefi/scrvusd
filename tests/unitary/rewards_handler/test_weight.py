import boa
import pytest

# TODO do fuzzing here
possible_min_weight = [i * 2000 for i in range(0, 5)]

possible_scaling_factor = [i * 4000 for i in range(0, 5)]

# requested weight can potentially be any number (capped anyway by fee splitter)
possible_req_weight = [i * 4000 for i in range(0, 3)]


@pytest.fixture(params=possible_min_weight)
def minimum_weight(request):
    return request.param


@pytest.fixture(params=possible_scaling_factor)
def scaling_factor(request):
    return request.param


@pytest.fixture(params=possible_req_weight)
def requested_weight(request):
    return request.param


def test_default_behavior(
    rewards_handler, minimum_weight, scaling_factor, requested_weight, rate_manager
):
    rewards_handler.eval(f"twa._take_snapshot({requested_weight})")
    boa.env.time_travel(blocks=100)
    assert rewards_handler.compute_twa() == requested_weight
    rewards_handler.set_minimum_weight(minimum_weight, sender=rate_manager)
    assert rewards_handler.weight() == max(
        minimum_weight, requested_weight * scaling_factor // 10_000
    )
