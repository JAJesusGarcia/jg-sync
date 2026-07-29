from __future__ import annotations

import pytest

from app.bpm.tracker import BeatTracker, TrackingState


def feed_beats(
    tracker: BeatTracker,
    timestamps: list[float],
):
    return [
        tracker.process_onset(timestamp)
        for timestamp in timestamps
    ]


def test_regular_126_bpm_signal() -> None:
    tracker = BeatTracker(
        calibration_window=8,
        minimum_consensus=5,
    )

    interval = 60.0 / 126.0
    timestamps = [
        index * interval
        for index in range(10)
    ]

    results = feed_beats(tracker, timestamps)

    assert results[-1].bpm == pytest.approx(
        126.0,
        abs=0.5,
    )
    assert results[-1].state in {
        TrackingState.TRACKING,
        TrackingState.LOCKED,
    }


def test_double_trigger_does_not_replace_onset_anchor() -> None:
    tracker = BeatTracker(
        calibration_window=8,
        minimum_consensus=5,
    )

    first = tracker.process_onset(0.0)
    duplicate = tracker.process_onset(0.230)
    real_beat = tracker.process_onset(0.476)

    assert first.accepted is False
    assert duplicate.accepted is False

    # The valid beat must still be measured from 0.0,
    # not from the rejected transient at 0.230.
    assert real_beat.interval == pytest.approx(
        0.476,
        abs=0.001,
    )


def test_double_triggers_do_not_corrupt_126_bpm_tracking() -> None:
    tracker = BeatTracker(
        calibration_window=8,
        minimum_consensus=5,
    )

    beat_interval = 60.0 / 126.0
    timestamps: list[float] = []

    for index in range(10):
        beat_time = index * beat_interval
        timestamps.append(beat_time)

        if index < 9:
            timestamps.append(
                beat_time + 0.230
            )

    results = feed_beats(tracker, timestamps)

    assert tracker.current_bpm == pytest.approx(
        126.0,
        abs=1.0,
    )

    accepted_results = [
        result
        for result in results
        if result.accepted
    ]

    assert accepted_results


def test_reset_clears_tracker() -> None:
    tracker = BeatTracker()

    tracker.process_onset(0.0)
    tracker.process_onset(0.476)
    tracker.reset()

    assert tracker.current_bpm is None
    assert tracker.last_onset_time is None
    assert tracker.state is TrackingState.CALIBRATING
    assert tracker.confidence == 0.0