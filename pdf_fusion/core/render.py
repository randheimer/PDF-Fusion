"""Renders PDF pages as images with PyMuPDF. No GUI code in here."""

import logging

from PIL import Image

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf  # PyMuPDF before 1.24.3 only provides this module name
    except ImportError:
        pymupdf = None

HAS_PYMUPDF = pymupdf is not None

logger = logging.getLogger(__name__)


def render_pdf_page(path: str, scale: float = 1.0) -> Image.Image | None:
    """
    Renders the first page of a PDF as an RGB image.

    Args:
        path: Path of the PDF file
        scale: Zoom factor, 1.0 is 72 DPI

    Returns:
        The rendered page, or None if PyMuPDF is missing or the file cannot be rendered
    """
    if not HAS_PYMUPDF:
        return None
    try:
        with pymupdf.open(path) as doc:
            pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(scale, scale))
            return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    except Exception:
        logger.exception("Could not render PDF: %s", path)
        return None
