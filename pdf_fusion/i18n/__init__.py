"""Translations for the user interface.

The texts live in JSON files in ``locales/``, one file per language code.
``t(key)`` returns the text for the active language and falls back to English.
"""

import ctypes
import json
import locale
from pathlib import Path

DEFAULT_LANGUAGE = "en"
LOCALE_DIR = Path(__file__).parent / "locales"

_active: dict[str, str] = {}
_fallback: dict[str, str] = {}


def available_languages() -> list[str]:
    """Returns the codes of all installed language files, sorted."""
    return sorted(path.stem for path in LOCALE_DIR.glob("*.json"))


def load_language(code: str) -> dict[str, str]:
    """Reads the strings of one language file."""
    return json.loads((LOCALE_DIR / f"{code}.json").read_text(encoding="utf-8"))


def set_language(code: str) -> None:
    """Activates a language. Unknown codes fall back to English."""
    global _active, _fallback
    _fallback = load_language(DEFAULT_LANGUAGE)
    _active = load_language(code) if code in available_languages() else _fallback


def t(key: str, **values: object) -> str:
    """Returns the text for a key, with the given values filled in."""
    text = _active.get(key) or _fallback.get(key) or key
    return text.format(**values) if values else text


def windows_ui_locale() -> str | None:
    """
    Returns the Windows display language as a locale tag such as "de-CH", or None.

    None is returned on other systems and when the lookup fails.
    """
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return None
    name = locale.windows_locale.get(lang_id)
    return name.replace("_", "-") if name else None


def match_language(locale_tag: str | None, supported: list[str] | None = None) -> str:
    """
    Returns the supported language for a locale tag such as "de-CH" or "de_AT".

    An exact match wins, then the base language, so "de-AT" gives "de". Anything else,
    including a missing tag, gives English.

    Args:
        locale_tag: The locale tag, or None
        supported: The language codes to match against; defaults to the installed languages
    """
    languages = available_languages() if supported is None else supported
    if locale_tag:
        by_name = {code.lower(): code for code in languages}
        name = locale_tag.replace("_", "-").lower()
        if name in by_name:
            return by_name[name]
        base = name.split("-")[0]
        if base in by_name:
            return by_name[base]
    return DEFAULT_LANGUAGE


def detect_system_language() -> str:
    """Returns the supported language that matches the Windows display language, or English."""
    return match_language(windows_ui_locale())


set_language(DEFAULT_LANGUAGE)
