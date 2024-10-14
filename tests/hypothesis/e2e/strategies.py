import boa
from hypothesis.strategies import composite, integers

from tests.hypothesis.utils import (
    original_vault_deployer,
    vault_factory_deployer,
    erc20_deployer,
    rewards_handler_deployer,
    hash_to_address,
)
from boa.test.strategies import strategy as boa_st

original_vault = original_vault_deployer(override_address=hash_to_address("original_vault"))

ZERO = boa.eval("empty(address)")

addresses = boa_st("address").filter(lambda addr: addr != ZERO)

# we don't use the `address` strategy here to
# avoid address collisions that are not realistic
yearn_gov = boa.env.generate_address()
role_manager = boa.env.generate_address()

vault_factory = vault_factory_deployer(
    "mock factory", original_vault, yearn_gov, override_address=hash_to_address("vault_factory")
)

crvusd = erc20_deployer(override_address=hash_to_address("crvusd"))


@composite
def vault(draw):
    _address = vault_factory.deploy_new_vault(crvusd, "Staked crvUSD", "st-crvUSD", role_manager, 0)

    # we just "cast the interface" on the address
    return original_vault_deployer.at(_address)


bps = integers(min_value=1, max_value=10_000)

minimum_weights = bps

scaling_factors = integers()


@composite
def rewards_handler(draw):
    _rewards_handler = rewards_handler_deployer(
        crvusd,
        _vault := draw(vault()),
        draw(minimum_weights),
        draw(scaling_factors),
        draw(addresses),  # TODO mock this
        draw(addresses),
    )

    _vault.set_role(_rewards_handler, 1, sender=role_manager)

    return _rewards_handler


if __name__ == "__main__":
    rewards_handler().example()
