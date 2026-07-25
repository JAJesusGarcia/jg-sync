import time

from app.audio.capture import AudioCapture


BAR_WIDTH = 40


def create_meter(level: float) -> str:
    level = max(0.0, min(level, 1.0))

    filled = int(level * BAR_WIDTH)

    return "█" * filled + "░" * (BAR_WIDTH - filled)


def main() -> None:
    capture = AudioCapture()

    print()
    print("=" * 60)
    print("JG SYNC — AUDIO CAPTURE")
    print("=" * 60)
    print()
    print("Listening to default input device...")
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