from __future__ import annotations

import time

from app.audio.capture import AudioCapture
from app.audio.devices import get_default_devices, get_input_devices


BAR_WIDTH = 40


def create_meter(level: float) -> str:
    """Create a terminal audio level meter."""

    level = max(0.0, min(level, 1.0))
    filled = int(level * BAR_WIDTH)

    return "█" * filled + "░" * (BAR_WIDTH - filled)


def select_input_device() -> int | None:
    """Let the user select an available audio input device."""

    devices = get_input_devices()
    default_input, _ = get_default_devices()

    print()
    print("=" * 72)
    print("JG SYNC — INPUT DEVICE")
    print("=" * 72)
    print()

    for device in devices:
        default_marker = (
            " [DEFAULT]"
            if device["id"] == default_input
            else ""
        )

        print(
            f"[{device['id']:02}] "
            f"{device['name']} "
            f"({device['host_api']})"
            f"{default_marker}"
        )

    print()
    print("Press ENTER to use the default input device.")

    while True:
        selection = input("\nInput device ID: ").strip()

        if selection == "":
            return default_input

        try:
            device_id = int(selection)
        except ValueError:
            print("Please enter a valid device ID.")
            continue

        valid_ids = {
            device["id"]
            for device in devices
        }

        if device_id not in valid_ids:
            print("That device is not a valid audio input.")
            continue

        return device_id


def main() -> None:
    device_id = select_input_device()

    capture = AudioCapture(
        device_id=device_id,
    )

    print()
    print("=" * 60)
    print("JG SYNC — AUDIO CAPTURE")
    print("=" * 60)
    print()
    print(f"Input device ID: {device_id}")
    print("Listening...")
    print("Press Ctrl+C to stop.")
    print()

    try:
        capture.start()

        while True:
            level = capture.current_level
            meter = create_meter(level.peak)

            print(
                f"\rINPUT [{meter}] "
                f"PEAK {level.peak:5.2f} | "
                f"{level.dbfs:6.1f} dBFS",
                end="",
                flush=True,
            )

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\nStopping JG Sync...")

    finally:
        capture.stop()
        print("Audio capture stopped.")


if __name__ == "__main__":
    main()