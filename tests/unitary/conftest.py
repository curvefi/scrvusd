import boa
import boa_solidity  # noqa: F401
import pytest

MOCK_CRV_USD_CIRCULATING_SUPPLY = 69_420_000 * 10**18


@pytest.fixture(scope="module")
def yearn_gov():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def curve_dao():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def dev_address():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def vault_original():
    return boa.load("contracts/yearn/Vault.vy")


@pytest.fixture(scope="module")
def vault_factory(vault_original, yearn_gov):
    return boa.load(
        "contracts/yearn/VaultFactory.vy",
        "mock factory",
        vault_original,
        yearn_gov,
    )


@pytest.fixture(scope="module")
def crvusd():
    return boa.load("tests/mocks/MockERC20.vy")


@pytest.fixture(scope="module")
def role_manager():
    return boa.env.generate_address()


@pytest.fixture(scope="module")
def vault(vault_factory, crvusd, role_manager, accrual_strategy, dev_address):
    vault_deployer = boa.load_partial("contracts/yearn/Vault.vy")

    address = vault_factory.deploy_new_vault(
        crvusd, "Staked crvUSD", "st-crvUSD", role_manager, 86_400 * 7
    )

    vault = vault_deployer.at(address)

    # creata a local god to avoid recursive dependencies in fixtures
    _god = boa.env.generate_address()

    vault.set_role(_god, int("11111111111111", 2), sender=role_manager)

    vault.add_strategy(accrual_strategy, sender=_god)  # TODO figure out queue
    boa.deal(crvusd, dev_address, 1 * 10**18)
    with boa.env.prank(dev_address):
        crvusd.approve(vault, 1 * 10**18)
        vault.set_deposit_limit(10_000_000 * 10**18, sender=_god)
        vault.deposit(1 * 10**18, dev_address)

    vault.update_max_debt_for_strategy(accrual_strategy, 1 * 10**18, sender=_god)
    vault.update_debt(accrual_strategy, 1 * 10**18, sender=_god)
    return vault


@pytest.fixture(scope="module")
def vault_god(vault, role_manager):
    _god = boa.env.generate_address()

    vault.set_role(_god, int("11111111111111", 2), sender=role_manager)

    return _god


@pytest.fixture(scope="module")
def minimum_weight(request):
    return 1000  # 10%


@pytest.fixture(scope="module")
def scaling_factor(request):
    return 10000  # 100%


@pytest.fixture(scope="module")
def mock_controller_factory(mock_controller):
    mock_controller_factory = boa.load("tests/mocks/MockControllerFactory.vy")
    for i in range(4):  # because we use 3rd controller (weth) in contract code
        mock_controller_factory.eval(
            f"self._controllers.append(IController({mock_controller.address}))"
        )
    return mock_controller_factory


@pytest.fixture(scope="module")
def mock_controller(mock_monetary_policy):
    mock_controller = boa.load("tests/mocks/MockController.vy")
    mock_controller.eval(f"self._monetary_policy={mock_monetary_policy.address}")
    return mock_controller


@pytest.fixture(scope="module")
def mock_monetary_policy(mock_peg_keeper):
    mock_monetary_policy = boa.load("tests/mocks/MockMonetaryPolicy.vy")
    mock_monetary_policy.eval(f"self.peg_keeper_array[0] = IPegKeeper({mock_peg_keeper.address})")
    return mock_monetary_policy


@pytest.fixture(scope="module")
def mock_peg_keeper():
    mock_peg_keeper = boa.load("tests/mocks/MockPegKeeper.vy", MOCK_CRV_USD_CIRCULATING_SUPPLY)
    return mock_peg_keeper


@pytest.fixture(scope="module")
def rewards_handler(
    vault,
    crvusd,
    role_manager,
    minimum_weight,
    scaling_factor,
    mock_controller_factory,
    curve_dao,
    dev_address,
):
    print(crvusd, vault, minimum_weight, scaling_factor, mock_controller_factory, curve_dao)
    rewards_handler_deployer = boa.load_partial("contracts/RewardsHandler.vy")

    with boa.env.prank(dev_address):
        rh = rewards_handler_deployer(
            crvusd, vault, minimum_weight, scaling_factor, mock_controller_factory, curve_dao
        )

    vault.set_role(rh, 2**11 | 2**6 | 2**5 | 2**0, sender=role_manager)

    return rh


@pytest.fixture(scope="module")
def solc_args():
    return {
        "optimize": True,
        "optimize_runs": 200,
    }


@pytest.fixture(scope="module")
def tokenized_strategy(solc_args, vault_factory, dev_address):
    deployer = boa.load_partial_solc(
        "contracts/yearn/TokenizedStrategy.sol", compiler_args=solc_args
    )
    with boa.env.prank(dev_address):
        tokenized_strategy = deployer.deploy(
            vault_factory.address, override_address="0x2e234DAe75C793f67A35089C9d99245E1C58470b"
        )
    return tokenized_strategy


@pytest.fixture(scope="module")
def accrual_strategy(solc_args, crvusd, tokenized_strategy, dev_address):
    deployer = boa.load_partial_solc("contracts/yearn/AccrualStrategy.sol", compiler_args=solc_args)
    with boa.env.prank(dev_address):
        strategy = deployer.deploy(crvusd.address, "AccrualStrategy")
    return strategy


@pytest.fixture(scope="module")
def accrual_strategy_ext(accrual_strategy, dev_address):
    accrual_strategy_extended_abi = boa.load_vyi("contracts/interfaces/IStrategy.vyi").at(
        accrual_strategy.address
    )
    with boa.env.prank(dev_address):
        accrual_strategy_extended_abi.setProfitMaxUnlockTime(0)
        accrual_strategy_extended_abi.setPerformanceFee(0)
    return accrual_strategy_extended_abi
