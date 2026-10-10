# Development

## Project layout

```
PDF-Fusion/
├── main.py                # Entry point
├── pdf_fusion/core/       # Merge and render logic, no GUI code
├── pdf_fusion/ui/         # CustomTkinter user interface, theme and thumbnails
├── pdf_fusion/i18n/       # Translations: one JSON file per language
├── pdf_fusion/selftest.py # Smoke test used by the release build
├── packaging/             # PyInstaller spec for the portable exe
├── tests/                 # pytest tests
├── docs/                  # Documentation and screenshots
└── CHANGELOG.md           # Release notes
```

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

CI runs the same tests on Windows with Python 3.10 to 3.12.

## Translations

User-visible text lives in `pdf_fusion/i18n/locales/en.json` and is read with `t("key")`. Add the same key to every other locale file. The tests fail when a key or a placeholder is missing.

## Build the portable exe

```bash
pip install -r requirements.txt pyinstaller
pyinstaller packaging/pdf-fusion.spec --noconfirm
dist\PDF-Fusion.exe --smoke-test
```

The smoke test merges a generated page, renders it and checks the language files. It exits with 0 on success.

## Release

The Release workflow builds and smoke-tests the exe on every run. Pushing a tag such as `v0.1.0` also creates a GitHub release. The tag must match `pdf_fusion/__init__.py`, and `CHANGELOG.md` needs a section `## [0.1.0]`, which becomes the release notes.
