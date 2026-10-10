"""User settings, saved as JSON in the user's application data folder."""

import json
import os
from pathlib import Path

from pdf_fusion.i18n import available_languages, detect_system_language


def settings_path() -> Path:
    """Returns the settings file, PDF Fusion\\settings.json under %APPDATA% on Windows."""
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "PDF Fusion" / "settings.json"


def load_settings() -> dict:
    """Reads the settings. A missing or broken file gives empty settings."""
    try:
        data = json.loads(settings_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_settings(data: dict) -> None:
    """Writes the settings file, creating its folder if needed."""
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_language() -> str:
    """
    Returns the language to use.

    A saved language wins if it is supported. Otherwise the Windows display language is used,
    and English when that is not supported either.
    """
    saved = load_settings().get("language")
    if saved in available_languages():
        return saved
    return detect_system_language()
