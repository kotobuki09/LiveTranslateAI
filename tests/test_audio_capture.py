import queue
import threading
from unittest.mock import MagicMock, patch


def test_audio_capture_creates_queue():
    from audio_capture import AudioCapture

    cap = AudioCapture()
    assert isinstance(cap.audio_queue, queue.Queue)


def test_audio_capture_is_not_running_by_default():
    from audio_capture import AudioCapture

    assert AudioCapture().is_running is False


def test_audio_capture_stop_when_not_started_is_safe():
    from audio_capture import AudioCapture

    AudioCapture().stop()  # must not raise


@patch("audio_capture.pyaudio.PyAudio")
def test_audio_capture_start_sets_running(mock_pa):
    mock_stream = MagicMock()
    mock_stream.read.return_value = b"\x00" * 8000
    mock_pa.return_value.open.return_value = mock_stream
    from audio_capture import AudioCapture

    cap = AudioCapture()
    t = threading.Thread(target=cap.start, daemon=True)
    t.start()
    import time

    time.sleep(0.15)
    assert cap.is_running is True
    cap.stop()
    t.join(timeout=1)


@patch("audio_capture.pyaudio")
def test_audio_capture_loopback_start_sets_running(mock_pyaudio):
    import time
    from audio_capture import AudioCapture

    mock_stream = MagicMock()
    mock_stream.read.return_value = b"\x00" * 9600
    mock_pyaudio.__name__ = "pyaudiowpatch"  # Indicate pyaudiowpatch is available
    mock_pyaudio.PyAudio.return_value.get_default_wasapi_loopback.return_value = {
        "index": 0,
        "name": "Speakers [Loopback]",
        "defaultSampleRate": 48000.0,
        "maxInputChannels": 2,
    }
    mock_pyaudio.PyAudio.return_value.open.return_value = mock_stream

    cap = AudioCapture(source_mode="system")
    t = threading.Thread(target=cap.start, daemon=True)
    t.start()
    time.sleep(0.15)
    assert cap.is_running is True
    cap.stop()
    t.join(timeout=1)


@patch("audio_capture.pyaudio")
def test_audio_capture_loopback_resamples_stereo_to_mono(mock_pyaudio):
    import time
    from audio_capture import AudioCapture

    mock_stream = MagicMock()
    mock_stream.read.return_value = b"\x01\x02" * 4800
    mock_pyaudio.__name__ = "pyaudiowpatch"  # Indicate pyaudiowpatch is available
    mock_pyaudio.PyAudio.return_value.get_default_wasapi_loopback.return_value = {
        "index": 0,
        "name": "Speakers [Loopback]",
        "defaultSampleRate": 48000.0,
        "maxInputChannels": 2,
    }
    mock_pyaudio.PyAudio.return_value.open.return_value = mock_stream

    cap = AudioCapture(source_mode="system")
    t = threading.Thread(target=cap.start, daemon=True)
    t.start()
    time.sleep(0.15)
    cap.stop()
    t.join(timeout=1)
    assert not cap.audio_queue.empty()


@patch("audio_capture.pyaudio")
def test_audio_capture_loopback_preserves_ratecv_state(mock_pyaudio):
    import time
    from audio_capture import AudioCapture

    mock_stream = MagicMock()
    mock_stream.read.return_value = b"\x00" * 9600
    mock_pyaudio.__name__ = "pyaudiowpatch"  # Indicate pyaudiowpatch is available
    mock_pyaudio.PyAudio.return_value.get_default_wasapi_loopback.return_value = {
        "index": 0,
        "name": "Speakers [Loopback]",
        "defaultSampleRate": 48000.0,
        "maxInputChannels": 2,
    }
    mock_pyaudio.PyAudio.return_value.open.return_value = mock_stream

    cap = AudioCapture(source_mode="system")
    t = threading.Thread(target=cap.start, daemon=True)
    t.start()
    time.sleep(0.15)
    assert cap._ratecv_state is not None
    cap.stop()
    t.join(timeout=1)


@patch("audio_capture.pyaudio.PyAudio")
def test_audio_capture_loopback_no_device_calls_error_callback(mock_pa):
    from audio_capture import AudioCapture

    mock_pa.return_value.get_default_wasapi_loopback.side_effect = OSError(
        "No loopback device"
    )
    error_cb = MagicMock()

    cap = AudioCapture(source_mode="system", error_callback=error_cb)
    cap.start()

    error_cb.assert_called_once()
    assert (
        "system audio" in error_cb.call_args[0][0].lower()
        or "audio" in error_cb.call_args[0][0].lower()
    )


def test_audio_queue_drops_oldest_chunk_when_full():
    """Verify that when AUDIO_QUEUE_MAX_CHUNKS is reached, the oldest is discarded."""
    import config as _config

    orig = _config.AUDIO_QUEUE_MAX_CHUNKS
    _config.AUDIO_QUEUE_MAX_CHUNKS = 3
    from audio_capture import AudioCapture

    cap = AudioCapture()
    # Re-create queue with new maxsize since __init__ already ran
    import queue as _queue

    cap.audio_queue = _queue.Queue(maxsize=3)
    for i in range(5):
        cap._put_chunk(b"chunk%d" % i)
    chunks = []
    while not cap.audio_queue.empty():
        chunks.append(cap.audio_queue.get_nowait())
    _config.AUDIO_QUEUE_MAX_CHUNKS = orig
    assert len(chunks) == 3
    assert chunks[0] == b"chunk2"  # oldest two dropped
