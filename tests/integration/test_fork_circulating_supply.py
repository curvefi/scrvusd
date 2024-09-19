def test_fork_circulating_supply(lens):
    # TODO mint more crvusd and make sure this increases accordingly
    # TODO increase flashloan debt ceiling and make
    #  sure supply doesn't increase
    print("{:2e}".format(lens.internal._circulating_supply()))
