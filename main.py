"""
LiveTranslate — Real-time EN↔(VI/ZH/JA/KO/FR) speech translation subtitle overlay.

Entry point. Wires AudioCapture, STT engine, SubtitleWindow, and TrayManager together.

Improvements over original:
  - Internet connectivity check before starting
  - on_failure callback from engines → subtitle error display
  - Global hotkey Ctrl+Shift+L to toggle listening (requires `keyboard` package)
  - TrayManager.set_listening() + SubtitleWindow.set_listening() for visual state sync
  - AudioCapture error callback for mic failure handling
  - _toggle_listening() helper
  - MAX_HISTORY reads from config
"""
import sys
import os
import queue
import socket
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import config
from logger import setup_logger, get_logger

setup_logger(debug=config.DEBUG_MODE)
logger = get_logger("main")

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

from audio_capture import AudioCapture
from subtitle_window import SubtitleWindow
from tray import TrayManager
from gemini_client import GeminiClient
from azure_speech_client import AzureSpeechClient
from settings_window import SettingsWindow


class _Bridge(QObject):
    """Thread-safe signal bridge — lets background threads trigger Qt UI actions."""
    open_settings = pyqtSignal()
    show_subtitle = pyqtSignal()
    show_error    = pyqtSignal(str)


class App:
    def __init__(self):
        self._qt_app = QApplication(sys.argv)
        self._qt_app.setQuitOnLastWindowClosed(False)

        self._bridge = _Bridge()
        self._bridge.open_settings.connect(self._show_settings_on_main_thread)
        self._bridge.show_subtitle.connect(self._show_subtitle_on_main_thread)
        self._bridge.show_error.connect(self._show_error_on_main_thread)

        self._validate_api_key()

        self._audio = AudioCapture(error_callback=self._on_audio_error)
        self._settings_window = None
        self._engine = self._create_engine()
        self._subtitle = SubtitleWindow()
        self._tray = TrayManager(
            on_start=self._start_listening,
            on_stop=self._stop_listening,
            on_settings=self._open_settings,
            on_quit=self._quit,
            on_show_subtitle=self._open_show_subtitle,
            is_listening_fn=lambda: self._listening,
        )

        # Poll result_queue every 50ms on Qt main thread
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll_results)
        self._poll_timer.start(50)

        # Auto-clear after silence
        self._silence_timer = QTimer()
        self._silence_timer.setSingleShot(True)
        self._silence_timer.timeout.connect(self._on_silence)

        self._last_display_time = 0.0
        self._last_had_translation = False
        self._history: list = []
        self._listening = False

        self._register_hotkey()

    # ── Engine factory ────────────────────────────────────────────────

    def _create_engine(self):
        if config.STT_ENGINE == "gemini":
            engine = GeminiClient(audio_queue=self._audio.audio_queue)
            engine.on_reconnect = lambda msg: self._bridge.show_error.emit(msg)
            logger.info("Using GEMINI Live API STT")
        else:
            engine = AzureSpeechClient(audio_queue=self._audio.audio_queue)
            logger.info("Using AZURE Speech STT")
        engine.on_failure = lambda msg: self._bridge.show_error.emit(msg)
        return engine

    # ── Startup ───────────────────────────────────────────────────────

    def _validate_api_key(self):
        if config.STT_ENGINE == "azure" and not config.AZURE_SPEECH_KEY:
            msg = QMessageBox()
            msg.setWindowTitle("LiveTranslate — Missing Azure Speech Key")
            msg.setText(
                "AZURE_SPEECH_KEY is not set.\n\n"
                "Open Settings from the tray menu to enter your key.\n"
                "Get a key at: https://portal.azure.com → Azure AI services"
            )
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()
        elif config.STT_ENGINE == "gemini" and not config.GEMINI_API_KEY:
            msg = QMessageBox()
            msg.setWindowTitle("LiveTranslate — Missing Gemini API Key")
            msg.setText(
                "GEMINI_API_KEY is not set.\n\n"
                "Open Settings from the tray menu to enter your key.\n"
                "Get a free key at: https://aistudio.google.com/app/apikey"
            )
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()

    def _register_hotkey(self):
        """Register Ctrl+Shift+L as a global toggle hotkey (optional)."""
        try:
            import keyboard
            keyboard.add_hotkey("ctrl+shift+l", self._toggle_listening)
            logger.info("Global hotkey registered: Ctrl+Shift+L (toggle listening)")
        except ImportError:
            logger.info("'keyboard' package not installed — global hotkey skipped.")
        except Exception as e:
            logger.warning(f"Could not register global hotkey: {e}")

    # ── Internet check ────────────────────────────────────────────────

    def _check_internet(self) -> bool:
        """Check connectivity against the endpoint relevant to the active STT engine."""
        if config.STT_ENGINE == "gemini":
            host = "generativelanguage.googleapis.com"
        else:
            host = "api.cognitive.microsofttranslator.com"
        try:
            socket.setdefaulttimeout(3)
            socket.getaddrinfo(host, 443)
            return True
        except OSError:
            return False

    # ── App lifecycle ─────────────────────────────────────────────────

    def run(self):
        self._tray.start()
        self._subtitle.show()
        sys.exit(self._qt_app.exec_())

    def _toggle_listening(self):
        if self._listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        if self._listening:
            return

        if not self._check_internet():
            self._tray.notify("⚠  No internet connection — translation unavailable.")
            self._subtitle.show_error("No internet connection")
            return

        # Hot-swap engine if config changed
        if config.STT_ENGINE == "gemini" and not isinstance(self._engine, GeminiClient):
            self._engine = self._create_engine()
            logger.info("Switched to GEMINI STT")
        elif config.STT_ENGINE != "gemini" and not isinstance(self._engine, AzureSpeechClient):
            self._engine = self._create_engine()
            logger.info("Switched to AZURE STT")

        self._listening = True
        self._engine.start()
        threading.Thread(target=self._audio.start, daemon=True).start()

        self._tray.set_listening(True)
        self._subtitle.set_listening(True)
        self._tray.notify(
            f"🎙 Listening  — STT: {config.STT_ENGINE}  |  Trans: {config.TRANSLATE_ENGINE}  |  {config.LANG_PAIR.upper()}"
        )

    def _stop_listening(self):
        if not self._listening:
            return
        self._listening = False
        self._audio.stop()
        self._engine.stop()
        # Drain any stale audio chunks so they don't bleed into the next session
        while not self._audio.audio_queue.empty():
            try:
                self._audio.audio_queue.get_nowait()
            except Exception:
                break
        self._subtitle.clear()
        self._subtitle.set_listening(False)
        self._history.clear()
        self._tray.set_listening(False)
        self._tray.notify("⏹  Listening stopped.")

    def _open_settings(self):
        self._bridge.open_settings.emit()

    def _open_show_subtitle(self):
        self._bridge.show_subtitle.emit()

    def _show_settings_on_main_thread(self):
        if self._settings_window is None:
            self._settings_window = SettingsWindow()
            self._settings_window.accepted.connect(self._subtitle.refresh_styles)
            self._settings_window.finished.connect(
                lambda: setattr(self, "_settings_window", None)
            )
        self._settings_window.show()
        self._settings_window.raise_()
        self._settings_window.activateWindow()

    def _show_subtitle_on_main_thread(self):
        self._subtitle.show()
        self._subtitle.raise_()

    def _show_error_on_main_thread(self, message: str):
        self._subtitle.show_error(message)
        self._tray.notify(f"⚠  {message}")

    def _on_audio_error(self, message: str):
        """Called from audio thread on microphone failure."""
        self._bridge.show_error.emit(f"Microphone error: {message}")
        self._stop_listening()

    def _quit(self):
        self._stop_listening()
        self._qt_app.quit()

    # ── Result polling ────────────────────────────────────────────────

    def _on_silence(self):
        self._subtitle.clear()
        self._history.clear()

    def _poll_results(self):
        """Drain all pending results each 50ms cycle."""
        latest = None
        try:
            while True:
                latest = self._engine.result_queue.get_nowait()
        except queue.Empty:
            pass

        if latest is None:
            return

        original       = latest.get("original", "")
        translation    = latest.get("translation", "")
        source_lang    = latest.get("source_lang", "en")
        is_final       = latest.get("is_final", False)
        has_real_trans = translation and translation != "…"
        now            = time.monotonic()

        if self._last_had_translation:
            elapsed = now - self._last_display_time
            if elapsed < config.MIN_DISPLAY_SEC and not has_real_trans:
                return

        # Debounce interim results: don't refresh the UI faster than 300ms
        if not is_final and (now - self._last_display_time) < 0.3:
            return

        max_h = config.MAX_HISTORY

        if is_final:
            self._history.append((original, translation))
            if len(self._history) > max_h:
                self._history = self._history[-max_h:]
            display_orig  = "\n".join(h[0] for h in self._history)
            display_trans = "\n".join(h[1] for h in self._history)
        else:
            display_orig  = "\n".join([h[0] for h in self._history] + [original])
            display_trans = "\n".join([h[1] for h in self._history] + [translation])

        self._subtitle.update_text(display_orig, display_trans, source_lang)
        self._last_display_time = now
        self._last_had_translation = has_real_trans

        self._silence_timer.stop()
        self._silence_timer.start(config.AUTO_CLEAR_SEC * 1000)


if __name__ == "__main__":
    App().run()
