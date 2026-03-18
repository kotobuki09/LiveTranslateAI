def test_config_has_required_audio_settings():
    import config
    assert config.SAMPLE_RATE == 16000
    assert config.CHUNK_MS == 250
    assert config.CHANNELS == 1


def test_config_has_required_gemini_settings():
    import config
    assert config.MODEL == "gemini-2.5-flash-native-audio-preview-12-2025"
    assert config.TRANSLATE_MODEL == "gemini-2.5-flash"
    assert config.API_VERSION == "v1alpha"
    assert config.MAX_RETRIES == 3


def test_config_has_stt_engine_settings():
    import config
    assert config.STT_ENGINE in ("local", "gemini")
    assert config.WHISPER_MODEL in ("tiny", "base", "small", "medium", "large-v3")
    assert isinstance(config.WHISPER_LANG, str)


def test_config_has_required_ui_settings():
    import config
    assert config.WINDOW_OPACITY == 0.85
    assert config.COLOR_TRANS == "#FFD700"
    assert config.COLOR_ORIGINAL == "#FFFFFF"
    assert config.AUTO_CLEAR_SEC == 8


def test_chunk_size_is_calculated_correctly():
    import config
    # 16000 samples/sec * 250ms / 1000 * 2 bytes/sample = 8000 bytes
    assert config.CHUNK_SIZE == 8000
