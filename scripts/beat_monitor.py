import time

from app.audio.capture import AudioCapture
from app.bpm.onset import EnergyOnsetDetector


def main() -> None:
    capture = AudioCapture()
    detector = EnergyOnsetDetector()

    print()
    print("=" * 60)
    print("JG SYNC — HEARTBEAT")
    print("=" * 60)
    print()
    print("Listening for beats...")
    print("Press Ctrl+C to stop.")
    print()

    last_samples = None

    try:
        capture.start()

        while True:
            samples = capture.latest_samples

            if samples is not None and samples is not last_samples:
                result = detector.process(samples)

                last_samples = samples

                if result.detected:
                    print(
                        f"● BEAT | "
                        f"energy={result.energy:.5f} | "
                        f"delta={result.difference:.5f} | "
                        f"threshold={result.threshold:.5f}"
                    )

            time.sleep(0.005)

    except KeyboardInterrupt:
        print()
        print("Stopping JG Sync...")

    finally:
        capture.stop()
        print("Audio capture stopped.")


if __name__ == "__main__":
    main()