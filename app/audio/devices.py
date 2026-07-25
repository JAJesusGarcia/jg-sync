from __future__ import annotations

import sounddevice as sd


def get_audio_devices() -> list[dict]:
    """
    Return all audio devices detected by PortAudio.

    Each device is normalized into a simple dictionary so the
    rest of JG Sync does not depend directly on SoundDevice's
    internal representation.
    """

    devices = sd.query_devices()
    host_apis = sd.query_hostapis()

    normalized_devices: list[dict] = []

    for index, device in enumerate(devices):
        host_api_index = device["hostapi"]
        host_api_name = host_apis[host_api_index]["name"]

        normalized_devices.append(
            {
                "id": index,
                "name": device["name"],
                "host_api": host_api_name,
                "input_channels": device["max_input_channels"],
                "output_channels": device["max_output_channels"],
                "default_sample_rate": device["default_samplerate"],
            }
        )

    return normalized_devices


def get_default_devices() -> tuple[int | None, int | None]:
    """
    Return the default input and output device IDs.

    Returns:
        tuple:
            (input_device_id, output_device_id)
    """

    default_input, default_output = sd.default.device

    input_id = None if default_input < 0 else int(default_input)
    output_id = None if default_output < 0 else int(default_output)

    return input_id, output_id


def get_input_devices() -> list[dict]:
    """Return devices capable of receiving audio."""

    return [
        device
        for device in get_audio_devices()
        if device["input_channels"] > 0
    ]


def get_output_devices() -> list[dict]:
    """Return devices capable of playing audio."""

    return [
        device
        for device in get_audio_devices()
        if device["output_channels"] > 0
    ]


def print_audio_devices() -> None:
    """Print a readable list of available audio devices."""

    devices = get_audio_devices()
    default_input, default_output = get_default_devices()

    print()
    print("=" * 72)
    print("JG SYNC — AUDIO DEVICES")
    print("=" * 72)

    for device in devices:
        markers: list[str] = []

        if device["id"] == default_input:
            markers.append("DEFAULT INPUT")

        if device["id"] == default_output:
            markers.append("DEFAULT OUTPUT")

        marker_text = (
            f" [{' | '.join(markers)}]"
            if markers
            else ""
        )

        print()
        print(
            f"[{device['id']:02}] "
            f"{device['name']}"
            f"{marker_text}"
        )

        print(
            f"     API: {device['host_api']} | "
            f"IN: {device['input_channels']} | "
            f"OUT: {device['output_channels']} | "
            f"SR: {device['default_sample_rate']:.0f} Hz"
        )

    print()
    print("=" * 72)


if __name__ == "__main__":
    print_audio_devices()