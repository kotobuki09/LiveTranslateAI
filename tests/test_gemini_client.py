import queue
from unittest.mock import MagicMock


def test_gemini_client_creates_result_queue():
    from gemini_client import GeminiClient
    assert isinstance(GeminiClient(audio_queue=queue.Queue()).result_queue, queue.Queue)


def test_gemini_client_is_not_running_by_default():
    from gemini_client import GeminiClient
    assert GeminiClient(audio_queue=queue.Queue()).is_running is False


def test_prompts_exist():
    from gemini_client import LIVE_SYSTEM_PROMPT
    assert "listen" in LIVE_SYSTEM_PROMPT.lower()
