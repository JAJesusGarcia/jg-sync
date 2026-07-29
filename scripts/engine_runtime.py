from __future__ import annotations

import signal
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.audio.capture import AudioCapture  # noqa: E402
from app.bpm.spectral_onset import (  # noqa: E402
    SpectralFluxOnsetDetector,
)
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


def stop_runtime(
    _signum: int,
    _frame: object,
) -> None:
    """Stop the runtime loop gracefully."""

    global RUNNING
    RUNNING = False


def dbfs_to_percentage(dbfs: float) -> float:
    """
    Convert a dBFS value into a UI-friendly 0–100 percentage.

    Values at or below -60 dBFS are shown as silence.
    0 dBFS represents the maximum digital signal level.
    """

    clamped = min(
        max(dbfs, MIN_DBFS),
        MAX_DBFS,
    )

    return (
        (clamped - MIN_DBFS)
        / (MAX_DBFS - MIN_DBFS)
        * 100.0
    )


def normalize_engine_state(
    state_value: str,
) -> EngineState:
    """
    Convert the BeatTracker state into the public engine protocol state.
    """

    try:
        return EngineState(state_value)
    except ValueError:
        return EngineState.TRACKING


def main() -> int:
    signal.signal(
        signal.SIGINT,
        stop_runtime,
    )

    if hasattr(signal, "SIGTERM"):
        signal.signal(
            signal.SIGTERM,
            stop_runtime,
        )

    capture = AudioCapture()

    detector = SpectralFluxOnsetDetector(
        block_size=capture.block_size,
    )

    tracker = BeatTracker()

    last_snapshot_time = 0.0
    last_reported_dropped_blocks = 0

    current_bpm = 0.0
    current_confidence = 0.0
    current_state = EngineState.CALIBRATING

    pending_beat = False

    try:
        capture.start()

        while RUNNING:
            # Drain every currently queued audio block.
            #
            # This prevents old blocks from accumulating while the
            # runtime processes only the newest available input.
            while True:
                audio_block = capture.pop_block()

                if audio_block is None:
                    break

                onset_result = detector.process(
                    audio_block.samples
                )

                if not onset_result.detected:
                    continue

                tracking_result = tracker.process_onset(
                    audio_block.timestamp
                )

                if tracking_result.interval is None:
                    print(
                        (
                            "onset"
                            f" | block={audio_block.sequence}"
                            " | first candidate"
                        ),
                        file=sys.stderr,
                        flush=True,
                    )
                else:
                    raw_candidate_bpm = (
                        60.0
                        / tracking_result.interval
                    )

                    print(
                        (
                            "onset"
                            f" | block={audio_block.sequence}"
                            f" | interval="
                            f"{tracking_result.interval:.6f}s"
                            f" | raw="
                            f"{raw_candidate_bpm:7.3f} BPM"
                            f" | accepted="
                            f"{tracking_result.accepted}"
                            f" | state="
                            f"{tracking_result.state.value}"
                        ),
                        file=sys.stderr,
                        flush=True,
                    )

                if tracking_result.bpm is not None:
                    current_bpm = (
                        tracking_result.bpm
                    )

                current_confidence = (
                    tracking_result.confidence
                    * 100.0
                )

                current_state = normalize_engine_state(
                    tracking_result.state.value
                )

                # Preserve a detected beat until the next snapshot.
                #
                # Using `or` prevents a later rejected onset from
                # clearing an accepted beat before it reaches the UI.
                pending_beat = (
                    pending_beat
                    or tracking_result.accepted
                )

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

            # Report queue overflow only when the count changes.
            if (
                capture.dropped_blocks
                > last_reported_dropped_blocks
            ):
                last_reported_dropped_blocks = (
                    capture.dropped_blocks
                )

                print(
                    (
                        "audio queue warning"
                        f" | dropped="
                        f"{capture.dropped_blocks}"
                        f" | queued="
                        f"{capture.queued_block_count}"
                    ),
                    file=sys.stderr,
                    flush=True,
                )

            time.sleep(
                LOOP_SLEEP_SECONDS
            )

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