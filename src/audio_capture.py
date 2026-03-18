import queue
import pyaudio
import config
from logger import get_logger

logger = get_logger(__name__)


class AudioCapture:
    """Captures microphone audio and puts raw PCM chunks into audio_queue.

    Improvements:
      - Optional error_callback for microphone failures
      - Configurable input device (AUDIO_DEVICE_INDEX in config)
      - Graceful cleanup on error
      - list_input_devices() static helper for Settings UI
    """

    def __init__(self, error_callback=None):
        self.audio_queue: queue.Queue[bytes] = queue.Queue()
        self.is_running = False
        self._stream = None
        self._pa = None
        self._error_callback = error_callback

    def start(self):
        """Start capturing audio. Blocks until stop() is called."""
        try:
            self._pa = pyaudio.PyAudio()
            device_index = (
                config.AUDIO_DEVICE_INDEX if config.AUDIO_DEVICE_INDEX >= 0 else None
            )
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=config.CHANNELS,
                rate=config.SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=int(config.CHUNK_SIZE / 2),
            )
            self.is_running = True
            logger.info(
                f"[AudioCapture] Started — device={'default' if device_index is None else device_index}, "
                f"chunk={config.CHUNK_MS}ms"
            )
            while self.is_running:
                data = self._stream.read(
                    int(config.CHUNK_SIZE / 2),
                    exception_on_overflow=False,
                )
                self.audio_queue.put(data)
        except Exception as e:
            logger.error(f"[AudioCapture] Fatal error: {e}")
            if self._error_callback:
                self._error_callback(str(e))
        finally:
            self._cleanup()

    def stop(self):
        """Signal capture to stop."""
        self.is_running = False

    def _cleanup(self):
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None
        logger.info("[AudioCapture] Stopped.")

    @staticmethod
    def list_input_devices() -> list:
        """Return a list of available audio input devices for the Settings UI."""
        try:
            pa = pyaudio.PyAudio()
            devices = []
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get("maxInputChannels", 0) > 0:
                    devices.append({"index": i, "name": info.get("name", f"Device {i}")})
            pa.terminate()
            return devices
        except Exception as e:
            logger.warning(f"[AudioCapture] Could not list devices: {e}")
            return []
