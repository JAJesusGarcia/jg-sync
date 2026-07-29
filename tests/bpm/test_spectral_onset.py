from __future__ import annotations

import numpy as np

from app.bpm.spectral_onset import (
    SpectralFluxOnsetDetector,
)


def test_first_block_does_not_detect_onset() -> None:
    detector = SpectralFluxOnsetDetector(
        block_size=1024,
    )

    samples = np.zeros(
        1024,
        dtype=np.float32,
    )

    result = detector.process(samples)

    assert result.detected is False
    assert result.flux == 0.0


def test_silence_does_not_trigger_onset() -> None:
    detector = SpectralFluxOnsetDetector(
        block_size=1024,
    )

    samples = np.zeros(
        1024,
        dtype=np.float32,
    )

    results = [
        detector.process(samples)
        for _ in range(20)
    ]

    assert all(
        result.detected is False
        for result in results
    )


def test_transient_can_trigger_onset() -> None:
    detector = SpectralFluxOnsetDetector(
        block_size=1024,
        sensitivity=1.5,
        minimum_threshold=0.001,
        minimum_rms=0.0001,
    )

    silence = np.zeros(
        1024,
        dtype=np.float32,
    )

    for _ in range(8):
        detector.process(silence)

    transient = np.zeros(
        1024,
        dtype=np.float32,
    )
    transient[:32] = 1.0

    result = detector.process(transient)

    assert result.detected is True
    assert result.flux > result.threshold


def test_constant_tone_is_not_repeatedly_detected() -> None:
    detector = SpectralFluxOnsetDetector(
        block_size=1024,
        sensitivity=1.5,
        minimum_threshold=0.001,
        minimum_rms=0.0001,
    )

    time_axis = np.arange(
        1024,
        dtype=np.float32,
    )

    tone = np.sin(
        2.0
        * np.pi
        * 440.0
        * time_axis
        / 44100.0
    ).astype(np.float32)

    results = [
        detector.process(tone)
        for _ in range(20)
    ]

    detections = sum(
        result.detected
        for result in results
    )

    assert detections <= 1


def test_reset_clears_detector_state() -> None:
    detector = SpectralFluxOnsetDetector(
        block_size=1024,
    )

    samples = np.ones(
        1024,
        dtype=np.float32,
    )

    detector.process(samples)
    detector.process(samples)
    detector.reset()

    assert detector.previous_spectrum is None
    assert len(detector.flux_history) == 0
    assert detector.cooldown == 0