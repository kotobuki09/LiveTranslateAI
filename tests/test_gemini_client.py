import queue
from unittest.mock import MagicMock


def test_gemini_client_creates_result_queue():
    from gemini_client import GeminiClient
    assert isinstance(GeminiClient(audio_queue=queue.Queue()).result_queue, queue.Queue)


def test_gemini_client_is_not_running_by_default():
    from gemini_client import GeminiClient
    assert GeminiClient(audio_queue=queue.Queue()).is_running is False


def test_detect_lang_english():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("Hello world") == "en"


def test_detect_lang_vietnamese():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("Xin chào buổi sáng") == "vi"


def test_detect_lang_empty_string():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("") == "en"


def test_detect_lang_vietnamese_diacritics():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("Đây là tiếng Việt") == "vi"


def test_stop_when_not_running_is_safe():
    from gemini_client import GeminiClient
    GeminiClient(queue.Queue()).stop()  # must not raise


def test_prompts_exist():
    from gemini_client import LIVE_SYSTEM_PROMPT
    assert "listen" in LIVE_SYSTEM_PROMPT.lower()
