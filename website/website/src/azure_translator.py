"""
AzureTranslator — EN↔(VI/ZH/JA/KO/FR) translation via Azure Translator API.

Supports all language pairs defined in config.SUPPORTED_LANG_PAIRS.
Retry logic with exponential backoff for transient network errors.
"""
import json
import urllib.request
import urllib.parse
import time

from logger import get_logger
import config

logger = get_logger(__name__)

_ENDPOINT = "https://api.cognitive.microsofttranslator.com"
_PATH = "/translate"
_API_VERSION = "3.0"


class AzureTranslator:
    """Translates between any configured language pair using Azure Translator API."""

    def __init__(self):
        self._api_key = config.AZURE_TRANSLATOR_KEY
        self._region = config.AZURE_TRANSLATOR_REGION

    def translate(self, text: str, source_lang: str, retries: int = 2) -> str:
        """Translate text with automatic retry on failure.

        source_lang: short code e.g. 'en', 'vi', 'zh', 'ja'
        target_lang is determined from the active LANG_PAIR in config.
        """
        pair = config.SUPPORTED_LANG_PAIRS.get(config.LANG_PAIR,
                                                config.SUPPORTED_LANG_PAIRS["en-vi"])
        codes = pair["azure_translator_codes"]
        target_lang = codes.get(source_lang)
        if not target_lang:
            # Fallback: pick whichever isn't the source
            all_codes = list(codes.keys())
            target_lang = all_codes[1] if source_lang == all_codes[0] else all_codes[0]

        last_exc = None
        for attempt in range(retries + 1):
            try:
                return self._do_translate(text, source_lang, target_lang)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    f"[AzureTranslator] Attempt {attempt + 1}/{retries + 1} failed: {exc}"
                )
                if attempt < retries:
                    time.sleep(0.4 * (attempt + 1))
        raise last_exc  # type: ignore

    def _do_translate(self, text: str, source_lang: str, target_lang: str) -> str:
        params = urllib.parse.urlencode({
            "api-version": _API_VERSION,
            "from": source_lang,
            "to": target_lang,
        })
        url = f"{_ENDPOINT}{_PATH}?{params}"
        body = json.dumps([{"text": text}]).encode("utf-8")
        headers: dict = {
            "Ocp-Apim-Subscription-Key": self._api_key,
            "Content-Type": "application/json",
        }
        if self._region and self._region.lower() != "global":
            headers["Ocp-Apim-Subscription-Region"] = self._region

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        return result[0]["translations"][0]["text"]


# Module-level singleton
_instance: "AzureTranslator | None" = None


def get_azure_translator() -> AzureTranslator:
    global _instance
    if _instance is None:
        _instance = AzureTranslator()
    return _instance
