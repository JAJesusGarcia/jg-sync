from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class BpmSample:
    elapsed_seconds: float
    bpm: float
    confidence: float
    state: str


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure JG Sync BPM accuracy using the JSON snapshots "
            "produced by scripts/engine_runtime.py."
        )
    )

    parser.add_argument(
        "--reference",
        type=float,
        required=True,
        help="Known reference tempo in BPM.",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Measurement duration in seconds. Default: 30.",
    )

    parser.add_argument(
        "--warmup",
        type=float,
        default=5.0,
        help=(
            "Seconds ignored at the beginning while the tracker "
            "calibrates. Default: 5."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("bpm_benchmark.csv"),
        help="CSV output path. Default: bpm_benchmark.csv.",
    )

    return parser.parse_args()


def is_valid_snapshot(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False

    return payload.get("type") == "snapshot"


def extract_sample(
    payload: dict[str, object],
    elapsed_seconds: float,
) -> BpmSample | None:
    bpm_value = payload.get("bpm")
    confidence_value = payload.get("confidence")
    state_value = payload.get("state")
    beat_detected = payload.get("beatDetected")

    # Only measure new accepted beat updates.
    #
    # The runtime publishes snapshots continuously, so collecting every
    # snapshot would count the same BPM value many times.
    if beat_detected is not True:
        return None

    if not isinstance(bpm_value, int | float):
        return None

    bpm = float(bpm_value)

    if bpm <= 0:
        return None

    confidence = (
        float(confidence_value)
        if isinstance(confidence_value, int | float)
        else 0.0
    )

    state = (
        str(state_value)
        if state_value is not None
        else "UNKNOWN"
    )

    return BpmSample(
        elapsed_seconds=elapsed_seconds,
        bpm=bpm,
        confidence=confidence,
        state=state,
    )


def save_csv(
    output_path: Path,
    samples: list[BpmSample],
    reference_bpm: float,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "elapsed_seconds",
                "bpm",
                "reference_bpm",
                "signed_error",
                "absolute_error",
                "confidence",
                "state",
            ]
        )

        for sample in samples:
            signed_error = sample.bpm - reference_bpm

            writer.writerow(
                [
                    f"{sample.elapsed_seconds:.3f}",
                    f"{sample.bpm:.3f}",
                    f"{reference_bpm:.3f}",
                    f"{signed_error:.3f}",
                    f"{abs(signed_error):.3f}",
                    f"{sample.confidence:.2f}",
                    sample.state,
                ]
            )


def print_report(
    samples: list[BpmSample],
    reference_bpm: float,
    total_detected_beats: int,
    ignored_warmup_beats: int,
) -> None:
    print()
    print("=" * 64)
    print("JG SYNC — BPM BENCHMARK REPORT")
    print("=" * 64)

    print(f"Reference BPM:          {reference_bpm:.3f}")
    print(f"Detected beat updates:  {total_detected_beats}")
    print(f"Ignored during warmup:  {ignored_warmup_beats}")
    print(f"Measured samples:       {len(samples)}")

    if not samples:
        print()
        print(
            "No valid BPM samples were collected after the warmup period."
        )
        print("=" * 64)
        return

    bpm_values = [
        sample.bpm
        for sample in samples
    ]

    signed_errors = [
        bpm - reference_bpm
        for bpm in bpm_values
    ]

    absolute_errors = [
        abs(error)
        for error in signed_errors
    ]

    mean_bpm = statistics.fmean(bpm_values)
    median_bpm = statistics.median(bpm_values)

    standard_deviation = (
        statistics.stdev(bpm_values)
        if len(bpm_values) >= 2
        else 0.0
    )

    mean_absolute_error = statistics.fmean(
        absolute_errors
    )

    bias = statistics.fmean(
        signed_errors
    )

    root_mean_squared_error = (
        statistics.fmean(
            error**2
            for error in signed_errors
        )
        ** 0.5
    )

    state_counts = Counter(
        sample.state
        for sample in samples
    )

    lock_count = state_counts.get(
        "LOCKED",
        0,
    )

    lock_percentage = (
        lock_count / len(samples) * 100.0
    )

    print()
    print("Tempo")
    print("-" * 64)
    print(f"Mean BPM:               {mean_bpm:.3f}")
    print(f"Median BPM:             {median_bpm:.3f}")
    print(f"Minimum BPM:            {min(bpm_values):.3f}")
    print(f"Maximum BPM:            {max(bpm_values):.3f}")
    print(f"Standard deviation:     {standard_deviation:.3f} BPM")

    print()
    print("Accuracy")
    print("-" * 64)
    print(f"Bias:                   {bias:+.3f} BPM")
    print(f"Mean absolute error:    {mean_absolute_error:.3f} BPM")
    print(f"Maximum absolute error: {max(absolute_errors):.3f} BPM")
    print(f"RMSE:                   {root_mean_squared_error:.3f} BPM")

    print()
    print("Tracking")
    print("-" * 64)
    print(f"LOCKED samples:         {lock_count}")
    print(f"LOCKED percentage:      {lock_percentage:.1f}%")

    for state, count in sorted(state_counts.items()):
        print(f"{state:<23}{count}")

    print()
    print("Interpretation")
    print("-" * 64)

    if abs(bias) >= 1.0 and standard_deviation < 1.0:
        print(
            "The result suggests a systematic timing bias: "
            "the measurements are relatively stable but shifted."
        )
    elif standard_deviation >= 1.0:
        print(
            "The result suggests timing jitter: "
            "the measured BPM varies significantly between beats."
        )
    else:
        print(
            "The detector appears stable and close to the reference tempo."
        )

    print("=" * 64)


def terminate_process(
    process: subprocess.Popen[str],
) -> None:
    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3.0)


def run_benchmark(
    reference_bpm: float,
    duration_seconds: float,
    warmup_seconds: float,
    output_path: Path,
) -> int:
    if reference_bpm <= 0:
        raise ValueError(
            "reference BPM must be greater than zero"
        )

    if duration_seconds <= 0:
        raise ValueError(
            "duration must be greater than zero"
        )

    if warmup_seconds < 0:
        raise ValueError(
            "warmup cannot be negative"
        )

    if warmup_seconds >= duration_seconds:
        raise ValueError(
            "warmup must be shorter than duration"
        )

    project_root = Path(__file__).resolve().parent.parent

    runtime_path = (
        project_root
        / "scripts"
        / "engine_runtime.py"
    )

    if not runtime_path.exists():
        raise FileNotFoundError(
            f"Runtime not found: {runtime_path}"
        )

    command = [
        sys.executable,
        str(runtime_path),
    ]

    print("JG SYNC — BPM BENCHMARK")
    print()
    print(f"Reference:   {reference_bpm:.3f} BPM")
    print(f"Duration:    {duration_seconds:.1f} seconds")
    print(f"Warmup:      {warmup_seconds:.1f} seconds")
    print(f"Output CSV:  {output_path}")
    print()
    print("Start the metronome now.")
    print("Press Ctrl+C to stop early.")
    print()

    process = subprocess.Popen(
        command,
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    if process.stdout is None:
        terminate_process(process)

        raise RuntimeError(
            "Could not read engine runtime output"
        )

    start_time = time.monotonic()
    samples: list[BpmSample] = []

    total_detected_beats = 0
    ignored_warmup_beats = 0

    try:
        while True:
            elapsed = time.monotonic() - start_time

            if elapsed >= duration_seconds:
                break

            line = process.stdout.readline()

            if line == "":
                if process.poll() is not None:
                    break

                continue

            clean_line = line.strip()

            if not clean_line.startswith("{"):
                continue

            try:
                payload = json.loads(clean_line)
            except json.JSONDecodeError:
                continue

            if not is_valid_snapshot(payload):
                continue

            if payload.get("beatDetected") is not True:
                continue

            total_detected_beats += 1

            sample = extract_sample(
                payload=payload,
                elapsed_seconds=elapsed,
            )

            if sample is None:
                continue

            if elapsed < warmup_seconds:
                ignored_warmup_beats += 1
                continue

            samples.append(sample)

            signed_error = (
                sample.bpm - reference_bpm
            )

            print(
                f"{elapsed:6.2f}s | "
                f"BPM {sample.bpm:7.3f} | "
                f"error {signed_error:+7.3f} | "
                f"confidence {sample.confidence:6.2f}% | "
                f"{sample.state}"
            )

    except KeyboardInterrupt:
        print()
        print("Measurement stopped by user.")

    finally:
        terminate_process(process)

    save_csv(
        output_path=output_path,
        samples=samples,
        reference_bpm=reference_bpm,
    )

    print_report(
        samples=samples,
        reference_bpm=reference_bpm,
        total_detected_beats=total_detected_beats,
        ignored_warmup_beats=ignored_warmup_beats,
    )

    print()
    print(f"CSV saved to: {output_path.resolve()}")

    return 0


def main() -> int:
    arguments = parse_arguments()

    try:
        return run_benchmark(
            reference_bpm=arguments.reference,
            duration_seconds=arguments.duration,
            warmup_seconds=arguments.warmup,
            output_path=arguments.output,
        )
    except (
        FileNotFoundError,
        RuntimeError,
        ValueError,
    ) as error:
        print(
            f"Benchmark error: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())