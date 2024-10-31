# yearn vaults 3.0.3 factory
yearn_vault_factory = "0x770D0d1Fb036483Ed4AbB6d53c1C88fb277D812F"
vault_original = "0xd8063123BBA3B480569244AE66BFE72B6c84b00d"

crvusd = "0xf939E0A03FB07F59A73314E73794Be0E57ac1b4E"
crvusd_controller_factory = "0xC9332fdCB1C491Dcc683bAe86Fe3cb70360738BC"
crvusd_fee_collector = "0xa2Bcd1a4Efbd04B63cd03f5aFf2561106ebCCE00"
fee_splitter = "0x2dFd89449faff8a532790667baB21cF733C064f2"
dao_agent = "0x40907540d8a6C65c637785e8f8B742ae6b0b9968"

dev_multisig = "0xe286b81d16FC7e87eD9dc2a80dd93b1816F4Dcf2"
fuzzland_address = "0xaE4A2FFeeD8eEDA4698bBf4A36F01d1f86602973"

# curve factories
factory_stableswap_ng = "0x6A8cbed756804B16E05E741eDaBd5cB544AE21bf"
factory_twocrypto_ng = "0x98EE851a00abeE0d95D08cF4CA2BdCE32aeaAF7F"
factory_tricrypto_ng = "0x0c0e5f2fF0ff18a3be9b835635039256dC4B4963"

stables = [
    {"name": "dai", "address": "0x6b175474e89094c44da98b954eedeac495271d0f", "asset_type": 0},
    {"name": "usdt", "address": "0xdac17f958d2ee523a2206206994597c13d831ec7", "asset_type": 0},
    {"name": "usdc", "address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "asset_type": 0},
    {"name": "usde", "address": "0x4c9edd5852cd905f086c759e8383e09bff1e68b3", "asset_type": 0},
    {"name": "frax", "address": "0x853d955acef822db058eb8505911ed77f175b99e", "asset_type": 0},
]

yield_stables = [
    {"name": "sdai", "address": "0x83f20f44975d03b1b09e64809b757c47f942beea", "asset_type": 3},
    {"name": "sfrax", "address": "0xa663b02cf0a4b149d2ad41910cb81e23e1c41c32", "asset_type": 3},
    {"name": "susde", "address": "0x9d39a5de30e57443bff2a8307a4256c8797a3497", "asset_type": 3},
]
all_stables = [*stables, *yield_stables]

cryptos = {
    "weth": {"address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"},
    "steth": {"address": "0xae7ab96520de3a18e5e111b5eaab095312d7fe84"},
    "wbtc": {"address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"},
    "tbtc": {"address": "0x18084fba666a33d37592fa2633fd49a74dd93a88"},
}
