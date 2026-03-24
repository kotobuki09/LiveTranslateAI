"""
translator.py — Shared language-detection utility used by all STT engines.

The old Translator class was unused (engines load translators directly),
so it has been removed. Only detect_lang() is kept here as the single
source of truth.
"""

import re

_VI_CHARS = set("àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừởữựỳýỷỹỵđ")

# Small set of common Italian words to help heuristic detection
_IT_WORDS = {
    "il",
    "lo",
    "la",
    "i",
    "gli",
    "le",
    "di",
    "da",
    "in",
    "su",
    "per",
    "tra",
    "fra",
    "un",
    "una",
    "uno",
    "che",
    "non",
    "si",
    "sono",
    "con",
    "ma",
    "come",
    "ciao",
    "grazie",
}

# Unicode character-set patterns for reliable CJK detection
# These are checked BEFORE the ascii_ratio fallback which has no empirical basis for CJK.
_ZH_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df]")
_JA_RE = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")
_KO_RE = re.compile(r"[\uac00-\ud7af\u1100-\u11ff]")


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

    pair = config.SUPPORTED_LANG_PAIRS.get(
        pair_key, config.SUPPORTED_LANG_PAIRS["en-vi"]
    )
    lang_map = pair["azure_speech_map"]  # e.g. {"en-US": "en", "vi-VN": "vi"}

    if azure_lang and azure_lang in lang_map:
        return lang_map[azure_lang]

    # Heuristic fallback
    if "vi" in lang_map.values():
        return detect_lang(text)

    # Non-vi pairs heuristic
    if len(text) == 0:
        return pair["lang_a"]

    # Unicode character-set checks (reliable for CJK scripts)
    if "zh" in lang_map.values() and _ZH_RE.search(text):
        return "zh"
    if "ja" in lang_map.values() and _JA_RE.search(text):
        return "ja"
    if "ko" in lang_map.values() and _KO_RE.search(text):
        return "ko"

    # Check for Italian keywords if 'it' is in the pair
    if "it" in lang_map.values():
        words = set(re.sub(r"[^\w\s]", "", text.lower()).split())
        if words & _IT_WORDS:
            return "it"

    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
    return pair["lang_a"] if ascii_ratio > 0.85 else pair["lang_b"]


def detect_lang_for_pair_with_confidence(
    text: str, pair_key: str, azure_lang: str = ""
) -> tuple[str, str]:
    """Returns (lang, confidence) where confidence ∈ 'high'|'medium'|'low'."""
    lang = detect_lang_for_pair(text, pair_key, azure_lang)
    if azure_lang:
        confidence = "high"
    elif len(text) < 8:
        confidence = "low"
    else:
        confidence = "medium"
    return lang, confidence
