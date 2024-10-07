// SPDX-License-Identifier: AGPL-3.0
pragma solidity >=0.8.18 ^0.8.0;

import {BaseStrategy} from "./BaseStrategy.sol";

contract DummyStrategy is BaseStrategy {
    constructor(
        address _asset,
        string memory _name
    ) BaseStrategy(_asset, _name) {}


    function _deployFunds(uint256 _amount) internal override {}
    function _freeFunds(uint256 _amount) internal override {}
    function _harvestAndReport() internal override returns (uint256 _totalAssets) {
        _totalAssets = asset.balanceOf(address(this));
    }
}
