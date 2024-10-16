import boa
import pytest

MOCK_CRV_USD_CIRCULATING_SUPPLY = 69_420_000 * 10**18
CURVE_DAO = boa.env.generate_address()


@pytest.fixture()
def yearn_gov():
    return boa.env.generate_address()


@pytest.fixture()
def curve_dao():
    return CURVE_DAO


@pytest.fixture(params=[CURVE_DAO, boa.env.generate_address("rate_manager")])
def rate_manager(request, rewards_handler):
    _rate_manager = request.param
    if _rate_manager != CURVE_DAO:
        rewards_handler.grantRole(rewards_handler.RATE_MANAGER(), _rate_manager, sender=CURVE_DAO)

    return _rate_manager


@pytest.fixture(params=[CURVE_DAO, boa.env.generate_address("lens_manager")])
def lens_manager(request, rewards_handler):
    _lens_manager = request.param
    if _lens_manager != CURVE_DAO:
        rewards_handler.grantRole(rewards_handler.LENS_MANAGER(), _lens_manager, sender=CURVE_DAO)

    return _lens_manager


@pytest.fixture(params=[CURVE_DAO, boa.env.generate_address("recovery_manager")])
def recovery_manager(request, rewards_handler):
    _recovery_manager = request.param
    if _recovery_manager != CURVE_DAO:
        rewards_handler.grantRole(
            rewards_handler.RECOVERY_MANAGER(), _recovery_manager, sender=CURVE_DAO
        )

    return _recovery_manager


@pytest.fixture()
def dev_deployer():
    return boa.env.generate_address()


@pytest.fixture()
def dev_multisig():
    return boa.env.generate_address()


@pytest.fixture()
def security_agent():
    return boa.env.generate_address()


@pytest.fixture()
def vault_init_deposit_cap():
    return 5_000_000 * 10**18


@pytest.fixture()
def deposit_limit_module(dev_deployer, crvusd, vault, vault_init_deposit_cap, dev_multisig):
    contract_deployer = boa.load_partial("contracts/DepositLimitModule.vy")
    with boa.env.prank(dev_deployer):
        contract = contract_deployer(vault, vault_init_deposit_cap, dev_multisig)
    return contract


@pytest.fixture()
def vault_original():
    return boa.load("contracts/yearn/VaultV3.vy")


@pytest.fixture()
def vault_factory(vault_original, yearn_gov):
    return boa.load(
        "contracts/yearn/VaultFactory.vy",
        "mock factory",
        vault_original,
        yearn_gov,
    )


@pytest.fixture()
def crvusd():
    return boa.load("tests/mocks/MockERC20.vy")


@pytest.fixture()
def role_manager():
    return boa.env.generate_address()


@pytest.fixture()
def vault(vault_factory, crvusd, role_manager, dev_deployer):
    vault_deployer = boa.load_partial("contracts/yearn/VaultV3.vy")

    with boa.env.prank(dev_deployer):
        address = vault_factory.deploy_new_vault(
            crvusd, "Savings crvUSD", "scrvUSD", role_manager, 0
        )

    return vault_deployer.at(address)


@pytest.fixture()
def vault_god(vault, role_manager):
    _god = boa.env.generate_address()

    vault.set_role(_god, int("11111111111111", 2), sender=role_manager)

    return _god


@pytest.fixture()
def minimum_weight(request):
    return 1000  # 10%


@pytest.fixture()
def scaling_factor(request):
    return 10000  # 100%


@pytest.fixture()
def mock_controller_factory(mock_controller):
    mock_controller_factory = boa.load("tests/mocks/MockControllerFactory.vy")
    for i in range(4):  # because we use 3rd controller (weth) in contract code
        mock_controller_factory.eval(
            f"self._controllers.append(IController({mock_controller.address}))"
        )
    return mock_controller_factory


@pytest.fixture()
def mock_controller(mock_monetary_policy):
    mock_controller = boa.load("tests/mocks/MockController.vy")
    mock_controller.eval(f"self._monetary_policy={mock_monetary_policy.address}")
    return mock_controller


@pytest.fixture()
def mock_monetary_policy(mock_peg_keeper):
    mock_monetary_policy = boa.load("tests/mocks/MockMonetaryPolicy.vy")
    mock_monetary_policy.eval(f"self.peg_keeper_array[0] = IPegKeeper({mock_peg_keeper.address})")
    return mock_monetary_policy


@pytest.fixture()
def mock_peg_keeper():
    mock_peg_keeper = boa.load("tests/mocks/MockPegKeeper.vy", MOCK_CRV_USD_CIRCULATING_SUPPLY)
    return mock_peg_keeper


@pytest.fixture()
def rewards_handler(
    vault,
    crvusd,
    role_manager,
    minimum_weight,
    scaling_factor,
    stablecoin_lens,
    curve_dao,
    dev_deployer,
):
    rewards_handler_deployer = boa.load_partial("contracts/RewardsHandler.vy")
    with boa.env.prank(dev_deployer):
        rh = rewards_handler_deployer(
            crvusd, vault, stablecoin_lens, minimum_weight, scaling_factor, curve_dao
        )

    vault.set_role(rh, 2**11 | 2**5, sender=role_manager)

    return rh


@pytest.fixture()
def stablecoin_lens(mock_controller_factory):
    return boa.load("contracts/StablecoinLens.vy", mock_controller_factory)
