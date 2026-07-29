from __future__ import annotations

import pytest

from app.bpm.tempo import TempoEstimator


def test_double_trigger_does_not_move_beat_anchor() -> None:
    estimator = TempoEstimator()

    estimator.process_beat(0.0)

    duplicate = estimator.process_beat(0.230)
    real_beat = estimator.process_beat(0.476)

    assert duplicate.accepted is False
    assert real_beat.accepted is True
    assert real_beat.interval == pytest.approx(
        0.476,
        abs=0.001,
    )
    assert real_beat.bpm == pytest.approx(
        126.05,
        abs=0.5,
    )


def test_regular_126_bpm_beats() -> None:
    estimator = TempoEstimator()

    interval = 60.0 / 126.0
    result = None

    for index in range(10):
        result = estimator.process_beat(
            index * interval
        )

    assert result is not None
    assert result.bpm == pytest.approx(
        126.0,
        abs=0.5,
    )