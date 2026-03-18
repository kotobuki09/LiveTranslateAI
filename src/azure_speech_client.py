"""
AzureSpeechClient — Real-time speech-to-text + translation via Azure Cognitive Services.

Architecture:
  Mic → audio_queue → Azure Speech (PushAudioInputStream) → continuous recognition
       → recognizing (interim) / recognized (final) callbacks
       → result_queue → subtitle UI

Improvements over original:
  - Removed duplicate _detect_lang / VI_CHARS — uses translator.detect_lang_for_pair()
  - Replaced raw print() with logger
  - Eager fallback-translator loading in start() (not mid-speech)
  - Dynamic language pair from config.LANG_PAIR
  - on_failure callback when recognition is permanently canceled
"""
from logger import get_logger

logger = get_logger(__name__)

import queue
import threading
import config
from translator import detect_lang_for_pair

try:
    import azure.cognitiveservices.speech as speechsdk
except ImportError:
    speechsdk = None  # reported at start()


class AzureSpeechClient:
    """
    Drop-in replacement for GeminiClient using Azure Speech SDK.

    Interface contract (same as GeminiClient):
      - audio_queue: queue.Queue  — raw PCM bytes from AudioCapture
      - result_queue: queue.Queue — dicts {original, translation, source_lang}
      - start() / stop()
      - on_failure: callable(str) | None — called when engine gives up
    """

    def __init__(self, audio_queue: queue.Queue):
        self.audio_queue = audio_queue
        self.result_queue: queue.Queue[dict] = queue.Queue()
        self.is_running = False
        self.on_failure = None  # type: ignore  # set by App

        self._thread: "threading.Thread | None" = None
        self._current_interim = ""
        self._last_translation = ""
        self._lock = threading.Lock()
        self._translator = None

        self._push_stream = None
        self._recognizer = None
        self._stop_event = threading.Event()
        self._last_interim_word_count = 0

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self):
        if speechsdk is None:
            raise ImportError(
                "azure-cognitiveservices-speech is not installed.\n"
                "Run: pip install azure-cognitiveservices-speech"
            )
        self._stop_event.clear()
        self.is_running = True

        # Eagerly load fallback translator so first mid-session fallback is instant
        self._build_translator()
        self._build_recognizer()

        self._thread = threading.Thread(target=self._push_audio_loop, daemon=True)
        self._thread.start()

        logger.info(
            f"[AzureSpeech] Starting continuous recognition "
            f"(key=...{config.AZURE_SPEECH_KEY[-6:] if config.AZURE_SPEECH_KEY else 'MISSING'}, "
            f"region={config.AZURE_SPEECH_REGION}, pair={config.LANG_PAIR})"
        )
        self._recognizer.start_continuous_recognition_async()

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        if self._recognizer:
            try:
                self._recognizer.stop_continuous_recognition_async()
            except Exception:
                pass
        if self._push_stream:
            try:
                self._push_stream.close()
            except Exception:
                pass
        logger.info("[AzureSpeech] Stopped.")

    # ── Internal ────────────────────────────────────────────────────────────

    def _build_translator(self):
        """Pre-load fallback translator on start so mid-speech fallback is instant."""
        if config.TRANSLATE_ENGINE == "gemini" and config.GEMINI_API_KEY:
            from gemini_translator import get_gemini_translator
            self._translator = get_gemini_translator()
            logger.info("[AzureSpeech] Fallback translator: Gemini")
        else:
            from azure_translator import get_azure_translator
            self._translator = get_azure_translator()
            logger.info("[AzureSpeech] Fallback translator: Azure")

    def _build_recognizer(self):
        """Create SpeechTranslationConfig + PushAudioInputStream + TranslationRecognizer."""
        pair = config.SUPPORTED_LANG_PAIRS.get(config.LANG_PAIR,
                                                config.SUPPORTED_LANG_PAIRS["en-vi"])

        translation_config = speechsdk.translation.SpeechTranslationConfig(
            subscription=config.AZURE_SPEECH_KEY,
            region=config.AZURE_SPEECH_REGION,
        )
        auto_detect = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
            languages=pair["azure_speech_detect"]
        )
        for lang in pair["azure_speech_targets"]:
            translation_config.add_target_language(lang)

        translation_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
            "Continuous",
        )

        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000,
            bits_per_sample=16,
            channels=1,
        )
        self._push_stream = speechsdk.audio.PushAudioInputStream(stream_format=audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=self._push_stream)

        self._recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=translation_config,
            audio_config=audio_config,
            auto_detect_source_language_config=auto_detect,
        )

        self._recognizer.recognizing.connect(self._on_recognizing)
        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.canceled.connect(self._on_canceled)
        self._recognizer.session_started.connect(
            lambda evt: logger.info("[AzureSpeech] Session started.")
        )
        self._recognizer.session_stopped.connect(
            lambda evt: logger.info("[AzureSpeech] Session stopped.")
        )

    def _push_audio_loop(self):
        """Read PCM chunks from audio_queue and push into Azure stream."""
        logger.info("[AzureSpeech] Audio push loop started.")
        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=0.05)
                if self._push_stream:
                    self._push_stream.write(chunk)
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"[AzureSpeech] push_audio error: {e}")
                break
        logger.info("[AzureSpeech] Audio push loop ended.")

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _resolve_lang(self, result, text: str):
        """Return (source_lang, target_lang_azure) from an Azure recognition result."""
        try:
            auto_res = speechsdk.AutoDetectSourceLanguageResult(result)
            azure_lang = auto_res.language or ""
        except Exception:
            azure_lang = ""

        pair = config.SUPPORTED_LANG_PAIRS.get(config.LANG_PAIR,
                                                config.SUPPORTED_LANG_PAIRS["en-vi"])
        source_lang = detect_lang_for_pair(text, config.LANG_PAIR, azure_lang)

        # Azure Speech translation target is the opposite language in the pair
        if source_lang == pair["lang_a"]:
            target_lang = pair["azure_speech_targets"][0]
        else:
            target_lang = pair["azure_speech_targets"][1]

        return source_lang, target_lang

    def _on_recognizing(self, evt):
        """Interim (partial) recognition callback — throttled to every 3+ new words."""
        result = evt.result
        text = result.text.strip()
        if not text:
            return

        source_lang, target_lang = self._resolve_lang(result, text)
        translation = self._get_speech_translation(result, target_lang)

        with self._lock:
            self._current_interim = text
            if translation:
                self._last_translation = translation

        # Only push if we've spoken 3+ new words since the last interim push
        word_count = len(text.split())
        if word_count >= self._last_interim_word_count + 3 or not self._last_translation:
            self._last_interim_word_count = word_count
            self.result_queue.put({
                "original": text,
                "translation": self._last_translation or "…",
                "source_lang": source_lang,
                "is_final": False,
            })

    def _on_recognized(self, evt):
        """Final utterance callback."""
        result = evt.result
        if result.reason == speechsdk.ResultReason.TranslatedSpeech:
            text = result.text.strip()
            if not text:
                return

            source_lang, target_lang = self._resolve_lang(result, text)
            translation = self._get_speech_translation(result, target_lang)

            # Fallback translation
            if not translation and self._translator:
                try:
                    translation = self._translator.translate(text, source_lang)
                    logger.info(f"[AzureSpeech] Used fallback translator for: {text[:40]}")
                except Exception as e:
                    logger.error(f"[AzureSpeech] Fallback translation error: {e}")
                    translation = "…"

            with self._lock:
                self._current_interim = ""
                self._last_translation = translation or "…"
                self._last_interim_word_count = 0  # Reset on final utterance

            logger.info(f"[AzureSpeech] Final [{source_lang}]: {text[:60]} → {translation[:60] if translation else '?'}")
            self.result_queue.put({
                "original": text,
                "translation": translation or "…",
                "source_lang": source_lang,
                "is_final": True,
            })

        elif result.reason == speechsdk.ResultReason.NoMatch:
            pass  # Silence / unrecognizable audio

    def _on_canceled(self, evt):
        details = evt.cancellation_details
        logger.warning(f"[AzureSpeech] Recognition canceled: {details.reason}")
        if details.reason == speechsdk.CancellationReason.Error:
            logger.error(f"[AzureSpeech] Error details: {details.error_details}")
            if self.on_failure:
                self.on_failure(f"Azure Speech error: {details.error_details}")

    @staticmethod
    def _get_speech_translation(result, target_lang: str) -> str:
        """Extract built-in translation from Azure Speech result."""
        try:
            translations = result.translations
            if translations and target_lang in translations:
                return translations[target_lang].strip()
        except Exception:
            pass
        return ""
