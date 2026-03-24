def test_detect_lang_ascii_is_english():
    from translator import detect_lang

    assert detect_lang("Good morning") == "en"


def test_detect_lang_english():
    from translator import detect_lang

    assert detect_lang("Hello world") == "en"


def test_detect_lang_vietnamese():
    from translator import detect_lang

    assert detect_lang("Xin chào buổi sáng") == "vi"


def test_detect_lang_empty():
    from translator import detect_lang

    assert detect_lang("") == "en"


def test_translator_module_has_detect_lang():
    from translator import detect_lang

    assert callable(detect_lang)


def test_detect_lang_for_pair_japanese():
    from translator import detect_lang_for_pair

    # Hiragana text should resolve to 'ja' in the en-ja pair
    assert detect_lang_for_pair("おはようございます", "en-ja") == "ja"


def test_detect_lang_for_pair_korean():
    from translator import detect_lang_for_pair

    # Hangul text should resolve to 'ko' in the en-ko pair
    assert detect_lang_for_pair("안녕하세요", "en-ko") == "ko"


def test_detect_lang_for_pair_chinese():
    from translator import detect_lang_for_pair

    # CJK text should resolve to 'zh' in the en-zh pair
    assert detect_lang_for_pair("你好世界", "en-zh") == "zh"


def test_detect_lang_for_pair_english_in_ja_pair():
    from translator import detect_lang_for_pair

    # ASCII text in en-ja pair should resolve to 'en'
    assert detect_lang_for_pair("Good morning", "en-ja") == "en"


def test_cjk_text_detected_correctly_for_en_zh_pair():
    from translator import detect_lang_for_pair

    assert detect_lang_for_pair("你好世界", "en-zh") == "zh"


def test_ambiguous_single_word_falls_back_to_azure_hint():
    from translator import detect_lang_for_pair

    # Azure hint "vi-VN" should win over heuristic on ambiguous "ok"
    assert detect_lang_for_pair("ok", "en-vi", azure_lang="vi-VN") == "vi"


def test_confidence_tier_is_returned_for_callers():
    from translator import detect_lang_for_pair_with_confidence

    lang, confidence = detect_lang_for_pair_with_confidence("Hello world", "en-vi")
    assert lang == "en"
    assert confidence in ("high", "medium", "low")
