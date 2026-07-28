import time

from app.audio.capture import AudioCapture
from app.bpm.onset import EnergyOnsetDetector
# from app.bpm.tempo import TempoEstimator
from app.bpm.tracker import BeatTracker


def main() -> None:
    capture = AudioCapture()
    detector = EnergyOnsetDetector()
    # tempo = TempoEstimator()
    tracker = BeatTracker()

    print()
    print("=" * 68)
    print("JG SYNC — HEARTBEAT")
    print("=" * 68)
    print()
    print("Listening for beats and estimating tempo...")
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
                    timestamp = time.perf_counter()
                    # tempo_result = tempo.process_beat(timestamp)
                    tracking_result = tracker.process_onset(timestamp)

                    if tracking_result.bpm is None:
                        bpm_text = "calibrating..."
                    else:
                        bpm_text = f"{tracking_result.bpm:6.2f}"

                    confidence = tracking_result.confidence * 100

                    print(
                        f"● {tracking_result.state.value:<12}"
                        f" | BPM: {bpm_text}"
                        f" | Conf: {confidence:5.1f}%"
                        f" | {'ACCEPT' if tracking_result.accepted else 'REJECT'}"
                    )

                    # if tempo_result.bpm is None:
                    #     print(
                    #         "● BEAT | "
                    #         "BPM: calibrating..."
                    #     )
                    # else:
                    #     status = (
                    #         "ACCEPT"
                    #         if tempo_result.accepted
                    #         else "REJECT"
                    #     )

                    #     print(
                    #         f"● BEAT | "
                    #         f"BPM: {tempo_result.bpm:6.2f} | "
                    #         f"interval: {tempo_result.interval:.3f}s | "
                    #         f"samples: {tempo_result.samples} | "
                    #         f"{status}"
                    #     )

            time.sleep(0.005)

    except KeyboardInterrupt:
        print()
        print("Stopping JG Sync...")

    finally:
        capture.stop()
        print("Audio capture stopped.")


if __name__ == "__main__":
    main()