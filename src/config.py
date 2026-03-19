import os

os.environ.pop("GOOGLE_API_KEY", None)

from dotenv import load_dotenv
load_dotenv()

# ── Audio ───────────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
CHUNK_MS    = 100          # 100ms chunks → ~150ms lower first-word latency vs 250ms
CHANNELS    = 1
CHUNK_SIZE  = int(SAMPLE_RATE * CHUNK_MS / 1000) * 2  # bytes (16-bit = 2 bytes/sample)

# ── Gemini ──────────────────────────────────────────────────────────────
MODEL           = "gemini-2.5-flash-native-audio-preview-12-2025"
TRANSLATE_MODEL = "gemini-2.5-flash"
API_VERSION     = "v1alpha"
MAX_RETRIES     = 3

# ── Load persisted user settings ────────────────────────────────────────
from json_config import load_settings
_user_conf = load_settings()

# ── Default Fallback Credentials (lightly obfuscated) ───────────────────
def _d(s: str) -> str:
    return s[::-1]

_DG = _d("4M_9jxpU_Dzvf_AGrgZa7GEq_Qmx2gcIBySazIA")
_DAS = _d("VvdYGOCAYAAA3w3JXyLBBqCACC99JQQJtDTJ6CQMbvdd68uVc3HHr1sRVeFg8BcYLmxWppkVM7fgwgLbaUd9")
_DAT = _d("W0XfGOCAbAAA3w3JXpCyLUCACC99JQQJeSdcv5PfkO3AaCya7lLCn9NnTcwts79chNYXOXgWeeeedRJAQOh4")


# ── STT Engine ──────────────────────────────────────────────────────────
STT_ENGINE = _user_conf.get("STT_ENGINE", os.getenv("STT_ENGINE", "azure"))
if STT_ENGINE not in ["azure", "gemini"]:
    STT_ENGINE = "azure"

# ── Azure Speech ────────────────────────────────────────────────────────
AZURE_SPEECH_KEY    = _user_conf.get("AZURE_SPEECH_KEY",    os.getenv("AZURE_SPEECH_KEY",    _DAS))
AZURE_SPEECH_REGION = _user_conf.get("AZURE_SPEECH_REGION", os.getenv("AZURE_SPEECH_REGION", "southeastasia"))

# ── Azure Translator ────────────────────────────────────────────────────
AZURE_TRANSLATOR_KEY    = _user_conf.get("AZURE_TRANSLATOR_KEY",    os.getenv("AZURE_TRANSLATOR_KEY",    _DAT))
AZURE_TRANSLATOR_REGION = _user_conf.get("AZURE_TRANSLATOR_REGION", os.getenv("AZURE_TRANSLATOR_REGION", "global"))

# ── Gemini API Key ──────────────────────────────────────────────────────
GEMINI_API_KEY = _user_conf.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", _DG))

# ── Translation Engine ──────────────────────────────────────────────────
TRANSLATE_ENGINE = _user_conf.get("TRANSLATE_ENGINE", os.getenv("TRANSLATE_ENGINE", "azure"))
if TRANSLATE_ENGINE not in ["azure", "gemini"]:
    TRANSLATE_ENGINE = "azure"

# ── Language Pairs ──────────────────────────────────────────────────────
# Each pair defines: Azure Speech detection locales, Azure Speech translation
# targets, Azure Translator API codes, and display metadata.
SUPPORTED_LANG_PAIRS: dict = {
    "en-vi": {
        "azure_speech_detect": ["en-US", "vi-VN"],
        "azure_speech_targets": ["vi", "en"],
        "azure_translator_codes": {"en": "vi", "vi": "en"},  # source → target
        "azure_speech_map": {"en-US": "en", "vi-VN": "vi"},
        "lang_a": "en", "lang_b": "vi",
        "display": "EN ↔ VI",
        "badge": {"en": "🎙 EN → VI", "vi": "🎙 VI → EN"},
    },
    "en-zh": {
        "azure_speech_detect": ["en-US", "zh-CN"],
        "azure_speech_targets": ["zh-Hans", "en"],
        "azure_translator_codes": {"en": "zh-Hans", "zh": "en"},
        "azure_speech_map": {"en-US": "en", "zh-CN": "zh"},
        "lang_a": "en", "lang_b": "zh",
        "display": "EN ↔ ZH",
        "badge": {"en": "🎙 EN → ZH", "zh": "🎙 ZH → EN"},
    },
    "en-ja": {
        "azure_speech_detect": ["en-US", "ja-JP"],
        "azure_speech_targets": ["ja", "en"],
        "azure_translator_codes": {"en": "ja", "ja": "en"},
        "azure_speech_map": {"en-US": "en", "ja-JP": "ja"},
        "lang_a": "en", "lang_b": "ja",
        "display": "EN ↔ JA",
        "badge": {"en": "🎙 EN → JA", "ja": "🎙 JA → EN"},
    },
    "en-ko": {
        "azure_speech_detect": ["en-US", "ko-KR"],
        "azure_speech_targets": ["ko", "en"],
        "azure_translator_codes": {"en": "ko", "ko": "en"},
        "azure_speech_map": {"en-US": "en", "ko-KR": "ko"},
        "lang_a": "en", "lang_b": "ko",
        "display": "EN ↔ KO",
        "badge": {"en": "🎙 EN → KO", "ko": "🎙 KO → EN"},
    },
    "en-fr": {
        "azure_speech_detect": ["en-US", "fr-FR"],
        "azure_speech_targets": ["fr", "en"],
        "azure_translator_codes": {"en": "fr", "fr": "en"},
        "azure_speech_map": {"en-US": "en", "fr-FR": "fr"},
        "lang_a": "en", "lang_b": "fr",
        "display": "EN ↔ FR",
        "badge": {"en": "🎙 EN → FR", "fr": "🎙 FR → EN"},
    },
    "en-it": {
        "azure_speech_detect": ["en-US", "it-IT"],
        "azure_speech_targets": ["it", "en"],
        "azure_translator_codes": {"en": "it", "it": "en"},
        "azure_speech_map": {"en-US": "en", "it-IT": "it"},
        "lang_a": "en", "lang_b": "it",
        "display": "EN ↔ IT",
        "badge": {"en": "🎙 EN → IT", "it": "🎙 IT → EN"},
    },
}

LANG_PAIR = _user_conf.get("LANG_PAIR", os.getenv("LANG_PAIR", "en-vi"))
if LANG_PAIR not in SUPPORTED_LANG_PAIRS:
    LANG_PAIR = "en-vi"

# ── Audio Device ────────────────────────────────────────────────────────
AUDIO_DEVICE_INDEX = int(_user_conf.get("AUDIO_DEVICE_INDEX", -1))  # -1 = system default

# ── UI ──────────────────────────────────────────────────────────────────
WINDOW_OPACITY     = float(_user_conf.get("WINDOW_OPACITY", 1.0))
FONT_SIZE_ORIGINAL = int(_user_conf.get("FONT_SIZE_ORIGINAL", 16))
FONT_SIZE_TRANS    = int(_user_conf.get("FONT_SIZE_TRANS", 22))
FONT_ORIGINAL      = ("Segoe UI", FONT_SIZE_ORIGINAL)
FONT_TRANS         = ("Segoe UI", FONT_SIZE_TRANS, "bold")
COLOR_ORIGINAL     = "#FFFFFF"
COLOR_TRANS        = "#FFD700"
AUTO_CLEAR_SEC     = int(_user_conf.get("AUTO_CLEAR_SEC", 4))
MIN_DISPLAY_SEC    = 2
WINDOW_WIDTH_RATIO = 0.75
MAX_HISTORY        = int(_user_conf.get("MAX_HISTORY", 1))

# ── Debug ───────────────────────────────────────────────────────────────
DEBUG_MODE = bool(_user_conf.get("DEBUG_MODE", os.getenv("DEBUG", "false").lower() == "true"))
