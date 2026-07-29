from __future__ import annotations

import math
import signal
import sys
import time
from pathlib import Path

# Permite ejecutar este archivo directamente desde /scripts.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.engine.protocol import (  # noqa: E402
    EngineState,
    emit_error,
    emit_snapshot,
)


RUNNING = True


def stop_runtime(_signum: int, _frame: object) -> None:
    global RUNNING
    RUNNING = False


def main() -> int:
    signal.signal(signal.SIGINT, stop_runtime)

    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_runtime)

    tick = 0

    try:
        while RUNNING:
            phase = math.sin(tick * 0.35)

            emit_snapshot(
                bpm=128.0 + phase * 0.35,
                confidence=86.0 + phase * 5.0,
                audio_level=60.0 + phase * 18.0,
                state=EngineState.TRACKING,
                beat_detected=tick % 2 == 0,
            )

            tick += 1
            time.sleep(0.46)

    except KeyboardInterrupt:
        pass
    except Exception as error:
        emit_error(
            message=str(error),
            code="RUNTIME_FAILURE",
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())