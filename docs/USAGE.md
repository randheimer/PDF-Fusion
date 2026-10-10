# Usage

## Buttons and shortcuts

The labels below are the English ones. The app shows them in the language it uses.

| Button | Shortcut | Action |
|--------|----------|--------|
| ➕ Add files | Ctrl+O | Add PDF and image files |
| 📋 Paste from clipboard | Ctrl+V | Add an image from the clipboard |
| 🗑️ Clear all | Delete | Remove all files (asks for confirmation) |
| 💾 Save as PDF | Ctrl+S | Export everything as one PDF |

## Steps

1. **Add files:** click "Add files", or drag files into the window.
2. **Change the order:** drag thumbnails up or down. The export follows the order shown.
3. **Preview:** click a thumbnail. A PDF shows its first page, an image is shown in full. Previews are scaled to fit, up to 800 px.
4. **Remove a file:** click the red ✕ on its thumbnail.
5. **Paste an image:** copy an image, then click "Paste from clipboard".
6. **Export:** click "Save as PDF" and choose the output file. Every page of every PDF is kept, and each image becomes one page.

Images with transparency are placed on a white background.

## Supported formats

| Format | Input | Output | Preview |
|--------|-------|--------|---------|
| PDF | ✅ | ✅ all pages | ✅ with PyMuPDF |
| JPG / JPEG | ✅ | ✅ one page per image | ✅ |
| PNG | ✅ | ✅ one page per image | ✅ |

The output is always one PDF. Images are saved as pages at 100 DPI.

## Language

The interface uses the Windows display language if it is supported, and English otherwise. To choose a language yourself, set `language` in `settings.json` in `%APPDATA%\PDF Fusion\`:

```json
{"language": "de"}
```

Available: `en` (English, also the fallback), `de`, `de-CH`.

## Defaults

- Window: 1200×700 px, minimum 800×500 px
- Thumbnails: 80×80 px
- Maximum preview size: 800 px
