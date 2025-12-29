import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALE_DIR = BASE_DIR / "locales"
DEFAULT_LOCALE = "ko"

# 지원되는 언어 목록
SUPPORTED_LOCALES = ["ko", "en", "ja", "zh", "es", "fr", "de", "pt", "vi", "th"]

# 언어 표시 이름
LOCALE_NAMES = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
    "zh": "中文",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "vi": "Tiếng Việt",
    "th": "ไทย",
}


class Translator:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_locale(self, locale: str) -> Dict[str, Any]:
        # 지원되지 않는 언어는 기본값으로 폴백
        if locale not in SUPPORTED_LOCALES:
            locale = DEFAULT_LOCALE

        if locale in self._cache:
            return self._cache[locale]

        file_path = LOCALE_DIR / f"{locale}.json"
        if not file_path.exists():
            file_path = LOCALE_DIR / f"{DEFAULT_LOCALE}.json"

        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        self._cache[locale] = data
        return data

    def translate(self, locale: str, key: str, default: str | None = None) -> str:
        data = self.load_locale(locale)
        keys = key.split(".")
        current: Any = data
        for part in keys:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default or key
        if isinstance(current, str):
            return current
        return default or key

    def get_supported_locales(self) -> List[Dict[str, str]]:
        """지원되는 언어 목록 반환"""
        return [
            {"code": code, "name": LOCALE_NAMES.get(code, code)}
            for code in SUPPORTED_LOCALES
        ]


translator = Translator()


def load_translations(locale: str | None = None) -> Dict[str, Any]:
    """Return all translations for the requested locale, falling back to default."""
    target_locale = locale or DEFAULT_LOCALE
    return translator.load_locale(target_locale)


def get_supported_locales() -> List[Dict[str, str]]:
    """지원되는 언어 목록 반환"""
    return translator.get_supported_locales()
