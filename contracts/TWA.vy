# pragma version ~=0.4

"""
@title Time Weighted Average (TWA) Calculator Vyper Module @notice This contract
stores snapshots of a tracked value at specific timestamps and computes the Time
Weighted Average (TWA) over a defined time window.

@dev
- Snapshots Storage: Stores snapshots of a tracked value along with their
  timestamps in a dynamic array, ensuring snapshots are only added if a minimum
  time interval (`min_snapshot_dt_seconds`) has passed since the last snapshot.
- TWA Calculation: Computes the TWA by iterating over the stored snapshots in
  reverse chronological order. It uses the trapezoidal rule to calculate the
  weighted average of the tracked value over the specified time window
  (`twa_window`).
- Functions:
  - `_store_snapshot`: Internal function to store a new snapshot of the tracked
    value if the minimum time interval has passed. !!!Wrapper must be
    implemented in importing contract.
  - `compute_twa`: External view function that calculates and returns the TWA
    based on the stored snapshots.
  - `get_len_snapshots`: External view function that returns the total number of
    snapshots stored.
- Usage: Ideal for tracking metrics like staked supply rates, token prices,
  or any other value that changes over time and requires averaging over a
  period.
"""

MAX_SNAPSHOTS: constant(uint256) = 10**18  # 31.7 billion years if snapshot every second

snapshots: public(DynArray[Snapshot, MAX_SNAPSHOTS])
min_snapshot_dt_seconds: public(uint256)  # Minimum time between snapshots in seconds
twa_window: public(uint256)  # Time window in seconds for TWA calculation
last_snapshot_timestamp: public(uint256)  # Timestamp of the last snapshot (assigned in RewardsHandler)


struct Snapshot:
    tracked_value: uint256  # In 1e18 precision
    timestamp: uint256


@deploy
def __init__(_twa_window: uint256, _min_snapshot_dt_seconds: uint256):
    self.twa_window = _twa_window  # one week (in seconds)
    self.min_snapshot_dt_seconds = _min_snapshot_dt_seconds  # >=1s to prevent spamming


@external
@view
def get_len_snapshots() -> uint256:
    """
    @notice Returns the number of snapshots stored.
    @return Number of snapshots.
    """
    return len(self.snapshots)


@external
@view
def compute_twa() -> uint256:
    """
    @notice External endpoint for _compute() function.
    """
    return self._compute()


@internal
def _store_snapshot(_value: uint256):
    """
    @notice Stores a snapshot of the tracked value.
    @param _value The value to store.
    """
    if self.last_snapshot_timestamp + self.min_snapshot_dt_seconds <= block.timestamp:
        self.last_snapshot_timestamp = block.timestamp
        self.snapshots.append(
            Snapshot(tracked_value=_value, timestamp=block.timestamp)
        )  # store the snapshot into the DynArray


@internal
def _set_twa_window(_new_window: uint256):
    """
    @notice Adjusts the TWA window.
    @param _new_window The new TWA window in seconds.
    @dev Only callable by the importing contract.
    """
    self.twa_window = _new_window


@internal
def _set_snapshot_dt(_new_dt_seconds: uint256):
    """
    @notice Adjusts the minimum snapshot time interval.
    @param _new_dt_seconds The new minimum snapshot time interval in seconds.
    @dev Only callable by the importing contract.
    """
    self.min_snapshot_dt_seconds = _new_dt_seconds


@internal
@view
def _compute() -> uint256:
    """
    @notice Computes the TWA over the specified time window by iterating backwards over the snapshots.
    @return The TWA for tracked value over the self.twa_window (10**18 decimals precision).
    """
    num_snapshots: uint256 = len(self.snapshots)
    if num_snapshots == 0:
        return 0

    time_window_start: uint256 = block.timestamp - self.twa_window

    total_weighted_tracked_value: uint256 = 0
    total_time: uint256 = 0

    # Iterate backwards over all snapshots
    index_array_end: uint256 = num_snapshots - 1
    for i: uint256 in range(0, num_snapshots, bound=MAX_SNAPSHOTS):  # i from 0 to (num_snapshots-1)
        i_backwards: uint256 = index_array_end - i
        current_snapshot: Snapshot = self.snapshots[i_backwards]
        next_snapshot: Snapshot = current_snapshot
        if i != 0:  # If not the first iteration, get the next snapshot
            next_snapshot = self.snapshots[i_backwards + 1]

        interval_start: uint256 = current_snapshot.timestamp
        # Adjust interval start if it is before the time window start
        if interval_start < time_window_start:
            interval_start = time_window_start

        interval_end: uint256 = 0
        if i == 0:  # First iteration - we are on the last snapshot (i_backwards = num_snapshots - 1)
            # For the last snapshot, interval end is block.timestamp
            interval_end = block.timestamp
        else:
            # For other snapshots, interval end is the timestamp of the next snapshot
            interval_end = next_snapshot.timestamp

        if interval_end <= time_window_start:
            break

        time_delta: uint256 = interval_end - interval_start

        # Interpolation using the trapezoidal rule
        averaged_tracked_value: uint256 = (current_snapshot.tracked_value + next_snapshot.tracked_value) // 2

        # Accumulate weighted rate and time
        total_weighted_tracked_value += averaged_tracked_value * time_delta
        total_time += time_delta

    assert total_time > 0, "Zero total time!"
    twa: uint256 = total_weighted_tracked_value // total_time

    return twa
