from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import TextIO


class EngineState(str, Enum):
    CALIBRATING = "CALIBRATING"
    TRACKING = "TRACKING"
    LOCKED = "LOCKED"
    LOST = "LOST"


@dataclass(slots=True)
class EngineSnapshot:
    bpm: float
    confidence: float
    audio_level: float
    state: EngineState
    beat_detected: bool
    connected: bool
    timestamp: float

    def to_message(self) -> dict[str, object]:
        payload = asdict(self)

        return {
            "type": "snapshot",
            "bpm": payload["bpm"],
            "confidence": payload["confidence"],
            "audioLevel": payload["audio_level"],
            "state": self.state.value,
            "beatDetected": payload["beat_detected"],
            "connected": payload["connected"],
            "timestamp": payload["timestamp"],
        }


def emit_message(
    message: dict[str, object],
    output: TextIO = sys.stdout,
) -> None:
    """Write one compact JSON message per line."""

    serialized = json.dumps(
        message,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    print(serialized, file=output, flush=True)


def emit_snapshot(
    *,
    bpm: float,
    confidence: float,
    audio_level: float,
    state: EngineState,
    beat_detected: bool,
    connected: bool = True,
) -> None:
    snapshot = EngineSnapshot(
        bpm=round(max(0.0, bpm), 2),
        confidence=round(min(max(confidence, 0.0), 100.0), 2),
        audio_level=round(min(max(audio_level, 0.0), 100.0), 2),
        state=state,
        beat_detected=beat_detected,
        connected=connected,
        timestamp=time.time(),
    )

    emit_message(snapshot.to_message())


def emit_error(message: str, code: str = "ENGINE_ERROR") -> None:
    emit_message(
        {
            "type": "error",
            "code": code,
            "message": message,
            "timestamp": time.time(),
        },
        output=sys.stderr,
    )