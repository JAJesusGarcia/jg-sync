from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from statistics import median

from app.bpm.tempo import TempoEstimator


class TrackingState(str, Enum):
    """Current state of the beat tracking engine."""

    CALIBRATING = "CALIBRATING"
    TRACKING = "TRACKING"
    LOCKED = "LOCKED"
    LOST = "LOST"


@dataclass(frozen=True)
class BeatTrackingResult:
    """Result produced whenever a new onset is processed."""

    bpm: float | None
    interval: float | None
    confidence: float
    state: TrackingState
    accepted: bool
    samples: int


class BeatTracker:
    """
    Validate detected onsets and manage tempo tracking state.

    Responsibilities:
    - Find a consistent tempo during initial calibration.
    - Prevent the first few noisy onsets from defining the BPM.
    - Track confidence.
    - Expose CALIBRATING, TRACKING, LOCKED and LOST states.
    """

    def __init__(
        self,
        min_bpm: float = 70.0,
        max_bpm: float = 180.0,
        calibration_window: int = 12,
        minimum_consensus: int = 5,
        consensus_tolerance_percent: float = 7.0,
        lock_threshold: float = 0.80,
        lost_rejection_limit: int = 10,
    ) -> None:
        if min_bpm <= 0:
            raise ValueError("min_bpm must be greater than zero")

        if max_bpm <= min_bpm:
            raise ValueError("max_bpm must be greater than min_bpm")

        if calibration_window < 3:
            raise ValueError("calibration_window must be at least 3")

        if minimum_consensus < 2:
            raise ValueError("minimum_consensus must be at least 2")

        if minimum_consensus > calibration_window:
            raise ValueError(
                "minimum_consensus cannot exceed calibration_window"
            )

        self.min_bpm = min_bpm
        self.max_bpm = max_bpm
        self.calibration_window = calibration_window
        self.minimum_consensus = minimum_consensus
        self.consensus_tolerance_percent = (
            consensus_tolerance_percent
        )
        self.lock_threshold = lock_threshold
        self.lost_rejection_limit = lost_rejection_limit

        self.tempo_estimator = TempoEstimator(
            min_bpm=min_bpm,
            max_bpm=max_bpm,
        )

        self.state = TrackingState.CALIBRATING
        self.confidence = 0.0

        self.last_onset_time: float | None = None
        self.candidate_bpms: list[float] = []

        self.accepted_count = 0
        self.rejected_count = 0
        self.consecutive_rejections = 0

    @property
    def current_bpm(self) -> float | None:
        return self.tempo_estimator.current_bpm

    def process_onset(
        self,
        timestamp: float,
    ) -> BeatTrackingResult:
        """
        Process an onset timestamp and update the tracking state.
        """

        if self.last_onset_time is None:
            self.last_onset_time = timestamp

            return self._build_result(
                interval=None,
                accepted=False,
            )

        interval = timestamp - self.last_onset_time
        self.last_onset_time = timestamp

        if interval <= 0:
            return self._reject(interval)

        candidate_bpm = self._normalize_bpm(
            60.0 / interval
        )

        if candidate_bpm is None:
            return self._reject(interval)

        if self.state in {
            TrackingState.CALIBRATING,
            TrackingState.LOST,
        }:
            return self._process_calibration_candidate(
                timestamp=timestamp,
                interval=interval,
                candidate_bpm=candidate_bpm,
            )

        tempo_result = self.tempo_estimator.process_beat(
            timestamp
        )

        if tempo_result.accepted:
            self.accepted_count += 1
            self.consecutive_rejections = 0
            self._increase_confidence()

            if self.confidence >= self.lock_threshold:
                self.state = TrackingState.LOCKED
            else:
                self.state = TrackingState.TRACKING
        else:
            self.rejected_count += 1
            self.consecutive_rejections += 1
            self._decrease_confidence()

            if (
                self.consecutive_rejections
                >= self.lost_rejection_limit
            ):
                self._enter_lost_state()

        return BeatTrackingResult(
            bpm=self.current_bpm,
            interval=interval,
            confidence=self.confidence,
            state=self.state,
            accepted=tempo_result.accepted,
            samples=tempo_result.samples,
        )

    def reset(self) -> None:
        """Reset the complete tracker state."""

        self.tempo_estimator.reset()

        self.state = TrackingState.CALIBRATING
        self.confidence = 0.0

        self.last_onset_time = None
        self.candidate_bpms.clear()

        self.accepted_count = 0
        self.rejected_count = 0
        self.consecutive_rejections = 0

    def _process_calibration_candidate(
        self,
        timestamp: float,
        interval: float,
        candidate_bpm: float,
    ) -> BeatTrackingResult:
        self.candidate_bpms.append(candidate_bpm)

        if len(self.candidate_bpms) > self.calibration_window:
            self.candidate_bpms.pop(0)

        consensus = self._find_consensus()

        if len(consensus) < self.minimum_consensus:
            self.confidence = min(
                len(consensus) / self.minimum_consensus,
                0.75,
            )

            return self._build_result(
                interval=interval,
                accepted=False,
            )

        consensus_bpm = median(consensus)

        self._seed_tempo_estimator(
            timestamp=timestamp,
            bpm=consensus_bpm,
            sample_count=len(consensus),
        )

        self.accepted_count += 1
        self.consecutive_rejections = 0

        self.confidence = min(
            len(consensus) / self.calibration_window,
            1.0,
        )

        if self.confidence >= self.lock_threshold:
            self.state = TrackingState.LOCKED
        else:
            self.state = TrackingState.TRACKING

        return self._build_result(
            interval=interval,
            accepted=True,
        )

    def _find_consensus(self) -> list[float]:
        """
        Return the largest cluster of BPM candidates.

        Candidates belong to the same cluster when their percentage
        difference stays within the configured tolerance.
        """

        if not self.candidate_bpms:
            return []

        best_cluster: list[float] = []

        for reference in self.candidate_bpms:
            cluster = [
                candidate
                for candidate in self.candidate_bpms
                if self._percentage_difference(
                    candidate,
                    reference,
                )
                <= self.consensus_tolerance_percent
            ]

            if len(cluster) > len(best_cluster):
                best_cluster = cluster

        return best_cluster

    def _seed_tempo_estimator(
        self,
        timestamp: float,
        bpm: float,
        sample_count: int,
    ) -> None:
        """
        Seed TempoEstimator with consistent synthetic beat timestamps.

        The final synthetic timestamp matches the real current onset,
        preventing a large artificial interval on the next beat.
        """

        self.tempo_estimator.reset()

        interval = 60.0 / bpm
        count = max(sample_count, 2)

        start_time = timestamp - interval * (count - 1)

        for index in range(count):
            beat_time = start_time + interval * index
            self.tempo_estimator.process_beat(beat_time)

    def _normalize_bpm(
        self,
        bpm: float,
    ) -> float | None:
        """
        Normalize half-time and double-time BPM values into range.
        """

        if bpm <= 0:
            return None

        normalized = bpm

        while normalized < self.min_bpm:
            normalized *= 2.0

        while normalized > self.max_bpm:
            normalized /= 2.0

        if not self.min_bpm <= normalized <= self.max_bpm:
            return None

        return normalized

    def _increase_confidence(self) -> None:
        self.confidence = min(
            self.confidence + 0.08,
            1.0,
        )

    def _decrease_confidence(self) -> None:
        self.confidence = max(
            self.confidence - 0.06,
            0.0,
        )

    def _enter_lost_state(self) -> None:
        self.state = TrackingState.LOST
        self.confidence = 0.0
        self.candidate_bpms.clear()
        self.tempo_estimator.reset()
        self.consecutive_rejections = 0

    def _reject(
        self,
        interval: float | None,
    ) -> BeatTrackingResult:
        self.rejected_count += 1
        self.consecutive_rejections += 1

        if self.state not in {
            TrackingState.CALIBRATING,
            TrackingState.LOST,
        }:
            self._decrease_confidence()

        return self._build_result(
            interval=interval,
            accepted=False,
        )

    def _build_result(
        self,
        interval: float | None,
        accepted: bool,
    ) -> BeatTrackingResult:
        samples = len(
            self.tempo_estimator.bpm_history
        )

        return BeatTrackingResult(
            bpm=self.current_bpm,
            interval=interval,
            confidence=self.confidence,
            state=self.state,
            accepted=accepted,
            samples=samples,
        )

    @staticmethod
    def _percentage_difference(
        first: float,
        second: float,
    ) -> float:
        if first == 0 and second == 0:
            return 0.0

        average = (abs(first) + abs(second)) / 2.0

        if average == 0:
            return 100.0

        return abs(first - second) / average * 100.0