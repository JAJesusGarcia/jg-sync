import pytest

from app.bpm.tempo import TempoEstimator


def feed_beats(
    estimator: TempoEstimator,
    bpm: float,
    count: int = 10,
) -> None:
    """Feed perfectly timed beats into the estimator."""

    interval = 60.0 / bpm
    timestamp = 0.0

    estimator.process_beat(timestamp)

    for _ in range(count):
        timestamp += interval
        estimator.process_beat(timestamp)


def test_detects_120_bpm():
    estimator = TempoEstimator()

    feed_beats(estimator, 120.0)

    assert estimator.current_bpm == pytest.approx(
        120.0,
        abs=0.1,
    )


def test_detects_128_bpm():
    estimator = TempoEstimator()

    feed_beats(estimator, 128.0)

    assert estimator.current_bpm == pytest.approx(
        128.0,
        abs=0.1,
    )


def test_normalizes_half_time():
    estimator = TempoEstimator(
        min_bpm=70.0,
        max_bpm=180.0,
    )

    normalized = estimator._normalize_bpm(64.0)

    assert normalized == pytest.approx(128.0)


def test_normalizes_double_time():
    estimator = TempoEstimator(
        min_bpm=70.0,
        max_bpm=180.0,
    )

    normalized = estimator._normalize_bpm(256.0)

    assert normalized == pytest.approx(128.0)


def test_rejects_outlier_after_calibration():
    estimator = TempoEstimator(
        tolerance_percent=12.0,
    )

    feed_beats(
        estimator,
        bpm=128.0,
        count=6,
    )

    stable_before = estimator.current_bpm

    # Approximately 90 BPM.
    result = estimator.process_beat(
        estimator.last_beat_time + (60.0 / 90.0)
    )

    assert result.accepted is False
    assert estimator.current_bpm == pytest.approx(
        stable_before,
        abs=0.1,
    )


def test_reset_clears_tempo_state():
    estimator = TempoEstimator()

    feed_beats(estimator, 128.0)

    estimator.reset()

    assert estimator.current_bpm is None
    assert estimator.last_beat_time is None
    assert len(estimator.bpm_history) == 0