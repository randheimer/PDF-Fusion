"""Tests for the translation files, language detection and the settings file."""

import re

from pdf_fusion import settings
from pdf_fusion.i18n import available_languages, load_language, match_language, set_language, t

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


def test_exact_locale_match_is_used():
    assert match_language("de-CH") == "de-CH"
    assert match_language("de_ch") == "de-CH"


def test_base_language_is_used_for_other_regions():
    assert match_language("de-AT") == "de"


def test_unsupported_locale_falls_back_to_english():
    assert match_language("ja-JP") == "en"
    assert match_language("zh-TW") == "en"


def test_missing_locale_falls_back_to_english():
    assert match_language(None) == "en"


def test_windows_language_is_used_when_nothing_is_saved(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(settings, "detect_system_language", lambda: "de-CH")
    assert settings.get_language() == "de-CH"


def test_saved_language_beats_the_windows_language(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(settings, "detect_system_language", lambda: "de-CH")
    settings.save_settings({"language": "de"})
    assert settings.get_language() == "de"


def test_unknown_saved_language_uses_the_windows_language(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(settings, "detect_system_language", lambda: "de")
    settings.save_settings({"language": "xx"})
    assert settings.get_language() == "de"


def test_unsupported_windows_language_gives_english(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(settings, "detect_system_language", lambda: "en")
    assert settings.get_language() == "en"


def test_broken_settings_file_uses_the_windows_language(monkeypatch, tmp_path):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setattr(settings, "detect_system_language", lambda: "en")
    path = settings.settings_path()
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    assert settings.get_language() == "en"
