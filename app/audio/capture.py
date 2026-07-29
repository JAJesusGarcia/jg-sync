from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np
import sounddevice as sd


@dataclass
class AudioLevel:
    """Current audio signal measurements."""

    rms: float
    peak: float
    dbfs: float


class AudioCapture:
    """Real-time audio input engine for JG Sync."""

    def __init__(
        self,
        device_id: int | None = None,
        sample_rate: int = 44100,
        block_size: int = 1024,
        channels: int = 1,
    ) -> None:
        self.device_id = device_id
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels

        self.stream: sd.InputStream | None = None
        self.latest_samples: np.ndarray | None = None

        self.current_level = AudioLevel(
            rms=0.0,
            peak=0.0,
            dbfs=-100.0,
        )

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time,
        status: sd.CallbackFlags,
    ) -> None:
        """Process each incoming block of audio."""

        # if status:
        #     print(f"\nAudio warning: {status}")
        if status:
            print(
                f"Audio warning: {status}",
                file=sys.stderr,
                flush=True,
            )

        samples = np.asarray(indata, dtype=np.float32)

        self.latest_samples = samples.copy()

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(samples)
                )
            )
        )

        peak = float(np.max(np.abs(samples)))

        if rms > 0:
            dbfs = 20 * math.log10(rms)
        else:
            dbfs = -100.0

        self.current_level = AudioLevel(
            rms=rms,
            peak=peak,
            dbfs=dbfs,
        )

    def start(self) -> None:
        """Start capturing audio."""

        if self.stream is not None:
            return

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

    @property
    def is_running(self) -> bool:
        """Return whether the audio stream is currently active."""

        return bool(
            self.stream is not None
            and self.stream.active
        )