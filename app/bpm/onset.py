from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np


@dataclass
class OnsetResult:
    detected: bool
    energy: float
    difference: float
    threshold: float


class EnergyOnsetDetector:
    """
    Adaptive energy-based onset detector.

    The detector compares the current energy increase against
    the recent average energy variation instead of relying only
    on a fixed threshold.
    """

    def __init__(
        self,
        sensitivity: float = 2.5,
        minimum_threshold: float = 0.003,
        cooldown_blocks: int = 5,
        history_size: int = 24,
    ) -> None:
        self.sensitivity = sensitivity
        self.minimum_threshold = minimum_threshold
        self.cooldown_blocks = cooldown_blocks

        self.previous_energy = 0.0
        self.cooldown = 0

        self.difference_history: deque[float] = deque(
            maxlen=history_size,
        )

    def process(self, samples: np.ndarray) -> OnsetResult:
        """Analyze one block of audio and detect sudden energy increases."""

        samples = np.asarray(samples, dtype=np.float32)

        energy = float(np.mean(np.square(samples)))
        difference = max(
            0.0,
            energy - self.previous_energy,
        )

        if self.difference_history:
            average_difference = float(
                np.mean(self.difference_history)
            )
        else:
            average_difference = 0.0

        adaptive_threshold = max(
            self.minimum_threshold,
            average_difference * self.sensitivity,
        )

        detected = False

        if self.cooldown > 0:
            self.cooldown -= 1

        elif difference > adaptive_threshold:
            detected = True
            self.cooldown = self.cooldown_blocks

        self.difference_history.append(difference)
        self.previous_energy = energy

        return OnsetResult(
            detected=detected,
            energy=energy,
            difference=difference,
            threshold=adaptive_threshold,
        )