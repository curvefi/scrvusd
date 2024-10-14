import boa
from eth_account import Account
import hashlib

rewards_handler_deployer = boa.load_partial("contracts/RewardsHandler.vy")
original_vault_deployer = boa.load_partial("contracts/yearn/VaultV3.vy")
vault_factory_deployer = boa.load_partial("contracts/yearn/VaultFactory.vy")
erc20_deployer = boa.load_partial("tests/mocks/MockERC20.vy")
rewards_handler_deployer = boa.load_partial("contracts/RewardsHandler.vy")


def hash_to_address(input_string: str) -> str:
    # Hash the input string using SHA-256 to create a 32-byte private key
    private_key = hashlib.sha256(input_string.encode("utf-8")).hexdigest()
    # Create an account object from the private key
    account = Account.from_key(private_key)
    # Retrieve the Ethereum address in checksum format
    address = account.address
    return address
