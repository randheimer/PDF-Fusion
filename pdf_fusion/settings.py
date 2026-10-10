"""User settings, saved as JSON in the user's application data folder."""

import json
import os
from pathlib import Path

from pdf_fusion.i18n import DEFAULT_LANGUAGE, available_languages


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
    """Returns the saved language code, or English if none is saved or it is unknown."""
    code = load_settings().get("language", DEFAULT_LANGUAGE)
    return code if code in available_languages() else DEFAULT_LANGUAGE
