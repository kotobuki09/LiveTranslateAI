"""
translator.py — Shared language-detection utility used by all STT engines.

The old Translator class was unused (engines load translators directly),
so it has been removed. Only detect_lang() is kept here as the single
source of truth.
"""

_VI_CHARS = set(
    "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừởữựỳýỷỹỵđ"
)


def detect_lang(text: str) -> str:
    """Heuristic: presence of Vietnamese diacritics → 'vi', else 'en'.

    For non-EN/VI language pairs, callers should rely on the Azure
    auto-detected language code instead of this fallback.
    """
    if any(c in _VI_CHARS for c in text.lower()):
        return "vi"
    return "en"


def detect_lang_for_pair(text: str, pair_key: str, azure_lang: str = "") -> str:
    """Detect which language in the active pair is being spoken.

    Prefers Azure's reported language; falls back to heuristics.
    """
    import config
    pair = config.SUPPORTED_LANG_PAIRS.get(pair_key, config.SUPPORTED_LANG_PAIRS["en-vi"])
    lang_map = pair["azure_speech_map"]  # e.g. {"en-US": "en", "vi-VN": "vi"}

    if azure_lang and azure_lang in lang_map:
        return lang_map[azure_lang]

    # Heuristic fallback
    if "vi" in lang_map.values():
        return detect_lang(text)

    # Non-vi pairs: if text is mostly ASCII → English, else other lang
    if len(text) == 0:
        return pair["lang_a"]
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
    return pair["lang_a"] if ascii_ratio > 0.85 else pair["lang_b"]
