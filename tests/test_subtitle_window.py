import pytest  # type: ignore[import-not-found]


@pytest.fixture
def subtitle_win(qtbot):
    from subtitle_window import SubtitleWindow

    win = SubtitleWindow()
    qtbot.addWidget(win)
    return win


def test_subtitle_window_is_frameless(subtitle_win):
    from PyQt5.QtCore import Qt  # type: ignore[import-not-found]

    assert subtitle_win.windowFlags() & Qt.FramelessWindowHint


def test_subtitle_window_stays_on_top(subtitle_win):
    from PyQt5.QtCore import Qt  # type: ignore[import-not-found]

    assert subtitle_win.windowFlags() & Qt.WindowStaysOnTopHint


def test_subtitle_window_has_two_labels(subtitle_win):
    assert subtitle_win.label_original is not None
    assert subtitle_win.label_translation is not None


def test_update_text_sets_labels(subtitle_win):
    subtitle_win.update_text("Hello world", "Xin chao the gioi", "en")
    assert subtitle_win._target_orig == "Hello world"
    assert subtitle_win._target_trans == "Xin chao the gioi"


def test_update_text_sets_lang_badge_en(subtitle_win):
    subtitle_win.update_text("Hello", "Xin chao", "en")
    assert "EN" in subtitle_win.lang_badge.text()


def test_update_text_sets_lang_badge_vi(subtitle_win):
    subtitle_win.update_text("Xin chao", "Hello", "vi")
    assert "VI" in subtitle_win.lang_badge.text()


def test_clear_clears_labels(subtitle_win, qtbot):
    subtitle_win.update_text("Hello", "Xin chao", "en")
    subtitle_win.clear()
    qtbot.wait(600)
    assert subtitle_win.label_original.text() == ""
    assert subtitle_win.label_translation.text() == ""
    assert subtitle_win.lang_badge.text() == ""


def test_set_status_mode_listening_shows_green_dot(subtitle_win):
    subtitle_win.set_status_mode("listening")
    assert subtitle_win._status_mode == "listening"
    assert subtitle_win._is_listening is True


def test_set_status_mode_error_shows_red_indicator(subtitle_win):
    subtitle_win.set_status_mode("error")
    assert subtitle_win._status_mode == "error"
    assert subtitle_win._is_listening is False


def test_set_status_mode_reconnecting_shows_amber_indicator(subtitle_win):
    subtitle_win.set_status_mode("reconnecting")
    assert subtitle_win._status_mode == "reconnecting"
    assert subtitle_win._is_listening is False


def test_typewriter_does_not_rewind_on_small_correction(subtitle_win, qtbot):
    subtitle_win._curr_orig_text = "Hello world this is"
    subtitle_win._target_orig = "Hello world this"

    qtbot.wait(60)

    assert subtitle_win._curr_orig_text.startswith("Hello world this")


def test_typewriter_does_rewind_on_large_correction(subtitle_win, qtbot):
    subtitle_win._curr_orig_text = "Hello world this is a very long sentence"
    subtitle_win._target_orig = "Hello"

    qtbot.wait(60)

    assert subtitle_win._curr_orig_text == "Hello"


def test_interim_text_reduces_label_opacity(subtitle_win):
    subtitle_win.update_text("Hello", "Xin chào", "en", is_final=False)
    orig_style = subtitle_win.label_original.styleSheet()
    trans_style = subtitle_win.label_translation.styleSheet()
    assert "rgba" in orig_style, "Original should use rgba for dimming"
    assert "rgba" in trans_style, "Translation should use rgba for dimming"


def test_final_text_restores_full_opacity(subtitle_win):
    subtitle_win.update_text("Hello", "Xin chào", "en", is_final=False)
    subtitle_win.update_text("Hello world", "Xin chào thế giới", "en", is_final=True)
    orig_style = subtitle_win.label_original.styleSheet()
    trans_style = subtitle_win.label_translation.styleSheet()
    assert "rgba(240,240,255,230)" in orig_style, "Original should have full alpha"
    assert "color: #FFD700" in trans_style, "Translation should be full gold"
