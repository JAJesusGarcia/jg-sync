from __future__ import annotations

import pytest

from app.bpm.tracker import BeatTracker, TrackingState


def feed_regular_beats(
    tracker: BeatTracker,
    *,
    bpm: float,
    count: int,
    start_time: float = 0.0,
) -> list:
    interval = 60.0 / bpm
    results = []

    for index in range(count):
        timestamp = start_time + index * interval
        results.append(tracker.process_onset(timestamp))

    return results


def test_starts_calibrating() -> None:
    tracker = BeatTracker()

    assert tracker.current_bpm is None
    assert tracker.state is TrackingState.CALIBRATING
    assert tracker.confidence == 0.0


def test_calibrates_with_regular_120_bpm_beats() -> None:
    tracker = BeatTracker(
        calibration_window=8,
        minimum_consensus=5,
    )

    results = feed_regular_beats(
        tracker,
        bpm=120.0,
        count=8,
    )

    result = results[-1]

    assert result.bpm == pytest.approx(120.0, abs=0.5)
    assert result.state in {
        TrackingState.TRACKING,
        TrackingState.LOCKED,
    }


def test_calibrates_with_regular_126_bpm_beats() -> None:
    tracker = BeatTracker(
        calibration_window=12,
        minimum_consensus=5,
    )

    results = feed_regular_beats(
        tracker,
        bpm=126.0,
        count=10,
    )

    result = results[-1]

    assert result.bpm == pytest.approx(126.0, abs=0.5)
    assert result.confidence > 0.0


def test_accepts_small_timing_jitter() -> None:
    tracker = BeatTracker(
        calibration_window=10,
        minimum_consensus=5,
    )

    interval = 60.0 / 126.0
    jitters = [
        0.000,
        0.006,
        -0.004,
        0.003,
        -0.007,
        0.005,
        -0.002,
        0.004,
        -0.003,
        0.001,
    ]

    timestamp = 0.0
    result = tracker.process_onset(timestamp)

    for jitter in jitters:
        timestamp += interval + jitter
        result = tracker.process_onset(timestamp)

    assert result.bpm == pytest.approx(126.0, abs=2.0)
    assert result.state in {
        TrackingState.TRACKING,
        TrackingState.LOCKED,
    }


def test_normalizes_half_time_to_valid_range() -> None:
    tracker = BeatTracker(
        calibration_window=8,
        minimum_consensus=5,
    )

    results = feed_regular_beats(
        tracker,
        bpm=60.0,
        count=8,
    )

    assert results[-1].bpm == pytest.approx(120.0, abs=0.5)


def test_reset_clears_tracking_state() -> None:
    tracker = BeatTracker(
        calibration_window=8,
        minimum_consensus=5,
    )

    feed_regular_beats(
        tracker,
        bpm=128.0,
        count=8,
    )

    tracker.reset()

    assert tracker.current_bpm is None
    assert tracker.state is TrackingState.CALIBRATING
    assert tracker.confidence == 0.0
    assert tracker.last_onset_time is None
    assert tracker.candidate_bpms == []
    assert tracker.accepted_count == 0
    assert tracker.rejected_count == 0