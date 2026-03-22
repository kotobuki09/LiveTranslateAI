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


def test_show_separator_config_default(subtitle_win):
    """SHOW_SEPARATOR config flag defaults to True."""
    import config

    assert hasattr(config, "SHOW_SEPARATOR")
    assert config.SHOW_SEPARATOR is True


def test_paintEvent_does_not_crash_with_separator_and_text(subtitle_win):
    """paintEvent runs without error when both labels have text and SHOW_SEPARATOR=True."""
    import config

    config.SHOW_SEPARATOR = True
    subtitle_win.label_original.setText("Hello")
    subtitle_win.label_translation.setText("Xin chào")
    subtitle_win.repaint()
    assert subtitle_win.label_original.text() == "Hello"


def test_translation_on_top_layout(qtbot):
    """When TRANSLATION_ON_TOP=True, translation label appears before original in layout."""
    import config

    original_flag = config.TRANSLATION_ON_TOP
    config.TRANSLATION_ON_TOP = True
    try:
        from subtitle_window import SubtitleWindow

        w = SubtitleWindow()
        qtbot.addWidget(w)
        layout = w.layout()
        orig_idx = layout.indexOf(w.label_original)
        trans_idx = layout.indexOf(w.label_translation)
        assert trans_idx < orig_idx, (
            "Translation should be before original when TRANSLATION_ON_TOP=True"
        )
    finally:
        config.TRANSLATION_ON_TOP = original_flag


def test_translation_on_bottom_by_default(qtbot):
    """Default layout: original on top, translation on bottom."""
    import config

    original_flag = config.TRANSLATION_ON_TOP
    config.TRANSLATION_ON_TOP = False
    try:
        from subtitle_window import SubtitleWindow

        w = SubtitleWindow()
        qtbot.addWidget(w)
        layout = w.layout()
        orig_idx = layout.indexOf(w.label_original)
        trans_idx = layout.indexOf(w.label_translation)
        assert orig_idx < trans_idx, "Original should be before translation by default"
    finally:
        config.TRANSLATION_ON_TOP = original_flag


def test_history_lines_rendered_dimmer_than_current(subtitle_win):
    import config

    config.HISTORY_DIM_OPACITY = 0.45
    multi_line_orig = "Previous sentence.\nCurrent sentence."
    multi_line_trans = "Câu trước.\nCâu hiện tại."
    subtitle_win._curr_orig_text = multi_line_orig
    subtitle_win._curr_trans_text = multi_line_trans
    subtitle_win._render_labels_with_history()
    orig_html = subtitle_win.label_original.text()
    assert "<span" in orig_html, "Rich text spans expected for history dimming"
    assert "rgba" in orig_html, "Dim color rgba expected in history span"


def test_single_line_no_span_overhead(subtitle_win):
    subtitle_win._curr_orig_text = "Hello"
    subtitle_win._curr_trans_text = "Xin chào"
    subtitle_win._render_labels_with_history()
    orig_text = subtitle_win.label_original.text()
    assert "<span" not in orig_text, "No span overhead for single-line text"


def test_html_special_chars_are_escaped(subtitle_win):
    subtitle_win._curr_orig_text = "A < B & C\nNormal line."
    subtitle_win._curr_trans_text = "Line 2."
    subtitle_win._render_labels_with_history()
    html = subtitle_win.label_original.text()
    assert "<span" in html
    assert "&lt;" in html, "< should be escaped as &lt; in HTML output"


def test_typewriter_snaps_to_word_boundary(subtitle_win):
    """After ticks, current text ends on a complete word, not mid-word."""
    import config

    config.TYPEWRITER_WORD_SNAP = True
    subtitle_win._target_orig = "Hello beautiful world"
    subtitle_win._curr_orig_text = ""
    for _ in range(5):
        subtitle_win._on_typewriter_tick()
    result = subtitle_win._curr_orig_text
    if result and result != "Hello beautiful world":
        words_typed = result.split()
        full_words = "Hello beautiful world".split()
        for i, w in enumerate(words_typed):
            assert w == full_words[i], f"Word {i} should be complete: got '{w}'"


def test_snap_to_word_boundary_static():
    """_snap_to_word_boundary helper returns complete-word prefix including trailing space."""
    from subtitle_window import SubtitleWindow

    # Step of 8 from "" on "Hello beautiful world" covers "Hello be" -> snap to "Hello "
    result = SubtitleWindow._snap_to_word_boundary("", "Hello beautiful world", 8)
    assert result == "Hello ", f"Expected 'Hello ', got '{result!r}'"


def test_typewriter_word_snap_disabled_allows_midword(subtitle_win):
    """When TYPEWRITER_WORD_SNAP=False, tick advances by raw characters without error."""
    import config

    config.TYPEWRITER_WORD_SNAP = False
    subtitle_win._target_orig = "Hello"
    subtitle_win._curr_orig_text = ""
    subtitle_win._on_typewriter_tick()
    assert isinstance(subtitle_win._curr_orig_text, str)
