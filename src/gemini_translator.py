"""
GeminiTranslator — EN↔(VI/ZH/JA/KO/FR) translation using Gemini API.

Respects config.LANG_PAIR to determine the target language.
"""
from logger import get_logger

logger = get_logger(__name__)

import config

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None  # type: ignore

_LANG_DISPLAY_NAMES = {
    "en": "English",
    "vi": "Vietnamese",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "ko": "Korean",
    "fr": "French",
}


class GeminiTranslator:
    def __init__(self):
        if genai is None:
            raise ImportError("google-genai not installed.")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.TRANSLATE_MODEL

    def translate(self, text: str, source_lang: str) -> str:
        pair = config.SUPPORTED_LANG_PAIRS.get(config.LANG_PAIR,
                                                config.SUPPORTED_LANG_PAIRS["en-vi"])
        codes = pair["azure_translator_codes"]
        target_code = codes.get(source_lang, "vi")
        target_name = _LANG_DISPLAY_NAMES.get(target_code, target_code)

        prompt = (
            f"Translate the following text to {target_name}. "
            "Output only the translation with no extra commentary.\n\n"
            f"Text: {text}"
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"[GeminiTranslator] Error: {e}")
            return text


_instance = None


def get_gemini_translator() -> GeminiTranslator:
    global _instance
    if _instance is None:
        _instance = GeminiTranslator()
    return _instance
