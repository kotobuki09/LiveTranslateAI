import pytest


@pytest.fixture
def subtitle_win(qtbot):
    from subtitle_window import SubtitleWindow
    win = SubtitleWindow()
    qtbot.addWidget(win)
    return win


def test_subtitle_window_is_frameless(subtitle_win):
    from PyQt5.QtCore import Qt
    assert subtitle_win.windowFlags() & Qt.FramelessWindowHint


def test_subtitle_window_stays_on_top(subtitle_win):
    from PyQt5.QtCore import Qt
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
