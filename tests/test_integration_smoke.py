"""
Integration smoke test.
Verifies all modules import and core logic works end-to-end.
Does NOT require a real microphone, API key, or display.
"""

import queue
import pytest  # type: ignore[import-not-found]


def test_all_modules_importable():
    import config
    import audio_capture
    import gemini_client
    import metrics
    import translator
    import subtitle_window
    import tray

    assert True  # all imports succeeded


# detect_lang tests removed (tested in test_translator.py)


def test_metrics_module_importable():
    from metrics import PipelineMetrics

    m = PipelineMetrics()
    m.mark("audio_chunk")
    m.observe_latency_ms("poll_to_render", 45.3)
    m.inc_error("translation")
    assert m.error_count("translation") == 1


def test_subtitle_window_full_lifecycle(qtbot):
    from subtitle_window import SubtitleWindow

    win = SubtitleWindow()
    qtbot.addWidget(win)

    # English -> Vietnamese
    win.update_text("Good morning", "Chao buoi sang", "en")
    assert win._target_orig == "Good morning"
    assert win._target_trans == "Chao buoi sang"
    assert "EN" in win.lang_badge.text()

    # Vietnamese -> English
    win.update_text("Xin chao", "Hello", "vi")
    assert "VI" in win.lang_badge.text()

    # Clear
    win.clear()
    qtbot.wait(500)
    assert win.label_original.text() == ""
    assert win.label_translation.text() == ""
    assert win.lang_badge.text() == ""
