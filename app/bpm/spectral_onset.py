from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpectralOnsetResult:
    """Result of spectral-flux onset analysis."""

    detected: bool
    flux: float
    threshold: float
    energy: float


class SpectralFluxOnsetDetector:
    """
    Detect musical onsets using positive spectral flux.

    Spectral flux measures how much the frequency spectrum increases
    between consecutive audio blocks. A one-block look-ahead is used
    so only local spectral-flux peaks are emitted as onsets.
    """

    def __init__(
        self,
        block_size: int = 1024,
        sensitivity: float = 2.2,
        minimum_threshold: float = 0.003,
        history_size: int = 32,
        cooldown_blocks: int = 8,
        minimum_rms: float = 0.002,
    ) -> None:
        if block_size <= 0:
            raise ValueError("block_size must be greater than zero")

        if sensitivity <= 0:
            raise ValueError("sensitivity must be greater than zero")

        if history_size < 4:
            raise ValueError("history_size must be at least 4")

        if cooldown_blocks < 0:
            raise ValueError("cooldown_blocks cannot be negative")

        self.block_size = block_size
        self.sensitivity = sensitivity
        self.minimum_threshold = minimum_threshold
        self.cooldown_blocks = cooldown_blocks
        self.minimum_rms = minimum_rms

        self.window = np.hanning(block_size).astype(np.float32)

        self.previous_spectrum: np.ndarray | None = None

        self.flux_history: deque[float] = deque(
            maxlen=history_size,
        )

        self.cooldown = 0

        # Previous flux values are retained so an onset is emitted
        # only when the middle value is a local maximum.
        self.previous_flux: float | None = None
        self.previous_threshold: float = minimum_threshold
        self.previous_rms: float = 0.0

    def process(
        self,
        samples: np.ndarray,
    ) -> SpectralOnsetResult:
        """Analyze one audio block and detect spectral transients."""

        mono_samples = self._prepare_samples(samples)

        rms = float(
            np.sqrt(
                np.mean(
                    np.square(mono_samples),
                ),
            ),
        )

        windowed = mono_samples * self.window

        spectrum = np.abs(
            np.fft.rfft(windowed),
        ).astype(np.float32)

        spectrum_sum = float(np.sum(spectrum))

        if spectrum_sum > 0:
            spectrum /= spectrum_sum

        if self.previous_spectrum is None:
            self.previous_spectrum = spectrum

            return SpectralOnsetResult(
                detected=False,
                flux=0.0,
                threshold=self.minimum_threshold,
                energy=rms,
            )

        spectral_difference = spectrum - self.previous_spectrum

        positive_difference = np.maximum(
            spectral_difference,
            0.0,
        )

        flux = float(np.sum(positive_difference))
        threshold = self._calculate_threshold()

        detected = False

        if self.cooldown > 0:
            self.cooldown -= 1

        # Detect the previous block only when it is confirmed as a
        # local maximum relative to the current block.
        if (
            self.cooldown == 0
            and self.previous_flux is not None
            and self.previous_rms >= self.minimum_rms
            and self.previous_flux > self.previous_threshold
            and self.previous_flux >= flux
        ):
            detected = True
            self.cooldown = self.cooldown_blocks

        self.flux_history.append(flux)
        self.previous_spectrum = spectrum

        self.previous_flux = flux
        self.previous_threshold = threshold
        self.previous_rms = rms

        return SpectralOnsetResult(
            detected=detected,
            flux=flux,
            threshold=threshold,
            energy=rms,
        )

    def reset(self) -> None:
        """Reset detector history and internal state."""

        self.previous_spectrum = None
        self.flux_history.clear()
        self.cooldown = 0

        self.previous_flux = None
        self.previous_threshold = self.minimum_threshold
        self.previous_rms = 0.0

    def _calculate_threshold(self) -> float:
        """
        Calculate a robust adaptive threshold.

        Median and median absolute deviation are less affected by
        isolated peaks than a regular arithmetic mean.
        """

        if len(self.flux_history) < 4:
            return self.minimum_threshold

        history = np.asarray(
            self.flux_history,
            dtype=np.float32,
        )

        history_median = float(np.median(history))

        median_absolute_deviation = float(
            np.median(
                np.abs(history - history_median),
            ),
        )

        adaptive_threshold = (
            history_median
            + self.sensitivity
            * median_absolute_deviation
        )

        return max(
            self.minimum_threshold,
            adaptive_threshold,
        )

    def _prepare_samples(
        self,
        samples: np.ndarray,
    ) -> np.ndarray:
        """Convert the input block to a fixed-size mono array."""

        prepared = np.asarray(
            samples,
            dtype=np.float32,
        )

        if prepared.ndim == 2:
            prepared = np.mean(
                prepared,
                axis=1,
            )

        prepared = prepared.reshape(-1)

        if len(prepared) == self.block_size:
            return prepared

        if len(prepared) > self.block_size:
            return prepared[: self.block_size]

        padded = np.zeros(
            self.block_size,
            dtype=np.float32,
        )

        padded[: len(prepared)] = prepared

        return padded