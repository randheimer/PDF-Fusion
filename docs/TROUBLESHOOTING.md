# Troubleshooting

## PDF thumbnails show a placeholder, and clicking a PDF only shows its page count

PyMuPDF is missing or older than 1.24.3. Install a current version:

```bash
pip install --upgrade PyMuPDF
```

## Drag & drop does not work

Install `tkinterdnd2`:

```bash
pip install tkinterdnd2
```

## An encrypted PDF cannot be exported

PDFs that use AES encryption need the `crypto` extra of pypdf:

```bash
pip install "pypdf[crypto]"
```

PDFs that require a password to open cannot be merged, because the app does not ask for one.

## Images do not look right in the PDF

RGBA, LA and palette (P) images are converted to RGB on a white background. Check the source image if the result looks wrong.
