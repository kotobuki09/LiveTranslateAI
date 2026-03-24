import queue
import audioop  # type: ignore[import-not-found]  # NOTE: deprecated in Python 3.12, removed in 3.13 - migrate to audioop-lts when upgrading

try:
    import pyaudiowpatch as pyaudio  # type: ignore[import-not-found]
except ImportError:
    import pyaudio  # type: ignore[import-not-found]
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

    def __init__(self, error_callback=None, source_mode: str = "mic"):
        self.audio_queue: queue.Queue[bytes] = queue.Queue(
            maxsize=config.AUDIO_QUEUE_MAX_CHUNKS
        )
        self.is_running = False
        self._stream = None
        self._pa = None
        self._error_callback = error_callback
        self._source_mode = source_mode
        self._ratecv_state = None

    def _put_chunk(self, data: bytes) -> None:
        """Drop-oldest: discard head when full, then enqueue."""
        if self.audio_queue.full():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                pass
        self.audio_queue.put_nowait(data)

    def start(self):
        """Start capturing audio. Blocks until stop() is called."""
        if self._source_mode == "system":
            self._start_loopback()
        else:
            self._start_mic()

    def _start_mic(self):
        """Original mic capture code."""
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
                self._put_chunk(data)
        except Exception as e:
            logger.error(f"[AudioCapture] Fatal error: {e}")
            if self._error_callback:
                self._error_callback(str(e))
        finally:
            self._cleanup()

    def _start_loopback(self):
        """Capture system audio via WASAPI loopback and put resampled PCM into audio_queue."""
        # Guard: plain pyaudio does not support WASAPI loopback; pyaudiowpatch is required.
        # Check module name because pyaudiowpatch is imported as `pyaudio` via the alias shim.
        if pyaudio.__name__ != "pyaudiowpatch":
            logger.error(
                "[AudioCapture] pyaudiowpatch not installed; loopback unavailable."
            )
            if self._error_callback:
                self._error_callback(
                    "PyAudioWPatch is not installed. Run: pip install PyAudioWPatch"
                )
            return
        try:
            self._pa = pyaudio.PyAudio()
            try:
                loopback = self._pa.get_default_wasapi_loopback()
            except Exception as e:
                logger.error(f"[AudioCapture] No WASAPI loopback device: {e}")
                if self._error_callback:
                    self._error_callback(
                        "No system audio device found. Check your audio settings."
                    )
                return

            native_rate = int(loopback["defaultSampleRate"])
            native_channels = loopback["maxInputChannels"]
            frames = int(native_rate * config.CHUNK_MS / 1000)

            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=native_channels,
                rate=native_rate,
                input=True,
                input_device_index=loopback["index"],
                frames_per_buffer=frames,
            )
            self.is_running = True
            logger.info(
                f"[AudioCapture] Loopback started - device='{loopback['name']}', "
                f"native={native_rate}Hz/{native_channels}ch, resampling->16kHz mono"
            )
            while self.is_running:
                data = self._stream.read(frames, exception_on_overflow=False)
                if native_channels > 1:
                    data = audioop.tomono(data, 2, 0.5, 0.5)
                data, self._ratecv_state = audioop.ratecv(
                    data,
                    2,
                    1,
                    native_rate,
                    config.SAMPLE_RATE,
                    self._ratecv_state,
                )
                self._put_chunk(data)
        except Exception as e:
            logger.error(f"[AudioCapture] Loopback fatal error: {e}")
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
                    devices.append(
                        {"index": i, "name": info.get("name", f"Device {i}")}
                    )
            pa.terminate()
            return devices
        except Exception as e:
            logger.warning(f"[AudioCapture] Could not list devices: {e}")
            return []
