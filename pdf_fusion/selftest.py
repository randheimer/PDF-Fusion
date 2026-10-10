"""Smoke test for built executables. It checks the bundled parts without opening a window."""

import os
import tempfile

import customtkinter  # noqa: F401  imported to check that the UI library is bundled
from PIL import Image
from pypdf import PdfReader

from pdf_fusion.core.merge import merge_to_pdf
from pdf_fusion.core.render import HAS_PYMUPDF, render_pdf_page
from pdf_fusion.i18n import available_languages


def run_smoke_test() -> int:
    """
    Merges a generated image into a PDF and renders the result, and checks the language files.

    Returns:
        0 when every check passes, 1 otherwise
    """
    if not available_languages() or not HAS_PYMUPDF:
        return 1
    with tempfile.TemporaryDirectory() as folder:
        picture = os.path.join(folder, "page.png")
        output = os.path.join(folder, "out.pdf")
        Image.new("RGB", (100, 100), "white").save(picture)
        merge_to_pdf([picture], output)
        pages = len(PdfReader(output).pages)
        rendered = render_pdf_page(output, scale=1.0)
    return 0 if pages == 1 and rendered is not None else 1
