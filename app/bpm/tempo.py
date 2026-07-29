from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from statistics import median


@dataclass(frozen=True)
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
        if min_bpm <= 0:
            raise ValueError(
                "min_bpm must be greater than zero"
            )

        if max_bpm <= min_bpm:
            raise ValueError(
                "max_bpm must be greater than min_bpm"
            )

        if history_size < 1:
            raise ValueError(
                "history_size must be greater than zero"
            )

        if tolerance_percent <= 0:
            raise ValueError(
                "tolerance_percent must be greater than zero"
            )

        self.min_bpm = min_bpm
        self.max_bpm = max_bpm
        self.tolerance_percent = tolerance_percent

        self.last_beat_time: float | None = None

        self.bpm_history: deque[float] = deque(
            maxlen=history_size,
        )

    def process_beat(
        self,
        timestamp: float,
    ) -> TempoResult:
        """
        Process a detected beat timestamp and update tempo state.

        Duplicate fast onsets are rejected without replacing the
        previous valid beat timestamp.
        """

        if self.last_beat_time is None:
            self.last_beat_time = timestamp

            return TempoResult(
                bpm=None,
                interval=None,
                samples=0,
                accepted=False,
            )

        interval = timestamp - self.last_beat_time

        if interval <= 0:
            return self._build_result(
                interval=interval,
                accepted=False,
            )

        raw_bpm = 60.0 / interval

        # Reject duplicate fast transients.
        #
        # Do not move last_beat_time, because the next real beat
        # must still be measured from the previous valid beat.
        if raw_bpm > self.max_bpm:
            return self._build_result(
                interval=interval,
                accepted=False,
            )

        candidate_bpm = self._normalize_bpm(
            raw_bpm
        )

        if candidate_bpm is None:
            return self._build_result(
                interval=interval,
                accepted=False,
            )

        # This timestamp is temporally valid and can become the
        # new beat reference.
        self.last_beat_time = timestamp

        if self._is_candidate_acceptable(
            candidate_bpm
        ):
            self.bpm_history.append(
                candidate_bpm
            )

            return self._build_result(
                interval=interval,
                accepted=True,
            )

        return self._build_result(
            interval=interval,
            accepted=False,
        )

    def _normalize_bpm(
        self,
        bpm: float,
    ) -> float | None:
        """
        Normalize missed beats while rejecting duplicate fast onsets.

        Slow candidates can represent missed beats and are doubled
        until they enter the supported BPM range.

        Fast candidates above max_bpm are not divided by two because
        they usually represent duplicate onset detections.
        """

        if bpm <= 0:
            return None

        if bpm > self.max_bpm:
            return None

        normalized = bpm

        while normalized < self.min_bpm:
            normalized *= 2.0

        if not self.min_bpm <= normalized <= self.max_bpm:
            return None

        return normalized

    def _is_candidate_acceptable(
        self,
        candidate_bpm: float,
    ) -> bool:
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

        difference = abs(
            candidate_bpm - stable_bpm
        )

        tolerance = stable_bpm * (
            self.tolerance_percent / 100.0
        )

        return difference <= tolerance

    @property
    def current_bpm(self) -> float | None:
        """Return the median BPM from recent accepted measurements."""

        if not self.bpm_history:
            return None

        return float(
            median(self.bpm_history)
        )

    def reset(self) -> None:
        """Reset tempo estimation state."""

        self.last_beat_time = None
        self.bpm_history.clear()

    def _build_result(
        self,
        interval: float | None,
        accepted: bool,
    ) -> TempoResult:
        return TempoResult(
            bpm=self.current_bpm,
            interval=interval,
            samples=len(self.bpm_history),
            accepted=accepted,
        )