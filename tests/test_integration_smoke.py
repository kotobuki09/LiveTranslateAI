"""
Integration smoke test.
Verifies all modules import and core logic works end-to-end.
Does NOT require a real microphone, API key, or display.
"""
import queue
import pytest


def test_all_modules_importable():
    import config
    import audio_capture
    import gemini_client
    import local_stt
    import translator
    import subtitle_window
    import tray
    assert True  # all imports succeeded


def test_gemini_client_detect_lang_roundtrip_en():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("Good morning class") == "en"


def test_gemini_client_detect_lang_roundtrip_vi():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("Xin chào") == "vi"


def test_gemini_client_detect_lang_empty_and_ascii():
    from gemini_client import GeminiClient
    assert GeminiClient._detect_lang("") == "en"
    assert GeminiClient._detect_lang("random text") == "en"
    assert GeminiClient._detect_lang("Đây là tiếng Việt") == "vi"


def test_subtitle_window_full_lifecycle(qtbot):
    from subtitle_window import SubtitleWindow
    win = SubtitleWindow()
    qtbot.addWidget(win)

    # English -> Vietnamese
    win.update_text("Good morning", "Chao buoi sang", "en")
    assert "Good morning" in win.label_original.text()
    assert "Chao buoi sang" in win.label_translation.text()
    assert "EN" in win.lang_badge.text()
    assert "VI" in win.lang_badge.text()

    # Vietnamese -> English
    win.update_text("Xin chao", "Hello", "vi")
    assert "VI" in win.lang_badge.text()
    assert "EN" in win.lang_badge.text()

    # Clear
    win.clear()
    assert win.label_original.text() == ""
    assert win.label_translation.text() == ""
    assert win.lang_badge.text() == ""
