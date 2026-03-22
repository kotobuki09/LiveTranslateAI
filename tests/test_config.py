def test_config_has_required_audio_settings():
    import config

    assert config.SAMPLE_RATE == 16000
    assert config.CHUNK_MS == 100
    assert config.CHANNELS == 1


def test_config_has_required_gemini_settings():
    import config

    assert config.MODEL == "gemini-2.5-flash-native-audio-preview-12-2025"
    assert config.TRANSLATE_MODEL == "gemini-2.5-flash"
    assert config.API_VERSION == "v1alpha"
    assert config.MAX_RETRIES == 3


def test_config_has_stt_engine_settings():
    import config

    assert config.STT_ENGINE in ("azure", "gemini")


def test_config_has_required_ui_settings():
    import config

    assert config.WINDOW_OPACITY == 1.0
    assert config.COLOR_TRANS == "#FFD700"
    assert config.COLOR_ORIGINAL == "#FFFFFF"
    assert config.AUTO_CLEAR_SEC == 4


def test_chunk_size_is_calculated_correctly():
    import config

    # 16000 samples/sec * 100ms / 1000 * 2 bytes/sample = 3200 bytes
    assert config.CHUNK_SIZE == 3200


def test_config_has_audio_source_setting():
    import config

    assert config.AUDIO_SOURCE in ("mic", "system")


def test_new_config_flags_have_correct_defaults():
    import config

    assert hasattr(config, "METRICS_ENABLED")
    assert config.METRICS_ENABLED is False
    assert hasattr(config, "QUALITY_MODE")
    assert config.QUALITY_MODE in ("fast", "balanced", "accurate")
    assert hasattr(config, "AUDIO_QUEUE_MAX_CHUNKS")
    assert isinstance(config.AUDIO_QUEUE_MAX_CHUNKS, int)


def test_quality_mode_defaults_to_balanced(monkeypatch):
    import importlib
    import config as config_module
    import json_config

    with monkeypatch.context() as patch:
        patch.setattr(json_config, "load_settings", lambda: {})
        cfg = importlib.reload(config_module)
        assert cfg.QUALITY_MODE == "balanced"

    importlib.reload(config_module)


def test_quality_presets_have_correct_keys():
    import config

    preset = config.get_quality_preset()
    assert "interim_debounce_ms" in preset
    assert "interim_word_threshold" in preset
    assert "silence_ms" in preset
