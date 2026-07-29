from __future__ import annotations

import math
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass

import numpy as np
import sounddevice as sd


@dataclass(frozen=True)
class AudioLevel:
    """Current audio signal measurements."""

    rms: float
    peak: float
    dbfs: float


@dataclass(frozen=True)
class AudioBlock:
    """
    One captured audio block together with its audio-clock timestamp.

    timestamp represents the estimated centre of the input block.
    """

    samples: np.ndarray
    timestamp: float
    sequence: int
    frames: int


class AudioCapture:
    """Real-time audio input engine for JG Sync."""

    def __init__(
        self,
        device_id: int | None = None,
        sample_rate: int = 44100,
        block_size: int = 1024,
        channels: int = 1,
        queue_size: int = 128,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError(
                "sample_rate must be greater than zero"
            )

        if block_size <= 0:
            raise ValueError(
                "block_size must be greater than zero"
            )

        if channels <= 0:
            raise ValueError(
                "channels must be greater than zero"
            )

        if queue_size < 1:
            raise ValueError(
                "queue_size must be greater than zero"
            )

        self.device_id = device_id
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels

        self.stream: sd.InputStream | None = None

        # Preserved for compatibility with existing tests/code.
        self.latest_samples: np.ndarray | None = None

        self.current_level = AudioLevel(
            rms=0.0,
            peak=0.0,
            dbfs=-100.0,
        )

        self._blocks: deque[AudioBlock] = deque(
            maxlen=queue_size
        )

        self._queue_lock = threading.Lock()

        self._sequence = 0
        self._dropped_blocks = 0
        self._captured_frames = 0
        self._audio_clock_start = 0.0

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time,
        status: sd.CallbackFlags,
    ) -> None:
        """Capture and enqueue one incoming audio block."""

        if status:
            print(
                f"Audio warning: {status}",
                file=sys.stderr,
                flush=True,
            )

        samples = np.asarray(
            indata,
            dtype=np.float32,
        ).copy()

        self.latest_samples = samples

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(samples)
                )
            )
        )

        peak = float(
            np.max(
                np.abs(samples)
            )
        )

        if rms > 0:
            dbfs = 20.0 * math.log10(rms)
        else:
            dbfs = -100.0

        self.current_level = AudioLevel(
            rms=rms,
            peak=peak,
            dbfs=dbfs,
        )

        block_duration = (
            frames / float(self.sample_rate)
        )

        if self._sequence == 0:
            self._audio_clock_start = time_module_perf_counter()

        block_start_timestamp = (
            self._audio_clock_start
            + self._captured_frames
            / float(self.sample_rate)
        )

        block_timestamp = (
            block_start_timestamp
            + block_duration / 2.0
        )

        self._captured_frames += frames

        block = AudioBlock(
            samples=samples,
            timestamp=block_timestamp,
            sequence=self._sequence,
            frames=frames,
        )

        self._sequence += 1

        with self._queue_lock:
            if len(self._blocks) == self._blocks.maxlen:
                self._dropped_blocks += 1

            self._blocks.append(block)

    def start(self) -> None:
        """Start capturing audio."""

        if self.stream is not None:
            return

        self.clear_blocks()

        self.stream = sd.InputStream(
            device=self.device_id,
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            channels=self.channels,
            dtype="float32",
            callback=self._audio_callback,
        )

        self.stream.start()

    def stop(self) -> None:
        """Stop capturing audio."""

        if self.stream is None:
            return

        self.stream.stop()
        self.stream.close()

        self.stream = None
        self.latest_samples = None

        self.clear_blocks()

    def pop_block(self) -> AudioBlock | None:
        """Return the oldest unprocessed audio block."""

        with self._queue_lock:
            if not self._blocks:
                return None

            return self._blocks.popleft()

    def clear_blocks(self) -> None:
        """Clear queued audio blocks and reset queue counters."""

        with self._queue_lock:
            self._blocks.clear()

        self._sequence = 0
        self._dropped_blocks = 0
        self._captured_frames = 0
        self._audio_clock_start = 0.0

    @property
    def queued_block_count(self) -> int:
        """Return the number of queued audio blocks."""

        with self._queue_lock:
            return len(self._blocks)

    @property
    def dropped_blocks(self) -> int:
        """Return the number of overwritten queue blocks."""

        return self._dropped_blocks

    @property
    def is_running(self) -> bool:
        """Return whether the audio stream is currently active."""

        return bool(
            self.stream is not None
            and self.stream.active
        )


def time_module_perf_counter() -> float:
    """
    Return a monotonic high-resolution timestamp.

    This helper avoids shadowing the imported time module with the
    callback's `time` argument required by sounddevice and the tests.
    """

    return time.perf_counter()