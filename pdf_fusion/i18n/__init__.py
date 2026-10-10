"""Translations for the user interface.

The texts live in JSON files in ``locales/``, one file per language code.
``t(key)`` returns the text for the active language and falls back to English.
"""

import json
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


set_language(DEFAULT_LANGUAGE)
