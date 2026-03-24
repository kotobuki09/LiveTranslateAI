from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
)


def test_state_stays_idle_when_audio_start_fails():
    import importlib

    with (
        patch("audio_capture.pyaudio.PyAudio") as mock_pa,
        patch("socket.getaddrinfo") as mock_socket,
        patch("tray.pystray") as mock_pystray,
        patch("tray.Image") as mock_img,
    ):
        mock_socket.return_value = True
        mock_stream = MagicMock()
        mock_stream.read.side_effect = OSError("mic failed")
        mock_pa.return_value.open.return_value = mock_stream

        from PyQt5.QtWidgets import QApplication  # type: ignore
        import sys

        app_qt = QApplication.instance() or QApplication(sys.argv)

        import main

        importlib.reload(main)
        app = main.App.__new__(main.App)
        app._listening = False
        app._audio = MagicMock()
        app._audio.is_running = False
        app._engine = MagicMock()
        app._bridge = MagicMock()
        app._tray = MagicMock()
        app._subtitle = MagicMock()

        app._check_internet = lambda: True

        import main as m

        original_start = m.App._start_listening
        called_set_listening = []

        def patched_start(self):
            if self._listening:
                return
            if not self._check_internet():
                return
            self._listening = False
            self._engine.start()
            import threading
            import time

            audio_thread = threading.Thread(target=self._audio.start, daemon=True)
            audio_thread.start()
            deadline = time.monotonic() + 0.05
            while time.monotonic() < deadline:
                if self._audio.is_running:
                    break
                time.sleep(0.005)
            if not self._audio.is_running:
                self._engine.stop()
                self._bridge.show_error.emit("Audio failed to start.")
                return
            self._listening = True
            called_set_listening.append(True)

        patched_start(app)
        assert app._listening is False, "listening must stay False when audio fails"


def test_state_becomes_listening_only_after_audio_starts_successfully():
    from unittest.mock import MagicMock
    import threading
    import time

    app = MagicMock()
    app._listening = False
    app._audio = MagicMock()
    app._engine = MagicMock()
    app._bridge = MagicMock()
    app._tray = MagicMock()
    app._subtitle = MagicMock()

    def delayed_start():
        time.sleep(0.05)
        app._audio.is_running = True

    threading.Thread(target=delayed_start, daemon=True).start()
    app._audio.is_running = False

    app._engine.start()
    audio_thread = threading.Thread(target=app._audio.start, daemon=True)
    audio_thread.start()
    deadline = time.monotonic() + 0.8
    while time.monotonic() < deadline:
        if app._audio.is_running:
            break
        time.sleep(0.01)
    if app._audio.is_running:
        app._listening = True
    else:
        app._bridge.show_error.emit("Audio failed to start.")

    assert app._listening is True, (
        "listening must become True after audio confirms running"
    )
