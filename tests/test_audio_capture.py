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
