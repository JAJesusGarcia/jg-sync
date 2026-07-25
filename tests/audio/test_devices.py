from unittest.mock import patch

from app.audio.devices import (
    get_audio_devices,
    get_default_devices,
    get_input_devices,
    get_output_devices,
)


MOCK_DEVICES = [
    {
        "name": "Test Microphone",
        "hostapi": 0,
        "max_input_channels": 2,
        "max_output_channels": 0,
        "default_samplerate": 44100.0,
    },
    {
        "name": "Test Speakers",
        "hostapi": 1,
        "max_input_channels": 0,
        "max_output_channels": 2,
        "default_samplerate": 48000.0,
    },
]

MOCK_HOST_APIS = [
    {"name": "MME"},
    {"name": "Windows WASAPI"},
]


@patch("app.audio.devices.sd.query_hostapis")
@patch("app.audio.devices.sd.query_devices")
def test_get_audio_devices(
    mock_query_devices,
    mock_query_hostapis,
):
    mock_query_devices.return_value = MOCK_DEVICES
    mock_query_hostapis.return_value = MOCK_HOST_APIS

    devices = get_audio_devices()

    assert len(devices) == 2

    assert devices[0] == {
        "id": 0,
        "name": "Test Microphone",
        "host_api": "MME",
        "input_channels": 2,
        "output_channels": 0,
        "default_sample_rate": 44100.0,
    }

    assert devices[1]["name"] == "Test Speakers"
    assert devices[1]["host_api"] == "Windows WASAPI"
    assert devices[1]["output_channels"] == 2


@patch("app.audio.devices.sd.default.device", (0, 1))
def test_get_default_devices():
    input_device, output_device = get_default_devices()

    assert input_device == 0
    assert output_device == 1


@patch("app.audio.devices.sd.query_hostapis")
@patch("app.audio.devices.sd.query_devices")
def test_get_input_devices(
    mock_query_devices,
    mock_query_hostapis,
):
    mock_query_devices.return_value = MOCK_DEVICES
    mock_query_hostapis.return_value = MOCK_HOST_APIS

    input_devices = get_input_devices()

    assert len(input_devices) == 1
    assert input_devices[0]["name"] == "Test Microphone"


@patch("app.audio.devices.sd.query_hostapis")
@patch("app.audio.devices.sd.query_devices")
def test_get_output_devices(
    mock_query_devices,
    mock_query_hostapis,
):
    mock_query_devices.return_value = MOCK_DEVICES
    mock_query_hostapis.return_value = MOCK_HOST_APIS

    output_devices = get_output_devices()

    assert len(output_devices) == 1
    assert output_devices[0]["name"] == "Test Speakers"