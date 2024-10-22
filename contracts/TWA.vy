# pragma version ~=0.4

"""
@title Time Weighted Average (TWA) Calculator

@notice Stores value snapshots and computes the Time Weighted Average (TWA) over
a specified time window.

@dev
- Stores value snapshots with timestamps in an array, only adding if the minimum
  time interval (`min_snapshot_dt_seconds`) has passed.
- Uses the trapezoidal rule to calculate the TWA over the `twa_window`.
- Functions:
  - `_take_snapshot`: Internal, adds a snapshot if the minimum interval passed.
    Wrapper required in importing contract.
  - `compute_twa`: Calculates and returns the TWA based on stored snapshots.
  - `get_len_snapshots`: Returns the number of stored snapshots.

@license Copyright (c) Curve.Fi, 2020-2024 - all rights reserved
@author curve.fi
@custom:security security@curve.fi
"""


################################################################
#                            EVENTS                            #
################################################################


event SnapshotTaken:
    value: uint256
    timestamp: uint256

event TWAWindowUpdated:
    new_window: uint256

event SnapshotIntervalUpdated:
    new_dt_seconds: uint256


################################################################
#                           CONSTANTS                          #
################################################################


MAX_SNAPSHOTS: constant(uint256) = 10**18  # 31.7 billion years if snapshot every second


################################################################
#                            STORAGE                           #
################################################################


min_snapshot_dt_seconds: public(uint256)  # Minimum time between snapshots in seconds
twa_window: public(uint256)  # Time window in seconds for TWA calculation
last_snapshot_timestamp: public(uint256)  # Timestamp of the last snapshot
snapshots: public(DynArray[Snapshot, MAX_SNAPSHOTS])


struct Snapshot:
    tracked_value: uint256
    timestamp: uint256


################################################################
#                          CONSTRUCTOR                         #
################################################################


@deploy
def __init__(_twa_window: uint256, _min_snapshot_dt_seconds: uint256):
    self._set_twa_window(_twa_window)
    self._set_snapshot_dt(max(1, _min_snapshot_dt_seconds))


################################################################
#                         VIEW FUNCTIONS                       #
################################################################


@external
@view
def get_len_snapshots() -> uint256:
    """
    @notice Returns the number of snapshots stored.
    """
    return len(self.snapshots)


@external
@view
def compute_twa() -> uint256:
    """
    @notice External endpoint for _compute() function.
    """
    return self._compute()


################################################################
#                       INTERNAL FUNCTIONS                     #
################################################################


@internal
def _take_snapshot(_value: uint256):
    """
    @notice Stores a snapshot of the tracked value.
    @param _value The value to store.
    """
    if (len(self.snapshots) == 0) or (  # First snapshot
        self.last_snapshot_timestamp + self.min_snapshot_dt_seconds <= block.timestamp # after dt
    ):
        self.last_snapshot_timestamp = block.timestamp
        self.snapshots.append(
            Snapshot(tracked_value=_value, timestamp=block.timestamp)
        )  # store the snapshot into the DynArray
        log SnapshotTaken(_value, block.timestamp)


@internal
def _set_twa_window(_new_window: uint256):
    """
    @notice Adjusts the TWA window.
    @param _new_window The new TWA window in seconds.
    @dev Only callable by the importing contract.
    """
    self.twa_window = _new_window
    log TWAWindowUpdated(_new_window)


@internal
def _set_snapshot_dt(_new_dt_seconds: uint256):
    """
    @notice Adjusts the minimum snapshot time interval.
    @param _new_dt_seconds The new minimum snapshot time interval in seconds.
    @dev Only callable by the importing contract.
    """
    self.min_snapshot_dt_seconds = _new_dt_seconds
    log SnapshotIntervalUpdated(_new_dt_seconds)


@internal
@view
def _compute() -> uint256:
    """
    @notice Computes the TWA over the specified time window by iterating backwards over the snapshots.
    @return The TWA for tracked value over the self.twa_window.
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
        if i != 0:  # If not the first iteration (last snapshot), get the next snapshot
            next_snapshot = self.snapshots[i_backwards + 1]

        # Time Axis (Increasing to the Right) --->
        #                                        SNAPSHOT
        # |---------|---------|---------|------------------------|---------|---------|
        # t0   time_window_start      interval_start        interval_end      block.timestamp (Now)

        interval_start: uint256 = current_snapshot.timestamp
        # Adjust interval start if it is before the time window start
        if interval_start < time_window_start:
            interval_start = time_window_start

        interval_end: uint256 = interval_start
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

    if total_time == 0 and len(self.snapshots) == 1:
        # case when only snapshot is taken in the block where computation is called
        return self.snapshots[0].tracked_value

    assert total_time > 0, "Zero total time!"
    twa: uint256 = total_weighted_tracked_value // total_time
    return twa
