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
