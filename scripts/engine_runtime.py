from __future__ import annotations

import signal
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.audio.capture import AudioCapture  # noqa: E402
from app.bpm.onset import EnergyOnsetDetector  # noqa: E402
from app.bpm.tracker import BeatTracker  # noqa: E402
from app.engine.protocol import (  # noqa: E402
    EngineState,
    emit_error,
    emit_snapshot,
)


RUNNING = True

LOOP_SLEEP_SECONDS = 0.005
SNAPSHOT_INTERVAL_SECONDS = 0.05

MIN_DBFS = -60.0
MAX_DBFS = 0.0


def stop_runtime(_signum: int, _frame: object) -> None:
    global RUNNING
    RUNNING = False


def dbfs_to_percentage(dbfs: float) -> float:
    """
    Convert a dBFS value into a UI-friendly 0–100 percentage.

    Values at or below -60 dBFS are shown as silence.
    0 dBFS represents the maximum digital signal level.
    """

    clamped = min(max(dbfs, MIN_DBFS), MAX_DBFS)

    return (
        (clamped - MIN_DBFS)
        / (MAX_DBFS - MIN_DBFS)
        * 100.0
    )


def normalize_engine_state(state_value: str) -> EngineState:
    """
    Convert the BeatTracker state into the public engine protocol state.
    """

    try:
        return EngineState(state_value)
    except ValueError:
        return EngineState.TRACKING


def main() -> int:
    signal.signal(signal.SIGINT, stop_runtime)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_runtime)

    capture = AudioCapture()
    detector = EnergyOnsetDetector()
    tracker = BeatTracker()

    last_samples = None
    last_snapshot_time = 0.0

    current_bpm = 0.0
    current_confidence = 0.0
    current_state = EngineState.CALIBRATING

    pending_beat = False

    try:
        capture.start()

        while RUNNING:
            samples = capture.latest_samples

            if samples is not None and samples is not last_samples:
                onset_result = detector.process(samples)
                last_samples = samples

                if onset_result.detected:
                    onset_timestamp = time.perf_counter()
                    tracking_result = tracker.process_onset(
                        onset_timestamp
                    )

                    if tracking_result.bpm is not None:
                        current_bpm = tracking_result.bpm

                    current_confidence = (
                        tracking_result.confidence * 100.0
                    )

                    current_state = normalize_engine_state(
                        tracking_result.state.value
                    )

                    # Only accepted onsets are exposed as actual beats.
                    pending_beat = tracking_result.accepted

            now = time.perf_counter()

            if (
                now - last_snapshot_time
                >= SNAPSHOT_INTERVAL_SECONDS
            ):
                audio_level = dbfs_to_percentage(
                    capture.current_level.dbfs
                )

                emit_snapshot(
                    bpm=current_bpm,
                    confidence=current_confidence,
                    audio_level=audio_level,
                    state=current_state,
                    beat_detected=pending_beat,
                    connected=capture.is_running,
                )

                # The beat flag behaves like a one-frame event.
                pending_beat = False
                last_snapshot_time = now

            time.sleep(LOOP_SLEEP_SECONDS)

    except KeyboardInterrupt:
        pass

    except Exception as error:
        emit_error(
            message=str(error),
            code="RUNTIME_FAILURE",
        )
        return 1

    finally:
        capture.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())