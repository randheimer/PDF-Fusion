"""Tests for the translation files and the settings file."""

import re

from pdf_fusion import settings
from pdf_fusion.i18n import available_languages, load_language, set_language, t

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def test_known_languages_are_installed():
    assert {"en", "de", "de-CH"} <= set(available_languages())


def test_every_language_has_the_same_keys_as_english():
    english = set(load_language("en"))
    for code in available_languages():
        assert set(load_language(code)) == english, code


def test_placeholders_match_english_in_every_language():
    english = load_language("en")
    for code in available_languages():
        strings = load_language(code)
        for key, text in english.items():
            assert set(PLACEHOLDER.findall(strings[key])) == set(PLACEHOLDER.findall(text)), (code, key)


def test_t_uses_the_active_language_and_fills_values():
    set_language("de")
    assert t("status.ready", count=3) == "Bereit  |  3 Datei(en)"
    set_language("en")
    assert t("status.ready", count=3) == "Ready  |  3 file(s)"


def test_unknown_language_falls_back_to_english():
    set_language("xx")
    assert t("dialog.error") == "Error"


def test_unknown_key_returns_the_key_itself():
    assert t("no.such.key") == "no.such.key"


def test_settings_default_to_english_when_missing(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    assert settings.get_language() == "en"


def test_saved_language_is_used(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings.save_settings({"language": "de"})
    assert settings.get_language() == "de"


def test_unknown_saved_language_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings.save_settings({"language": "xx"})
    assert settings.get_language() == "en"


def test_broken_settings_file_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    path = settings.settings_path()
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    assert settings.get_language() == "en"
