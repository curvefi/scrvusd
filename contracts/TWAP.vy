# pragma version ~=0.4

MAX_SNAPSHOTS: constant(uint256) = 10**18  # 31.7 billion years if snapshot every second

snapshots: DynArray[Snapshot, MAX_SNAPSHOTS]
min_snapshot_dt_seconds: uint256  # Minimum time between snapshots in seconds
twap_window: uint256  # Time window in seconds for TWAP calculation
last_timestamp: uint256  # Timestamp of the last snapshot (assigned in RewardsHandler)


struct Snapshot:
    staked_supply_rate: uint256  # In 1e18 precision
    timestamp: uint256


@deploy
def __init__(_twap_window: uint256):
    self.twap_window = _twap_window  # one week (in seconds)


@external
@view
def get_snapshot(_index: uint256) -> Snapshot:
    return self.snapshots[_index]


@external
@view
def get_n_snapshots() -> uint256:
    return len(self.snapshots)


@external
@view
def get_twap_window() -> uint256:
    return self.twap_window


@external
@view
def tvl_twap() -> uint256:
    return self.compute()


@internal
def store_snapshot(staked_supply_rate: uint256):
    """
    @notice Stores a snapshot of the staked supply rate into storage DynArray
    @param staked_supply_rate The staked supply rate to store
    """
    self.snapshots.append(
        Snapshot(staked_supply_rate=staked_supply_rate, timestamp=block.timestamp)
    )  # store the snapshot into the list


@view
def compute() -> uint256:
    """
    @notice Computes the TWAP over the specified time window by iterating backwards over the snapshots.
    @return The TWAP staked supply rate over the self.twap_window (10**18 decimals precision).
    """
    num_snapshots: uint256 = len(self.snapshots)
    if num_snapshots == 0:
        return 0

    current_time: uint256 = block.timestamp
    time_window_start: uint256 = current_time - self.twap_window

    total_weighted_staked_supply_rate: uint256 = 0
    total_time: uint256 = 0

    # Iterate backwards over all snapshots
    for i: uint256 in range(0, num_snapshots, bound=MAX_SNAPSHOTS):  # i from 0 to num_snapshots - 1
        i_backwards: uint256 = num_snapshots - 1 - i
        current_snapshot: Snapshot = self.snapshots[i_backwards]
        next_snapshot: Snapshot = current_snapshot
        if i != 0:  # If not the first iteration, get the next snapshot
            next_snapshot = self.snapshots[i_backwards + 1]


        # Figure out snapshot interval wrt current time (Now) and time_window_start
        # Time Axis (Increasing to the Right) --->
        # |---------|---------|---------|---------|------------------------|---------|---------|
        # t0        t1   time_window_start        interval_start           interval_end       Now
        interval_start: uint256 = current_snapshot.timestamp
        # Adjust interval start if it is before the time window start
        if interval_start < time_window_start:
            interval_start = time_window_start

        interval_end: uint256 = 0
        if i == 0:  # First iteration - we are on the last snapshot (i_backwards = num_snapshots - 1)
            # For the last snapshot, interval end is current_time
            interval_end = current_time
        else:
            # For other snapshots, interval end is the timestamp of the next snapshot
            interval_end = next_snapshot.timestamp

        if interval_end <= time_window_start:
            break

        # Time inteval length
        time_delta: uint256 = interval_end - interval_start

        # Interpolation using the trapezoidal rule
        average_staked_supply_rate: uint256 = (
            current_snapshot.staked_supply_rate + next_snapshot.staked_supply_rate
        ) // 2

        # Accumulate weighted rate and time
        total_weighted_staked_supply_rate += average_staked_supply_rate * time_delta
        total_time += time_delta

    assert total_time > 0, "No snapshots taken!"
    twap: uint256 = total_weighted_staked_supply_rate // total_time

    return twap
