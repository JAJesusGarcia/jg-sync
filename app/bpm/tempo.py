from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import median


@dataclass
class TempoResult:
    bpm: float | None
    interval: float | None
    samples: int
    accepted: bool


class TempoEstimator:
    """Estimate and stabilize tempo from detected beat timestamps."""

    def __init__(
        self,
        min_bpm: float = 70.0,
        max_bpm: float = 180.0,
        history_size: int = 8,
        tolerance_percent: float = 12.0,
    ) -> None:
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm
        self.tolerance_percent = tolerance_percent

        self.last_beat_time: float | None = None

        self.bpm_history: deque[float] = deque(
            maxlen=history_size,
        )

    def process_beat(self, timestamp: float) -> TempoResult:
        """Process a detected beat timestamp and update tempo state."""

        if self.last_beat_time is None:
            self.last_beat_time = timestamp

            return TempoResult(
                bpm=None,
                interval=None,
                samples=0,
                accepted=False,
            )

        interval = timestamp - self.last_beat_time
        self.last_beat_time = timestamp

        if interval <= 0:
            return TempoResult(
                bpm=self.current_bpm,
                interval=interval,
                samples=len(self.bpm_history),
                accepted=False,
            )

        raw_bpm = 60.0 / interval
        candidate_bpm = self._normalize_bpm(raw_bpm)

        if candidate_bpm is None:
            return TempoResult(
                bpm=self.current_bpm,
                interval=interval,
                samples=len(self.bpm_history),
                accepted=False,
            )

        if self._is_candidate_acceptable(candidate_bpm):
            self.bpm_history.append(candidate_bpm)

            return TempoResult(
                bpm=self.current_bpm,
                interval=interval,
                samples=len(self.bpm_history),
                accepted=True,
            )

        return TempoResult(
            bpm=self.current_bpm,
            interval=interval,
            samples=len(self.bpm_history),
            accepted=False,
        )

    def _normalize_bpm(self, bpm: float) -> float | None:
        """Normalize half-time and double-time BPM values."""

        if bpm <= 0:
            return None

        while bpm < self.min_bpm:
            bpm *= 2.0

        while bpm > self.max_bpm:
            bpm /= 2.0

        if self.min_bpm <= bpm <= self.max_bpm:
            return bpm

        return None

    def _is_candidate_acceptable(self, candidate_bpm: float) -> bool:
        """
        Accept candidates close to the current stable tempo.

        During initial calibration there is not enough context,
        so the first few valid candidates are accepted freely.
        """

        if len(self.bpm_history) < 3:
            return True

        stable_bpm = self.current_bpm

        if stable_bpm is None:
            return True

        difference = abs(candidate_bpm - stable_bpm)
        tolerance = stable_bpm * (self.tolerance_percent / 100.0)

        if difference <= tolerance:
            return True

        half_candidate = candidate_bpm * 2.0
        double_candidate = candidate_bpm / 2.0

        if abs(half_candidate - stable_bpm) <= tolerance:
            return True

        if abs(double_candidate - stable_bpm) <= tolerance:
            return True

        return False

    @property
    def current_bpm(self) -> float | None:
        """Return the median BPM from recent accepted measurements."""

        if not self.bpm_history:
            return None

        return float(median(self.bpm_history))

    def reset(self) -> None:
        """Reset tempo estimation state."""

        self.last_beat_time = None
        self.bpm_history.clear()