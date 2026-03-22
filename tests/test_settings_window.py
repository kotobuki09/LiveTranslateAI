import pytest  # type: ignore[import-not-found]


@pytest.fixture
def settings_win(qtbot):
    from settings_window import SettingsWindow

    win = SettingsWindow()
    qtbot.addWidget(win)
    return win


def test_settings_window_has_audio_source_combo(settings_win):
    """Verify the STT tab contains an audio source selector widget."""
    assert settings_win._audio_source_combo is not None
    assert settings_win._audio_source_combo.count() == 2
    assert settings_win._audio_source_combo.itemData(0) == "mic"
    assert settings_win._audio_source_combo.itemData(1) == "system"


def test_quality_mode_combo_exists_in_display_tab(settings_win):
    assert hasattr(settings_win, "_quality_combo")
    assert settings_win._quality_combo.count() == 3


def test_quality_mode_combo_saves_to_config(settings_win, monkeypatch):
    import config
    import settings_window

    monkeypatch.setattr(settings_window, "save_settings", lambda *_: None)
    original_mode = config.QUALITY_MODE

    accurate_index = settings_win._quality_combo.findData("accurate")
    settings_win._quality_combo.setCurrentIndex(accurate_index)

    settings_win._save()

    assert settings_win._settings["QUALITY_MODE"] == "accurate"
    assert config.QUALITY_MODE == "accurate"
    config.QUALITY_MODE = original_mode
