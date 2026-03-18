"""
GeminiClient — real-time audio streaming via Gemini Live API (WebSocket).

Hybrid architecture for minimum latency:
  - Live API session: streams audio → input_audio_transcription (real-time)
  - Text translation: configured translator (~200ms)
  - on_failure callback when max retries exhausted

Improvements:
  - Removed duplicate _detect_lang — uses translator.detect_lang_for_pair()
  - on_failure callback
  - Exponential backoff capped at 8s
"""
from logger import get_logger

logger = get_logger(__name__)

import asyncio
import queue
import re
import threading
import time
import config
from translator import detect_lang_for_pair

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None   # type: ignore
    genai_types = None  # type: ignore

LIVE_SYSTEM_PROMPT = (
    "You are a silent listener in a classroom. "
    "Do not speak or respond. Just listen to the audio."
)


class GeminiClient:
    def __init__(self, audio_queue: queue.Queue):
        self.audio_queue = audio_queue
        self.result_queue: queue.Queue[dict] = queue.Queue()
        self.is_running = False
        self.on_failure = None  # type: ignore  # callable(str) | None
        self._thread: "threading.Thread | None" = None
        self._local_translator = None

    def start(self):
        self.is_running = True
        logger.info("[GeminiClient] Initializing in background thread…")
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False

    def _run_loop(self):
        # Eagerly load translator
        if config.TRANSLATE_ENGINE == "azure" and config.AZURE_TRANSLATOR_KEY:
            from azure_translator import get_azure_translator
            self._local_translator = get_azure_translator()
            logger.info("[GeminiClient] Using Azure Translator")
        elif config.TRANSLATE_ENGINE == "gemini" and config.GEMINI_API_KEY:
            from gemini_translator import get_gemini_translator
            self._local_translator = get_gemini_translator()
            logger.info("[GeminiClient] Using Gemini Translator")
        else:
            from azure_translator import get_azure_translator
            self._local_translator = get_azure_translator()
            logger.info("[GeminiClient] Using Azure Translator (default)")

        consecutive_errors = 0
        backoff = 1.0
        while self.is_running:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self._stream())
                loop.close()
                consecutive_errors = 0
                backoff = 1.0
                if self.is_running:
                    logger.info("[GeminiClient] Reconnecting…")
            except Exception as e:
                consecutive_errors += 1
                logger.warning(
                    f"[GeminiClient] Error ({consecutive_errors}/{config.MAX_RETRIES}): {e}"
                )
                if consecutive_errors >= config.MAX_RETRIES:
                    logger.error("[GeminiClient] Max retries reached. Stopping.")
                    if self.on_failure:
                        self.on_failure("Gemini STT stopped after too many errors.")
                    break
                time.sleep(min(backoff, 8.0))
                backoff *= 2
        self.is_running = False

    async def _stream(self):
        if genai is None:
            raise ImportError("google-genai not installed.")

        self._client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options={"api_version": config.API_VERSION},
        )

        live_config = genai_types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=genai_types.Content(
                parts=[genai_types.Part.from_text(text=LIVE_SYSTEM_PROMPT)]
            ),
            input_audio_transcription=genai_types.AudioTranscriptionConfig(),
            thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
            proactivity=genai_types.ProactivityConfig(proactive_audio=True),
            realtime_input_config=genai_types.RealtimeInputConfig(
                automatic_activity_detection=genai_types.AutomaticActivityDetection(
                    disabled=False,
                    start_of_speech_sensitivity=genai_types.StartSensitivity.START_SENSITIVITY_HIGH,
                    end_of_speech_sensitivity=genai_types.EndSensitivity.END_SENSITIVITY_LOW,
                    silence_duration_ms=100,
                ),
            ),
        )

        logger.info(f"[GeminiClient] Connecting to {config.MODEL}…")
        async with self._client.aio.live.connect(model=config.MODEL, config=live_config) as session:
            logger.info("[GeminiClient] Connected.")
            send_task = asyncio.create_task(self._send_audio(session))
            recv_task = asyncio.create_task(self._receive_responses(session))

            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                exc = task.exception()
                if exc:
                    raise exc
            logger.info("[GeminiClient] Session ended.")

    async def _send_audio(self, session):
        while self.is_running:
            try:
                chunk = self.audio_queue.get(timeout=0.05)
                await session.send_realtime_input(
                    audio=genai_types.Blob(data=chunk, mime_type="audio/pcm;rate=16000")
                )
            except queue.Empty:
                await asyncio.sleep(0.005)
            except Exception as e:
                logger.error(f"[GeminiClient] send_audio error: {e}")
                break
        logger.info("[GeminiClient] send_audio loop ended.")

    async def _receive_responses(self, session):
        self._pending_original = ""
        self._last_translation = ""
        translate_task: "asyncio.Task | None" = None

        async for response in session.receive():
            if not self.is_running:
                break
            try:
                sc = getattr(response, "server_content", None)
                if sc is None:
                    continue

                input_tx = getattr(sc, "input_transcription", None)
                if input_tx and getattr(input_tx, "text", None):
                    chunk_text = re.sub(r"<[^>]*>", "", input_tx.text)
                    if not chunk_text.strip():
                        continue
                    self._pending_original += chunk_text
                    current_text = self._pending_original.strip()
                    self.result_queue.put({
                        "original": current_text,
                        "translation": self._last_translation or "…",
                        "source_lang": detect_lang_for_pair(current_text, config.LANG_PAIR),
                        "is_final": False,
                    })
                    if translate_task and not translate_task.done():
                        translate_task.cancel()
                    if current_text:
                        translate_task = asyncio.create_task(
                            self._stream_translate(current_text, delay=1.0)
                        )

                if getattr(sc, "turn_complete", None) and self._pending_original.strip():
                    if translate_task and not translate_task.done():
                        translate_task.cancel()
                        try:
                            await translate_task
                        except (asyncio.CancelledError, Exception):
                            pass
                        translate_task = None
                    original = self._pending_original.strip()
                    await self._stream_translate(original, delay=0.0, is_final=True)
                    self._pending_original = ""
                    self._last_translation = ""

            except Exception as e:
                logger.error(f"[GeminiClient] receive error: {e}")

        logger.info("[GeminiClient] receive loop ended.")

    async def _stream_translate(self, text: str, delay: float = 0.0, is_final: bool = False):
        if delay > 0:
            await asyncio.sleep(delay)
        try:
            original = self._pending_original.strip() or text
            lang = detect_lang_for_pair(text, config.LANG_PAIR)
            translated = self._local_translator.translate(text, lang)
            self._last_translation = translated
            self.result_queue.put({
                "original": original,
                "translation": translated,
                "source_lang": lang,
                "is_final": is_final,
            })
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"[GeminiClient] translate error: {e!r}")
            if not self._last_translation:
                self._last_translation = "…"
