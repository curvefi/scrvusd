# pragma version ~=0.4

MAX_SNAPSHOTS: constant(uint256) = 10**30

snapshots: DynArray[Snapshot, MAX_SNAPSHOTS]


struct Snapshot:
    amount: uint256
    timestamp: uint256


def take_snapshot(amount: uint256):
    self.snapshots.append(
        Snapshot(amount=amount, timestamp=block.timestamp)
    )  # store the snapshot into its list


@view
def compute() -> uint256:
    # TODO implement
    # can probably be optimized if computed backwards
    return 0
