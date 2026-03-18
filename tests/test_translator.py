def test_detect_lang_english():
    from translator import detect_lang
    assert detect_lang("Hello world") == "en"


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
