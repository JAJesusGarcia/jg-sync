from unittest.mock import MagicMock, patch

import numpy as np

from app.audio.capture import AudioCapture


def test_initial_state():
    capture = AudioCapture()

    assert capture.stream is None
    assert capture.is_running is False
    assert capture.current_level.rms == 0.0
    assert capture.current_level.peak == 0.0
    assert capture.current_level.dbfs == -100.0


def test_audio_callback_calculates_signal_level():
    capture = AudioCapture()

    samples = np.array(
        [
            [0.0],
            [0.25],
            [-0.5],
            [0.75],
        ],
        dtype=np.float32,
    )

    capture._audio_callback(
        samples,
        frames=len(samples),
        time=None,
        status=None,
    )

    assert capture.current_level.rms > 0.0
    assert capture.current_level.peak == 0.75
    assert capture.current_level.dbfs > -100.0


def test_audio_callback_handles_silence():
    capture = AudioCapture()

    samples = np.zeros((1024, 1), dtype=np.float32)

    capture._audio_callback(
        samples,
        frames=len(samples),
        time=None,
        status=None,
    )

    assert capture.current_level.rms == 0.0
    assert capture.current_level.peak == 0.0
    assert capture.current_level.dbfs == -100.0


@patch("app.audio.capture.sd.InputStream")
def test_start_capture(mock_input_stream):
    stream = MagicMock()
    stream.active = True
    mock_input_stream.return_value = stream

    capture = AudioCapture(
        device_id=12,
        sample_rate=44100,
        block_size=1024,
        channels=1,
    )

    capture.start()

    mock_input_stream.assert_called_once()

    stream.start.assert_called_once()

    assert capture.stream is stream
    assert capture.is_running is True


@patch("app.audio.capture.sd.InputStream")
def test_stop_capture(mock_input_stream):
    stream = MagicMock()
    self.stream = None
    mock_input_stream.return_value = stream

    capture = AudioCapture()

    capture.start()
    capture.stop()

    stream.stop.assert_called_once()
    stream.close.assert_called_once()

    assert capture.stream is None
    assert capture.is_running is False