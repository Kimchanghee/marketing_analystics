import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALE_DIR = BASE_DIR / "locales"
DEFAULT_LOCALE = "ko"


class Translator:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_locale(self, locale: str) -> Dict[str, Any]:
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


translator = Translator()


def load_translations(locale: str | None = None) -> Dict[str, Any]:
    """Return all translations for the requested locale, falling back to default."""
    target_locale = locale or DEFAULT_LOCALE
    return translator.load_locale(target_locale)
