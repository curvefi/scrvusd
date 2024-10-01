import pytest
from hypothesis import Phase, Verbosity, settings

settings.register_profile("debug", settings(verbosity=Verbosity.verbose, phases=list(Phase)[:4]))
settings.load_profile("debug")

TWA_PARALLEL_INSTANCES = 10


@pytest.fixture()
def twa_testcase_instance(request):
    """Fixture to return a fresh instance of the twa state machine."""
    from tests.hypothesis.twa.test_twa import TWAStateful

    return TWAStateful.TestCase()


def pytest_generate_tests(metafunc):
    """Generate multiple instances of the state machine test."""
    if "twa_testcase_instance" in metafunc.fixturenames:
        metafunc.parametrize("twa_testcase_instance", range(TWA_PARALLEL_INSTANCES), indirect=True)
